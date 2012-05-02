import cProfile
import marshal
import os
import subprocess
import sys
import tempfile

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.test.client import Client

__all__ = ['AlastorMiddleware']

class SimulatedRequest(object):
    def __init__(self, request):
        self._method = request.method
        self._headers = dict([(k, v) for (k, v) in request.META.iteritems()
                              if k.startswith('HTTP_')])
        self._data = dict((k, request.POST[k]) for k in request.POST)

        path = request.path
        query = request.GET.copy()
        query.pop('__alastor__', None)
        query = query.urlencode()
        if query:
            path += '?' + query
        self._path = path

    def profile(self, options=''):
        client = Client()
        callback = {'GET': client.get,
                    'POST': client.post,
                    'HEAD': client.head,
                    'OPTIONS': client.options,
                    'PUT': client.put,
                    'DELETE': client.delete}[self._method]

        profiler = cProfile.Profile()
        profiler.runcall(callback, self._path, self._data, **self._headers)
        profiler.create_stats()

        # XXX
        gprof2dot = os.path.join(os.path.dirname(__file__), '_gprof2dot.py')

        with tempfile.NamedTemporaryFile() as stats:
            stats.write(marshal.dumps(profiler.stats))
            stats.flush()
            proc = subprocess.Popen('%s %s %s -f pstats %s | dot -Tpdf' # XXX
                                    % (sys.executable, gprof2dot, options,
                                       stats.name),
                                    shell=True, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE)
            output = proc.communicate()[0]
            if proc.poll():
                raise Exception # XXX
        return output

if getattr(settings, 'ALASTOR_CELERY', False):
    from celery.task import task
    @task
    def profiletask(srequest, options):
        with tempfile.NamedTemporaryFile(prefix='alastor-', suffix='.pdf',
                                         delete=False) as outfile:
            outfile.write(srequest.profile(options))
            return outfile.name
else:
    profiletask = None

class AlastorMiddleware(object):
    _refresh = """<!DOCTYPE html>
<head>
<title>Profiling...</title>
<meta http-equiv=refresh content=3>
</head>
<body>
<p>Profiling...</p>
"""

    def _allowed(self, request):
        if settings.DEBUG:
            return True
        user = getattr(request, 'user', None)
        if user is not None:
            return user.is_superuser
        else:
            return False

    def _profile(self, task_id, request):
        if task_id == '':
            options = getattr(settings, 'ALASTOR_GPROF2DOT_OPTIONS', '')
            srequest = SimulatedRequest(request)
            result = profiletask.delay(srequest, options)

            query = request.GET.copy()
            query['__alastor__'] = result.task_id
            return redirect(request.path + '?' + query.urlencode())
        else:
            result = profiletask.AsyncResult(task_id)
            if not result.ready():
                return HttpResponse(self._refresh)
            else:
                with open(result.get(), 'rb') as outfile:
                    output = outfile.read()
                return HttpResponse(output, content_type='application/pdf')

    def _profilenow(self, request):
        options = getattr(settings, 'ALASTOR_GPROF2DOT_OPTIONS', '')
        srequest = SimulatedRequest(request)
        return HttpResponse(srequest.profile(options),
                            content_type='application/pdf')

    def process_view(self, request, *args, **kwargs):
        if not self._allowed(request):
            return

        task_id = request.GET.get('__alastor__', None)
        if task_id is None:
            return

        if profiletask:
            return self._profile(task_id, request)
        else:
            return self._profilenow(request)
