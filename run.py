#
# PC-BASIC 3.23 - run.py
# Main loops for pc-basic 
# 
# (c) 2013, 3014 Rob Hagemans 
#
# This file is released under the GNU GPL version 3. 
# please see text file COPYING for licence terms.
#

import sys
from cStringIO import StringIO
#import cProfile

import error
import util
import tokenise 
import program
import statements 
import fileio
import automode
import console

def loop():
    # main loop    
    while True:
        # prompt for commands
        prompt()
        # input loop, checks events
        line = get_line()
        # run it 
        execute(line)
               
def prompt(force=False):
    if program.prompt or force:
        console.start_line()
        console.write("Ok\xff\r\n")
    else:
        program.prompt = True
                          
def get_line():
    if automode.auto_mode:
        return automode.auto_input_loop()
    try:
        # input loop, checks events
        line = console.read_screenline(from_start=True) 
    except error.Break:
        line = ''
    if not line:
        program.prompt = False
    # store the direct line
    return line
            
def execute(line):
    if not line:
        return
    try:
        # store the direct line
        get_command_line(line)
    except error.Error as e:
        e.handle() 
    # check for empty lines or lines that start with a line number & deal with them
    if parse_start_direct(program.direct_line):
        # execution loop, checks events
        # execute program or direct command             
        #cProfile.run('run.execution_loop()')
        execution_loop()

def get_command_line(line):
    program.direct_line.truncate(0)
    sline = StringIO(line)
    tokenise.tokenise_stream(sline, program.direct_line, onfile=False)
    program.direct_line.seek(0)
               
# execute any commands
def execution_loop():
    console.show_cursor(False)
    while True:
        try:
            console.check_events()
            if not statements.parse_statement():
                break
        except error.Error as e:
            if not e.handle():
                break
    console.show_cursor()
                   
def parse_start_direct(linebuf): 
    # ignore anything beyond 255
    pos = linebuf.tell()
    linebuf.truncate(255)              
    # restore position; this should not be necessary, but is.
    linebuf.seek(pos)
    if util.peek(linebuf) == '\x00':
        # line starts with a number, add to program memory, no prompt
        try:
            if program.protected:
                # don't list protected files
                raise error.RunError(5)
            program.store_line(linebuf, automode.auto_mode)
            program.prompt = False
        except error.RunError as e:
            e.handle() 
        linebuf.seek(0)
        return False
    # check for empty line, no prompt
    if util.skip_white(linebuf) in util.end_line:
        linebuf.seek(0)
        program.prompt = False
        return False
    # it is a command, go and execute    
    return True        

def exit():
    fileio.close_all()
    sys.exit(0)
    
