"""A Django middleware for interactive profiling"""

import cProfile
import marshal
import socket
import subprocess
import tempfile

from django.conf import settings
from django.http import HttpResponse

__all__ = ['VisorMiddleware']

class HolodeckException(Exception):
    """Captain, the holodeck's malfunctioning again!"""

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

    def process_request(self, request):
        if '__geordi__' in request.GET and self._allowed(request):
            request._geordi = cProfile.Profile()
            request._geordi.enable()

    def process_response(self, request, response):
        profiler = getattr(request, '_geordi', None)
        if profiler is None:
            return response

        profiler.disable()
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

        profresponse = HttpResponse(output,
                                    content_type='application/pdf')
        profresponse['X-Geordi-Served-By'] = socket.gethostname()
        profresponse['X-Geordi-Pstats-Filename'] = statsfn
        return profresponse
