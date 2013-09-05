"""A Django middleware for interactive profiling"""

import cProfile
import marshal
import socket
import subprocess
import tempfile
import urlparse

__all__ = ['HolodeckException', 'VisorMiddleware']

class HolodeckException(Exception):
    """Captain, the holodeck's malfunctioning again!"""

class VisorMiddleware(object):
    """Interactive profiling middleware.

    When a request comes in that has a __geordi__ GET parameter, this bypasses
    the view function, profiles the request, and returns the profiler output.

    Note that this only runs if settings.DEBUG is True or if the current user
    is a super user.
    """
    def __init__(self, app=None, allowedfunc=lambda environ: True):
        self._app = app
        self._allowed = allowedfunc

    def _response(self, profiler):
        profiler.create_stats()

        with tempfile.NamedTemporaryFile(prefix='geordi-', suffix='.pstats',
                                         delete=False) as stats:
            stats.write(marshal.dumps(profiler.stats))
            statsfn = stats.name

        # XXX: Formatting a shell string like this isn't ideal.
        cmd = ('gprof2dot.py -f pstats %s | dot -Tpdf'
                % statsfn)
        proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE)
        output = proc.communicate()[0]
        retcode = proc.poll()
        if retcode:
            raise HolodeckException('gprof2dot/dot exited with %d'
                                    % retcode)

        headers = [('Content-Type', 'application/pdf'),
                   ('X-Geordi-Served-By', socket.gethostname()),
                   ('X-Geordi-Pstats-Filename', statsfn)]
        return headers, output

    def __call__(self, environ, start_response):
        qs = urlparse.parse_qs(environ['QUERY_STRING'],
                               keep_blank_values=True)
        if '__geordi__' not in qs or not self._allowed(environ):
            return self._app(environ, start_response)

        def dummy_start_response(status, response_headers, exc_info=None):
            pass

        profiler = cProfile.Profile()
        profiler.runcall(self._app, environ, dummy_start_response)
        headers, output = self._response(profiler)
        start_response('200 OK', headers)
        return [output]

    def _djangoallowed(self, request):
        """Return whether or not the middleware should run"""
        from django.conf import settings
        if settings.DEBUG:
            return True

        user = getattr(request, 'user', None)
        if user is not None:
            return user.is_superuser
        else:
            return False

    def process_request(self, request):
        if ('__geordi__' not in request.GET or
            not self._djangoallowed(request)):
            return

        request._geordi = cProfile.Profile()
        request._geordi.enable()

    def process_response(self, request, response):
        profiler = getattr(request, '_geordi', None)
        if profiler is None:
            return response

        profiler.disable()
        headers, output = self._response(profiler)

        from django.http import HttpResponse
        profresponse = HttpResponse(output)
        for name, value in headers:
            profresponse[name] = value
        return profresponse
