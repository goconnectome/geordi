import inspect
import sys
from collections import namedtuple

Call = namedtuple('Call', 'module lineno name callees')

class Profiler(object):
    def __init__(self):
        self.callees = []
        self._callstack = []
        self._framestack = []

    def _tracecall(self, frame, arg):
        curframe = self._framestack[-1]
        if frame.f_back is not curframe:
            assert curframe.f_back is frame.f_back
            self._tracereturn(curframe, arg)
            assert frame.f_back is self._curframe

        fc = frame.f_code
        call = Call(fc.co_filename, fc.co_firstlineno, fc.co_name, [])

        if self._callstack:
            self._callstack[-1].callees.append(call)
            self._callstack.append(call)
        else:
            self.callees.append(call)
            self._callstack.append(call)

        self._framestack.append(frame)

    def _traceccall(self, frame, arg):
        call = Call(arg.__module__, 0, arg.__name__, [])

        if self._callstack:
            self._callstack[-1].callees.append(call)
            self._callstack.append(call)
        else:
            self.callees.append(call)
            self._callstack.append(call)

        self._framestack.append(frame)

    def _tracereturn(self, frame, arg):
        curframe = self._framestack.pop()
        if frame is not curframe:
            assert frame is self._framestack[-1]
            self._tracereturn(curframe, arg)

        if self._callstack:
            self._callstack.pop()

    def _traceexception(self, frame, arg):
        curframe = self._curframe
        if frame is not curframe and self._callstack:
            self._tracereturn(curframe, None)

    _tracers = {'call': _tracecall,
                'c_call': _traceccall,
                'return': _tracereturn,
                'c_return': _tracereturn,
                'exception': _traceexception,
                'c_exception': _traceexception}

    def _trace(self, frame, event, arg):
        self._tracers[event](self, frame, arg)

    def runcall(self, func, *args, **kwargs):
        self._framestack.append(inspect.currentframe())
        sys.setprofile(self._trace)
        try:
            return func(*args, **kwargs)
        finally:
            sys.setprofile(None)
            self.callees.pop()
            self._callstack.pop()
            self._framestack.pop()
