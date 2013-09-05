"""A Django middleware for interactive profiling"""

import cProfile
import marshal
import socket
import subprocess
import tempfile

from django.conf import settings
from django.http import HttpResponse
from django.test.client import Client, MULTIPART_CONTENT

__all__ = ['VisorMiddleware']

class HolodeckException(Exception):
    """Captain, the holodeck's malfunctioning again!"""

class HoloRequest(object):
    """A simulated, test client request that Celery can pickle.

    This tries to copy everything off of a real request object in order to
    replay it with the Django test client.
    """

    def __init__(self, request):
        """Initialize a HoloRequest.

        request should be a Django request object.
        """
        self._method = request.method
        self._headers = dict([(k, v) for (k, v) in request.META.iteritems()
                              if k.startswith('HTTP_')])

        ctype = request.META.get('HTTP_CONTENT_TYPE',
                                 request.META.get('CONTENT_TYPE',
                                                  MULTIPART_CONTENT))
        if (ctype == 'application/x-www-form-urlencoded' or
            ctype.startswith('multipart/')):
            self._data = dict((k, request.POST[k]) for k in request.POST)
            self._data_type = MULTIPART_CONTENT
        else:
            self._data = request.raw_post_data
            self._data_type = ctype

        path = request.path
        query = request.GET.copy()
        query.pop('__geordi__', None)
        query = query.urlencode()
        if query:
            path += '?' + query
        self._path = path

    def profile(self, options=''):
        """Profile the request and return a PDF of the call graph"""
        client = Client()
        callback = {'GET': client.get,
                    'POST': client.post,
                    'HEAD': client.head,
                    'OPTIONS': client.options,
                    'PUT': client.put,
                    'DELETE': client.delete}[self._method]

        profiler = cProfile.Profile()
        profiler.runcall(callback, self._path, self._data, self._data_type,
                         **self._headers)
        profiler.create_stats()

        outputdir = getattr(settings, 'GEORDI_OUTPUT_DIR', None)
        with tempfile.NamedTemporaryFile(prefix='geordi-', suffix='.pstats',
                                         dir=outputdir, delete=False) as stats:
            stats.write(marshal.dumps(profiler.stats))
            statsfn = stats.name

        # XXX: Formatting a shell string like this isn't ideal.
        cmd = ('gprof2dot.py %s -f pstats %s | dot -Tpdf'
                % (options, statsfn))
        proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE)
        output = proc.communicate()[0]
        retcode = proc.poll()
        if retcode:
            raise HolodeckException('gprof2dot/dot exited with %d'
                                    % retcode)
        return statsfn, output

class VisorMiddleware(object):
    """Interactive profiling middleware.

    When a request comes in that has a __geordi__ GET parameter, this bypasses
    the view function, profiles the request, and returns the profiler output.

    Note that this only runs if settings.DEBUG is True or if the current user
    is a super user.
    """

    def _allowed(self, request):
        """Return whether or not the middleware should run"""
        if settings.DEBUG:
            return True
        user = getattr(request, 'user', None)
        if user is not None:
            return user.is_superuser
        else:
            return False

    def _profile(self, request):
        """Profile the request in-process"""
        options = getattr(settings, 'GEORDI_GPROF2DOT_OPTIONS', '')
        srequest = HoloRequest(request)
        statsfn, output = srequest.profile(options)
        response = HttpResponse(output,
                                content_type='application/pdf')
        response['X-Geordi-Served-By'] = socket.gethostname()
        response['X-Geordi-Pstats-Filename'] = statsfn
        return response

    def process_view(self, request, *args, **kwargs):
        """Handle view bypassing/profiling"""
        if '__geordi__' in request.GET and self._allowed(request):
            return self._profile(request)
