"""
PC-BASIC - compat.posix
Interface for Unix-like system calls

(c) 2018 Rob Hagemans
This file is released under the GNU GPL version 3 or later.
"""

import os
import sys
import locale
import logging
import subprocess
import fcntl
import termios
import array
import struct
import select

# set locale - this is necessary for curses and *maybe* for clipboard handling
# there's only one locale setting so best to do it all upfront here
# NOTE that this affects str.upper() etc.
# don't do this on Windows as it makes the console codepage different from the stdout encoding ?
try:
    locale.setlocale(locale.LC_ALL, '')
except locale.Error as e:
    # mis-configured locale can throw an error here, no need to crash
    logging.error(e)

from .base import PY2, HOME_DIR, MACOS

if PY2:
    from .python2 import which
else:
    from shutil import which


# text conventions
# ctrl+D
EOF = u'\x04'
# LF end-of-line
EOL = u'\n'

# shell conventions
# console encoding
SHELL_ENCODING = sys.stdin.encoding or locale.getpreferredencoding()
FS_ENCODING = sys.getfilesystemencoding()
# window suppression not needed on Unix
HIDE_WINDOW = None


# output buffer for ioctl call
_sock_size = array.array('i', [0])


##############################################################################
# various

def set_dpi_aware():
    """Enable HiDPI awareness."""

##############################################################################
# file system

def get_free_bytes(path):
    """Return the number of free bytes on the drive."""
    # note that from Python 3.3 onwards, we can use the cross-platform shutil.disk_usage
    st = os.statvfs(path)
    return st.f_bavail * st.f_frsize

def get_short_pathname(native_path):
    """Return Windows short path name or None if not available."""
    return None

if PY2:
    # the official parameter should be LC_CTYPE but that's None in my locale
    # on Windows, this would only work if the mbcs CP_ACP includes the characters we need;
    argv = [_arg.decode(FS_ENCODING, errors='replace') for _arg in sys.argv]

def is_hidden(path):
    """File is hidden."""
    # dot files are hidden on unixy systems
    base = os.path.basename(path)
    return base.startswith(u'.') and (base not in (u'.', u'..'))


##############################################################################
# printing

if which('paps'):
    def line_print(printbuf, printer):
        """Print the buffer to a LPR printer using PAPS."""
        options = b''
        if printer and printer != u'default':
            options = b'-P "%s"' % (printer.encode(SHELL_ENCODING, 'replace'),)
        if printbuf:
            # A4 paper is 595 points wide by 842 points high.
            # Letter paper is 612 by 792 points.
            # the below seems to allow 82 chars horizontally on A4; it appears
            # my PAPS version doesn't quite use cpi correctly as 10cpi should
            # allow 80 chars on A4 with a narrow margin but only does so with a
            # margin of 0.
            pr = subprocess.Popen(
                b'paps --cpi=11 --lpi=6 --left-margin=20 --right-margin=20 '
                b'--top-margin=6 --bottom-margin=6 '
                b'| lpr %s' % (options,), shell=True, stdin=subprocess.PIPE)
            # PAPS does not recognise CRLF
            printbuf = printbuf.replace(b'\r\n', b'\n')
            pr.stdin.write(printbuf)
            pr.stdin.close()

else:
    def line_print(printbuf, printer):
        """Print the buffer to a LPR (CUPS or older UNIX) printer."""
        options = b''
        if printer and printer != u'default':
            options = b'-P "%s"' % (printer.encode(SHELL_ENCODING, 'replace'),)
        if printbuf:
            # cups defaults to 10 cpi, 6 lpi.
            pr = subprocess.Popen(b'lpr %s' % (options,), shell=True, stdin=subprocess.PIPE)
            pr.stdin.write(printbuf)
            pr.stdin.close()
