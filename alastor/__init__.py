import cProfile
import marshal
import subprocess
import tempfile

from django.conf import settings
from django.http import HttpResponse
from django.test.client import Client

def profile(method, path, data, headers, gprof2dot='gprof2dot'):
    client = Client()
    callback = {'GET': client.get, 'POST': client.post, 'HEAD': client.head,
                'OPTIONS': client.options, 'PUT': client.put,
                'DELETE': client.delete}[method]

    profiler = cProfile.Profile()
    profiler.runcall(callback, path, data, **headers)
    profiler.create_stats()

    with tempfile.NamedTemporaryFile() as stats:
        stats.write(marshal.dumps(profiler.stats))
        stats.flush()
        proc = subprocess.Popen('%s -f pstats %s | dot -Tpdf' # XXX
                                % (gprof2dot, stats.name),
                                shell=True, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE)
        output = proc.communicate()[0]
        if proc.poll():
            raise Exception # XXX

    return output

def distill(request):
    headers = dict([(k, v) for (k, v) in request.META.iteritems()
                    if k.startswith('HTTP_')])

    path = request.path
    query = request.GET.copy()
    query.pop('__alastor__', None)
    query = query.urlencode()
    if query:
        path += '?' + query

    data = dict((k, request.POST[k]) for k in request.POST)

    return request.method, path, data, headers

if getattr(settings, 'ALASTOR_CELERY', False):
    from celery.task import task
    profiletask = task(profile)
else:
    profiletask = None

class AlastorMiddleware(object):
    def process_view(self, request, *args, **kwargs):
        if ('__alastor__' in request.GET and
            (request.user.is_superuser or settings.DEBUG)):
            gprof2dot = getattr(settings, 'ALASTOR_GPROF2DOT', 'gprof2dot')
            method, path, data, headers = distill(request)

            if getattr(settings, 'ALASTOR_CELERY', False):
                result = profiletask.delay(method, path, data, headers,
                                           gprof2dot)
                output = result.get() # XXX
            else:
                output = profile(method, path, data, headers, gprof2dot)
            return HttpResponse(output, content_type='application/pdf')
