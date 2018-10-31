"""
PC-BASIC - compat.base
Cross-platform compatibility utilities

(c) 2018 Rob Hagemans
This file is released under the GNU GPL version 3 or later.
"""

import os
import re
import contextlib
import sys
import platform


# platform constants
WIN32 = sys.platform == 'win32'
MACOS = sys.platform == 'darwin'

# 64-bit (needed for Windows binary modules)
X64 = platform.architecture()[0] == '64bit'

# platform tag for libraries
if WIN32:
    PLATFORM = sys.platform + ('_x64' if X64 else '_x86')
else:
    PLATFORM = sys.platform

# user configuration and state directories
HOME_DIR = os.path.expanduser(u'~')

if WIN32:
    USER_CONFIG_HOME = os.getenv(u'APPDATA')
    USER_DATA_HOME = USER_CONFIG_HOME
elif MACOS:
    USER_CONFIG_HOME = os.path.join(HOME_DIR, u'Library', u'Application Support')
    USER_DATA_HOME = USER_CONFIG_HOME
else:
    USER_CONFIG_HOME = os.environ.get(u'XDG_CONFIG_HOME') or os.path.join(HOME_DIR, u'.config')
    USER_DATA_HOME = os.environ.get(u'XDG_DATA_HOME') or os.path.join(HOME_DIR, u'.local', u'share')

# package/executable directory
if hasattr(sys, 'frozen'):
    # we're a package: get the directory of the packaged executable
    # (__file__ is undefined in frozen packages)
    # this is for cx_Freeze's package layout
    BASE_DIR = os.path.join(os.path.dirname(sys.executable), 'lib', 'pcbasic')
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))


# utility function, this has to go somewhere...
def split_quoted(line, split_by=u'\s', quote=u'"', strip_quotes=False):
    """Split by separators, preserving quoted blocks."""
    chunks = re.findall(u'[^%s%s][^%s]*|%s.+?%s' % (quote, split_by, split_by, quote, quote), line)
    if strip_quotes:
        chunks = [c.strip(quote) for c in chunks]
    return chunks
