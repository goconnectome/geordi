import os
import sys
from collections import namedtuple
from time import time

class Call(object):
    __slots__ = ['module', 'lineno', 'name', 'start', 'stop', 'callees']

    def __init__(self, module, lineno, name, start, stop=None, callees=None):
        self.module = module
        self.lineno = lineno
        self.name = name
        self.start = start
        self.stop = None
        if callees is not None:
            self.callees = callees
        else:
            self.callees = []

    def __repr__(self):
        return 'Call(%r, %r, %r, %r, %r, %r)' % (self.module, self.lineno,
                                                 self.name, self.start,
                                                 self.stop, self.callees)

CallFrame = namedtuple('CallFrame', 'call frame')

class Profiler(object):
    def __init__(self):
        self._callees = []
        self._callstack = []

    def _tracecall(self, frame, arg, Call=Call, CallFrame=CallFrame,
                   time=time):
        if self._callstack:
            prevframe = self._callstack[-1].frame
            if frame.f_back is not prevframe:
                assert frame.f_back is prevframe.f_back
                self._tracereturn(prevframe, None)

        fc = frame.f_code
        call = Call(fc.co_filename, fc.co_firstlineno, fc.co_name, time())
        self._callstack.append(CallFrame(call, frame))

    def _traceccall(self, frame, arg, Call=Call, CallFrame=CallFrame,
                    time=time):
        if self._callstack:
            assert frame is self._callstack[-1].frame

        call = Call(arg.__module__, 0, arg.__name__, time())
        self._callstack.append(CallFrame(call, frame))

    def _tracereturn(self, frame, arg, time=time):
        if not self._callstack:
            return

        prevframe = self._callstack[-1].frame
        if frame is not prevframe:
            assert frame is prevframe.f_back
            self._tracereturn(prevframe, None)

        callframe = self._callstack.pop()
        callframe.call.stop = time()
        if self._callstack:
            self._callstack[-1].call.callees.append(callframe.call)
        else:
            self._callees.append(callframe.call)

    def _traceexception(self, frame, arg):
        if not self._callstack:
            return

        prevframe = self._callstack[-1].frame
        if frame is not prevframe:
            self._tracereturn(prevframe, None)

    _tracers = {'call': _tracecall,
                'c_call': _traceccall,
                'return': _tracereturn,
                'c_return': _tracereturn,
                'exception': _traceexception,
                'c_exception': _traceexception}

    def _trace(self, frame, event, arg):
        self._tracers[event](self, frame, arg)

    def enable(self):
        sys.setprofile(self._trace)

    def disable(self):
        sys.setprofile(None)

    def runcall(self, func, *args, **kwargs):
        self.enable()
        try:
            return func(*args, **kwargs)
        finally:
            self.disable()

    def stats(self):
        paths = [os.path.abspath(p) for p in sys.path]
        def simplify(call):
            if call.module is not None:
                for path in paths:
                    if call.module.startswith(path):
                        call.module = call.module[len(path):]
                        call.module = call.module.lstrip(os.path.sep)
                        break

                if os.path.sep not in call.module:
                    if call.module.endswith('.py'):
                        call.module = call.module[:-len('.py')]
                        call.module = call.module.replace('/', '.')

                    if call.module.endswith('.__init__'):
                        call.module = call.module[:-len('.__init__')]

            time = call.stop - call.start
            return {'module': call.module, 'lineno': call.lineno,
                    'name': call.name, 'time': time,
                    'callees': [simplify(c) for c in call.callees]}

        return [simplify(call) for call in self._callees]
