"""A Django middleware for interactive profiling"""

import optparse
import os
import pprint
import socket
import sys
import webbrowser
from wsgiref.simple_server import make_server

try:
    from urllib.parse import parse_qs
except ImportError:
    from urlparse import parse_qs

from geordi._profiler import Profiler

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
    def __init__(self, app=None, allowedfunc=None):
        self._app = app
        if allowedfunc is not None:
            self._allowed = allowedfunc

    def _response(self, profiler):
        headers = [('Content-Type', 'text/plain'),
                   ('X-Geordi-Served-By', socket.gethostname())]
        output = pprint.pformat(profiler.callees)
        return headers, output

    def _allowed(self, environ):
        qs = parse_qs(environ['QUERY_STRING'], keep_blank_values=True)
        return '__geordi__' in qs

    def __call__(self, environ, start_response):
        if not self._allowed(environ):
            return self._app(environ, start_response)

        def dummy_start_response(status, response_headers, exc_info=None):
            pass

        profiler = Profiler()
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

        request._geordi = Profiler()
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

def main(args):
    p = optparse.OptionParser(usage='geordi SCRIPT...', prog='geordi')
    opts, args = p.parse_args(args)
    if not args:
        sys.stdout.write(p.get_usage())
        return 2

    script = args[0]
    sys.argv[:] = args
    sys.path.insert(0, os.path.dirname(script))

    with open(script, 'rb') as f:
        code = compile(f.read(), script, 'exec')
    globs = {'__file__': script,
             '__name__': '__main__',
             '__package__': None}
    def app(environ, start_response):
        eval(code, globs)

    app = VisorMiddleware(app, allowedfunc=lambda environ: True)
    server = make_server('localhost', 41000, app)
    webbrowser.open('http://localhost:41000')
    server.handle_request()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
