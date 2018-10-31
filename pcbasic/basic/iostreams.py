"""
PC-BASIC - iostreams.py
Input/output streams

(c) 2014--2018 Rob Hagemans
This file is released under the GNU GPL version 3 or later.
"""

import logging
import threading
import sys
import time
import io
from contextlib import contextmanager
from collections import Iterable

from ..compat import WIN32, read_all_available
from .base import signals
from .codepage import CONTROL


# sleep period for input thread
# does not need to be very short as it reads multiple bytes in one cycle
TICK = 0.03


class IOStreams(object):
    """Manage input/output to files, printers and stdio."""

    def __init__(self, queues, codepage, input_streams, output_streams):
        """Initialise I/O streams."""
        self._queues = queues
        self._codepage = codepage
        # input; put in tuple if it's file-like so we do the right thing when looping
        if not input_streams:
            input_streams = ()
        elif hasattr(input_streams, 'read') or not isinstance(input_streams, Iterable):
            input_streams = (input_streams,)
        self._input_streams = [self._wrap_input(stream) for stream in input_streams]
        # output; put in tuple if it's file-like so we do the right thing when looping
        if not output_streams:
            output_streams = ()
        elif hasattr(output_streams, 'write') or not isinstance(output_streams, Iterable):
            output_streams = (output_streams,)
        self._output_echos = [
            self._codepage.wrap_output_stream(stream, preserve=CONTROL)
            for stream in output_streams
        ]
        # disable at start
        self._active = False
        # launch a daemon thread for input
        if self._input_streams:
            # launch a thread to allow nonblocking reads on both Windows and Unix
            thread = threading.Thread(target=self._process_input, args=())
            thread.daemon = True
            thread.start()

    def write(self, s):
        """Write a string/bytearray to all stream outputs."""
        for f in self._output_echos:
            f.write(s)

    def toggle_echo(self, stream):
        """Toggle copying of all screen I/O to stream."""
        if stream in self._output_echos:
            self._output_echos.remove(stream)
        else:
            self._output_echos.append(stream)

    @contextmanager
    def activate(self):
        """Grab and release input stream."""
        self._active = True
        try:
            yield
        finally:
            self._active = False

    def _wrap_input(self, stream):
        """Wrap input stream."""
        return NonBlockingInputWrapper(
            stream, self._codepage, lfcr=not WIN32 and stream.isatty()
        )

    def _process_input(self):
        """Process input from streams."""
        while True:
            time.sleep(TICK)
            if not self._active:
                continue
            queue = self._queues.inputs
            for stream in self._input_streams:
                instr = stream.read()
                if instr is None:
                    break
                elif instr:
                    queue.put(signals.Event(signals.STREAM_CHAR, (instr,)))
            else:
                # executed if not break
                continue
            # input stream is closed, remove it
            self._input_streams.remove(stream)
            # exit the interpreter if last input closed
            if not self._input_streams:
                queue.put(signals.Event(signals.STREAM_CLOSED))
                return


class NonBlockingInputWrapper(object):
    """
    Non-blocking input wrapper, converts CRLF.
    Wraps unicode or bytes stream; always produces unicode.
    """

    def __init__(self, stream, codepage, lfcr):
        """Set up codec."""
        self._stream = stream
        self._lfcr = lfcr
        # codepage, used to read unicode from bytes streams
        self._codepage = codepage

    def read(self):
        """Read all chars available; nonblocking; returns unicode."""
        # we need non-blocking readers
        s = read_all_available(self._stream)
        # can be None (closed) or b'' (no input)
        if s is None:
            return None
        elif not s:
            return u''
        if isinstance(s, bytes):
            # raw input means it's already in the BASIC codepage
            # but the keyboard functions use unicode
            # for input, don't use lead-byte buffering beyond the convert call
            s = self._codepage.str_to_unicode(s, preserve=CONTROL)
        # replace CRLF (and, if desired, LF) with CR
        s = s.replace(u'\r\n', u'\r')
        if self._lfcr:
            s = s.replace(u'\n', u'\r')
        return s
