"""
PC-BASIC - console.py
Console front-end

(c) 2013, 2014, 2015, 2016 Rob Hagemans
This file is released under the GNU GPL version 3 or later.
"""

import string

import state
import events
import error
# for num_fn_keys
import events
import basictoken as tk
from eascii import as_bytes as ea

# alt+key macros for interactive mode
# these happen at a higher level than F-key macros
alt_key_replace = {
    ea.ALT_a: tk.keyword[tk.AUTO],
    ea.ALT_b: tk.keyword[tk.BSAVE],
    ea.ALT_c: tk.keyword[tk.COLOR],
    ea.ALT_d: tk.keyword[tk.DELETE],
    ea.ALT_e: tk.keyword[tk.ELSE],
    ea.ALT_f: tk.keyword[tk.FOR],
    ea.ALT_g: tk.keyword[tk.GOTO],
    ea.ALT_h: tk.keyword[tk.HEX],
    ea.ALT_i: tk.keyword[tk.INPUT],
    ea.ALT_k: tk.keyword[tk.KEY],
    ea.ALT_l: tk.keyword[tk.LOCATE],
    ea.ALT_m: tk.keyword[tk.MOTOR],
    ea.ALT_n: tk.keyword[tk.NEXT],
    ea.ALT_o: tk.keyword[tk.OPEN],
    ea.ALT_p: tk.keyword[tk.PRINT],
    ea.ALT_r: tk.keyword[tk.RUN],
    ea.ALT_s: tk.keyword[tk.SCREEN],
    ea.ALT_t: tk.keyword[tk.THEN],
    ea.ALT_u: tk.keyword[tk.USING],
    ea.ALT_v: tk.keyword[tk.VAL],
    ea.ALT_w: tk.keyword[tk.WIDTH],
    ea.ALT_x: tk.keyword[tk.XOR],
    }

# on the keys line 25, what characters to replace & with which
keys_line_replace_chars = {
        '\x07': '\x0e',    '\x08': '\xfe',    '\x09': '\x1a',    '\x0A': '\x1b',
        '\x0B': '\x7f',    '\x0C': '\x16',    '\x0D': '\x1b',    '\x1C': '\x10',
        '\x1D': '\x11',    '\x1E': '\x18',    '\x1F': '\x19'}


#MOVE to Screen
# viewport parameters
state.console_state.view_start = 1

state.console_state.view_set = False
# writing on bottom row is allowed
state.console_state.bottom_row_allowed = False




class Console(object):
    """ Interactive environment. """

    def __init__(self, screen, keyboard, sound, output_redirection):
        """ Initialise console. """
        # function key legend is visible
        self.keys_visible = False
        # overwrite mode (instead of insert)
        self._overwrite_mode = True
        self.screen = screen
        self.sound = sound
        self.keyboard = keyboard
        self.init_mode()
        self.redirect = output_redirection

    def init_mode(self):
        """ Initialisation when we switched to new screen mode. """
        # only redraw keys if screen has been cleared  (any colours stay the same).
        if self.keys_visible:
            self.show_keys(True)
        # rebuild build the cursor;
        # first move to home in case the screen has shrunk
        self.set_pos(1, 1)
        self.screen.cursor.set_default_shape(self._overwrite_mode)
        self.screen.cursor.reset_visibility()
        # there is only one VIEW PRINT setting across all pages.
        if self.screen.scroll_height == 25:
            # tandy/pcjr special case: VIEW PRINT to 25 is preserved
            self.screen.set_view(1, 25)
        else:
            self.screen.unset_view()

    def set_width(self, to_width):
        """ Change the width of the screen. """
        # raise an error if the width value doesn't make sense
        if to_width not in (20, 40, 80):
            raise error.RunError(error.IFC)
        # if we're currently at that width, do nothing
        if to_width != self.screen.mode.width:
            # change video mode to one with new width
            self.screen.set_width(to_width)
            self.init_mode()

    ###############################
    # interactive mode

    def wait_screenline(self, write_endl=True, from_start=False):
        """ Enter interactive mode and read string from console. """
        # from_start means direct entry mode, otherwise input mode
        prompt_width = 0 if from_start else self.screen.current_col-1
        try:
            # give control to user for interactive mode
            prompt_row, left, right = self.wait_interactive(prompt_width)
        except error.Break:
            # for some reason, 0E character is printed to redirects at break
            self.redirect.write('\x0e')
            raise
        # get contents and of the logical line
        if from_start:
            outstr = self.get_logical_line(self.screen.current_row)
        else:
            outstr = self.get_logical_line_input(self.screen.current_row,
                                            prompt_row, left, right)
        # redirects output exactly the contents of the logical line
        # including any trailing whitespace and chars past 255
        self.redirect.write(outstr)
        # go to last row of logical line
        self.screen.current_row = self.find_end_of_line(self.screen.current_row)
        # echo the CR, if requested
        if write_endl:
            self.redirect.write('\r\n')
            self.set_pos(self.screen.current_row+1, 1)
        # to the parser/INPUT, only the first 255 chars are returned
        # with trailing whitespace removed
        return str(outstr[:255].rstrip(' \t\n'))

    def find_start_of_line(self, srow):
        """ Find the start of the logical line that includes our current position. """
        # move up as long as previous line wraps
        while srow > 1 and self.screen.apage.row[srow-2].wrap:
            srow -= 1
        return srow

    def find_end_of_line(self, srow):
        """ Find the end of the logical line that includes our current position. """
        # move down as long as this line wraps
        while srow <= self.screen.mode.height and self.screen.apage.row[srow-1].wrap:
            srow += 1
        return srow

    def get_logical_line(self, srow):
        """ Get bytearray of the contents of the logical line. """
        # find start of logical line
        srow = self.find_start_of_line(srow)
        line = bytearray()
        # add all rows of the logical line
        for therow in self.screen.apage.row[
                                    srow-1:self.screen.mode.height]:
            line += bytearray(pair[0] for pair in therow.buf[:therow.end])
            # continue so long as the line wraps
            if not therow.wrap:
                break
            # wrap before end of line means LF
            if therow.end < self.screen.mode.width:
                line += '\n'
        return line

    def get_logical_line_input(self, srow, prompt_row, left, right):
        """ Get bytearray of the contents of the logical line, adapted for INPUT. """
        # INPUT: the prompt starts at the beginning of a logical line
        # but the row may have moved up: this happens on line 24
        # in this case we need to move up to the start of the logical line
        prompt_row = self.find_start_of_line(prompt_row)
        # find start of logical line
        srow = self.find_start_of_line(srow)
        line = bytearray()
        # INPUT returns empty string if enter pressed below prompt row
        if srow <= prompt_row:
            # add all rows of the logical line
            for crow in range(srow, self.screen.mode.height+1):
                therow = self.screen.apage.row[crow-1]
                # exclude prompt, if any; only go from furthest_left to furthest_right
                if crow == prompt_row:
                    rowpairs = therow.buf[:therow.end][left-1:right-1]
                else:
                    rowpairs = therow.buf[:therow.end]
                # get characters from char/attr pairs and convert to bytearray
                line += bytearray(pair[0] for pair in rowpairs)
                if not therow.wrap:
                    break
                # wrap before end of line means LF
                if therow.end < self.screen.mode.width:
                    line += '\n'
        return line

    def wait_interactive(self, prompt_width):
        """ Manage the interactive mode. """
        # force cursor visibility in all cases
        self.screen.cursor.show(True)
        try:
            # this is where we started
            start_row = self.screen.current_row
            furthest_left = 1 + prompt_width
            # this is where we arrow-keyed on the start line
            furthest_right = self.screen.current_col
            while True:
                row, col = self.screen.current_row, self.screen.current_col
                if row == start_row:
                    furthest_left = min(col, furthest_left)
                    furthest_right = max(col, furthest_right)
                    if col == self.screen.mode.width and self.screen.overflow:
                        furthest_right += 1
                # wait_char returns one e-ASCII code
                d = self.keyboard.get_char_block()
                # insert dbcs chars from keyboard buffer two bytes at a time
                if (d in self.keyboard.codepage.lead and
                        self.keyboard.buf.peek() in self.keyboard.codepage.trail):
                    d += self.keyboard.buf.getc()
                if not d:
                    # input stream closed
                    raise error.Exit()
                if d in (ea.UP, ea.CTRL_6, ea.DOWN, ea.CTRL_MINUS,  ea.RIGHT, ea.CTRL_BACKSLASH,
                          ea.LEFT, ea.CTRL_RIGHTBRACKET, ea.HOME, ea.CTRL_k, ea.END, ea.CTRL_n):
                    # arrow keys drop us out of insert mode
                    self.set_overwrite_mode(True)
                if d == ea.CTRL_c:
                    # CTRL-C -- only caught here, not in wait_char like <CTRL+BREAK>
                    raise error.Break()
                elif d == b'\r':
                    # ENTER, CTRL+M
                    break
                elif d == b'\a':
                    # BEL, CTRL+G
                    self.sound.beep()
                elif d == b'\b':
                    # BACKSPACE, CTRL+H
                    self.backspace(start_row, furthest_left)
                elif d == b'\t':
                    # TAB, CTRL+I
                    self.tab()
                elif d == b'\n':
                    # CTRL+ENTER, CTRL+J
                    self.line_feed()
                elif d == ea.ESCAPE:
                    # ESC, CTRL+[
                    self.clear_line(row, furthest_left)
                elif d in (ea.CTRL_END, ea.CTRL_e):
                    self.clear_rest_of_line(row, col)
                elif d in (ea.UP, ea.CTRL_6):
                    self.set_pos(row - 1, col, scroll_ok=False)
                elif d in (ea.DOWN, ea.CTRL_MINUS):
                    self.set_pos(row + 1, col, scroll_ok=False)
                elif d in (ea.RIGHT, ea.CTRL_BACKSLASH):
                    # RIGHT, CTRL+\
                    # skip dbcs trail byte
                    if self.screen.apage.row[row-1].double[col-1] == 1:
                        self.set_pos(row, col + 2, scroll_ok=False)
                    else:
                        self.set_pos(row, col + 1, scroll_ok=False)
                elif d in (ea.LEFT, ea.CTRL_RIGHTBRACKET):
                    # LEFT, CTRL+]
                    self.set_pos(row, col - 1, scroll_ok=False)
                elif d in (ea.CTRL_RIGHT, ea.CTRL_f):
                    self.skip_word_right()
                elif d in (ea.CTRL_LEFT, ea.CTRL_b):
                    self.skip_word_left()
                elif d in (ea.INSERT, ea.CTRL_r):
                    self.set_overwrite_mode(not self._overwrite_mode)
                elif d in (ea.DELETE, ea.CTRL_BACKSPACE):
                    self.delete_char(row, col)
                elif d in (ea.HOME, ea.CTRL_k):
                    self.set_pos(1, 1)
                elif d in (ea.END, ea.CTRL_n):
                    self.end()
                elif d in (ea.CTRL_HOME, ea.CTRL_l):
                    self.clear()
                else:
                    try:
                        # these are done on a less deep level than the fn key macros
                        letters = list(alt_key_replace[d]) + [' ']
                    except KeyError:
                        letters = [d]
                    for d in letters:
                        # ignore eascii by this point, but not dbcs
                        if d[0] not in (b'\0', b'\r'):
                            if not self._overwrite_mode:
                                for c in d:
                                    self.insert(row, col, c, self.screen.attr)
                                    # row and col have changed
                                    self.screen.redraw_row(col-1, row)
                                    col += 1
                                self.set_pos(self.screen.current_row,
                                        self.screen.current_col + len(d))
                            else:
                                # put all dbcs in before messing with cursor position
                                for c in d:
                                    self.put_char(c, do_scroll_down=True)
                # move left if we end up on dbcs trail byte
                row, col = self.screen.current_row, self.screen.current_col
                if self.screen.apage.row[row-1].double[col-1] == 2:
                    self.set_pos(row, col-1, scroll_ok=False)
                # adjust cursor width
                row, col = self.screen.current_row, self.screen.current_col
                if self.screen.apage.row[row-1].double[col-1] == 1:
                    self.screen.cursor.set_width(2)
                else:
                    self.screen.cursor.set_width(1)
        finally:
            self.set_overwrite_mode(True)
            # reset cursor visibility
            self.screen.cursor.reset_visibility()
        return start_row, furthest_left, furthest_right

    def set_overwrite_mode(self, new_overwrite=True):
        """ Set or unset the overwrite mode (INS). """
        if new_overwrite != self._overwrite_mode:
            self._overwrite_mode = new_overwrite
            self.screen.cursor.set_default_shape(new_overwrite)

    def insert(self, crow, ccol, c, cattr):
        """ Insert a single byte at the current position. """
        while True:
            therow = self.screen.apage.row[crow-1]
            therow.buf.insert(ccol-1, (c, cattr))
            if therow.end < self.screen.mode.width:
                therow.buf.pop()
                if therow.end > ccol-1:
                    therow.end += 1
                else:
                    therow.end = ccol
                break
            else:
                if crow == self.screen.scroll_height:
                    self.screen.scroll()
                    # this is not the global row which is changed by scroll()
                    crow -= 1
                if not therow.wrap and crow < self.screen.mode.height:
                    self.screen.scroll_down(crow+1)
                    therow.wrap = True
                c, cattr = therow.buf.pop()
                crow += 1
                ccol = 1

    def delete_char(self, crow, ccol):
        """ Delete the character (single/double width) at the current position. """
        double = self.screen.apage.row[crow-1].double[ccol-1]
        if double == 0:
            # we're on an sbcs byte.
            self.delete_sbcs_char(crow, ccol)
        elif double == 1:
            # we're on a lead byte, delete this and the next.
            self.delete_sbcs_char(crow, ccol)
            self.delete_sbcs_char(crow, ccol)
        elif double == 2:
            # we're on a trail byte, delete the previous and this.
            self.delete_sbcs_char(crow, ccol-1)
            self.delete_sbcs_char(crow, ccol-1)

    def delete_sbcs_char(self, crow, ccol):
        """ Delete a single-byte character at the current position. """
        save_col = ccol
        thepage = self.screen.apage
        therow = thepage.row[crow-1]
        width = self.screen.mode.width
        if crow > 1 and ccol >= therow.end and therow.wrap:
            # row was an LF-ending row & we're deleting past the LF
            nextrow = thepage.row[crow]
            # replace everything after the delete location with
            # stuff from the next row
            therow.buf[ccol-1:] = nextrow.buf[:width-ccol+1]
            therow.end = min(max(therow.end, ccol) + nextrow.end, width)
            # and continue on the following rows as long as we wrap.
            while crow < self.screen.scroll_height and nextrow.wrap:
                nextrow2 = thepage.row[crow+1]
                nextrow.buf = (nextrow.buf[width-ccol+1:] +
                               nextrow2.buf[:width-ccol+1])
                nextrow.end = min(nextrow.end + nextrow2.end, width)
                crow += 1
                therow, nextrow = thepage.row[crow-1], thepage.row[crow]
            # replenish last row with empty space
            nextrow.buf = (nextrow.buf[width-ccol+1:] +
                           [(' ', self.screen.attr)] * (width-ccol+1))
            # adjust the row end
            nextrow.end -= width - ccol
            # redraw the full logical line from the original position onwards
            self.screen.redraw_row(save_col-1, self.screen.current_row)
            # if last row was empty, scroll up.
            if nextrow.end <= 0:
                nextrow.end = 0
                ccol += 1
                therow.wrap = False
                self.screen.scroll(crow+1)
        elif ccol <= therow.end:
            # row not ending with LF
            while True:
                if (therow.end < width or crow == self.screen.scroll_height
                        or not therow.wrap):
                    # no knock on to next row, just delete the char
                    del therow.buf[ccol-1]
                    # and replenish the buffer at the end of the line
                    therow.buf.insert(therow.end-1, (' ', self.screen.attr))
                    break
                else:
                    # wrap and end[row-1]==width
                    nextrow = thepage.row[crow]
                    # delete the char and replenish from next row
                    del therow.buf[ccol-1]
                    therow.buf.insert(therow.end-1, nextrow.buf[0])
                    # then move on to the next row and delete the first char
                    crow += 1
                    therow, nextrow = thepage.row[crow-1], thepage.row[crow]
                    ccol = 1
            # redraw the full logical line
            # this works from *global* row onwards
            self.screen.redraw_row(save_col-1, self.screen.current_row)
            # change the row end
            # this works on *local* row (last row edited)
            if therow.end > 0:
                therow.end -= 1
            else:
                # if there was nothing on the line, scroll the next line up.
                self.screen.scroll(crow)
                if crow > 1:
                    thepage.row[crow-2].wrap = False

    def clear_line(self, the_row, from_col=1):
        """ Clear whole logical line (ESC), leaving prompt. """
        self.clear_rest_of_line(self.find_start_of_line(the_row), from_col)

    def clear_rest_of_line(self, srow, scol):
        """ Clear from given position to end of logical line (CTRL+END). """
        mode = self.screen.mode
        therow = self.screen.apage.row[srow-1]
        therow.buf = (therow.buf[:scol-1] +
            [(' ', self.screen.attr)] * (mode.width-scol+1))
        therow.double = (therow.double[:scol-1] + [0] * (mode.width-scol+1))
        therow.end = min(therow.end, scol-1)
        crow = srow
        while self.screen.apage.row[crow-1].wrap:
            crow += 1
            self.screen.apage.row[crow-1].clear(self.screen.attr)
        for r in range(crow, srow, -1):
            self.screen.apage.row[r-1].wrap = False
            self.screen.scroll(r)
        therow = self.screen.apage.row[srow-1]
        therow.wrap = False
        self.set_pos(srow, scol)
        save_end = therow.end
        therow.end = mode.width
        if scol > 1:
            self.screen.redraw_row(scol-1, srow)
        else:
            # inelegant: we're clearing the text buffer for a second time now
            self.screen.clear_rows(srow, srow)
        therow.end = save_end

    def backspace(self, start_row, start_col):
        """ Delete the char to the left (BACKSPACE). """
        crow, ccol = self.screen.current_row, self.screen.current_col
        # don't backspace through prompt
        if ccol == 1:
            if crow > 1 and self.screen.apage.row[crow-2].wrap:
                ccol = self.screen.mode.width
                crow -= 1
        elif ccol != start_col or self.screen.current_row != start_row:
            ccol -= 1
        self.set_pos(crow, max(1, ccol))
        if self.screen.apage.row[self.screen.current_row-1].double[self.screen.current_col-1] == 2:
            # we're on a trail byte, move to the lead
            self.set_pos(self.screen.current_row, self.screen.current_col-1)
        self.delete_char(crow, ccol)

    def tab(self):
        """ Jump to next 8-position tab stop (TAB). """
        row, col = self.screen.current_row, self.screen.current_col
        newcol = 9 + 8 * int((col-1) / 8)
        if self._overwrite_mode:
            self.set_pos(row, newcol, scroll_ok=False)
        else:
            for _ in range(8):
                self.insert(row, col, ' ', self.screen.attr)
            self.screen.redraw_row(col - 1, row)
            self.set_pos(row, newcol)

    def end(self):
        """ Jump to end of logical line; follow wraps (END). """
        crow = self.screen.current_row
        while (self.screen.apage.row[crow-1].wrap and
                crow < self.screen.mode.height):
            crow += 1
        if self.screen.apage.row[crow-1].end == self.screen.mode.width:
            self.set_pos(crow, self.screen.apage.row[crow-1].end)
            self.screen.overflow = True
        else:
            self.set_pos(crow, self.screen.apage.row[crow-1].end+1)

    def line_feed(self):
        """ Move the remainder of the line to the next row and wrap (LF). """
        crow, ccol = self.screen.current_row, self.screen.current_col
        if ccol < self.screen.apage.row[crow-1].end:
            for _ in range(self.screen.mode.width - ccol + 1):
                self.insert(crow, ccol, ' ', self.screen.attr)
            self.screen.redraw_row(ccol - 1, crow)
            self.screen.apage.row[crow-1].end = ccol - 1
        else:
            while (self.screen.apage.row[crow-1].wrap and
                    crow < self.screen.scroll_height):
                crow += 1
            if crow >= self.screen.scroll_height:
                self.screen.scroll()
            # self.screen.current_row has changed, don't use crow
            if self.screen.current_row < self.screen.mode.height:
                self.screen.scroll_down(self.screen.current_row+1)
        # LF connects lines like word wrap
        self.screen.apage.row[self.screen.current_row-1].wrap = True
        self.set_pos(self.screen.current_row+1, 1)

    def skip_word_right(self):
        """ Skip one word to the right (CTRL+RIGHT). """
        crow, ccol = self.screen.current_row, self.screen.current_col
        # find non-alphanumeric chars
        while True:
            c = self.screen.apage.row[crow-1].buf[ccol-1][0]
            if (c not in string.digits + string.ascii_letters):
                break
            ccol += 1
            if ccol > self.screen.mode.width:
                if crow >= self.screen.scroll_height:
                    # nothing found
                    return
                crow += 1
                ccol = 1
        # find alphanumeric chars
        while True:
            c = self.screen.apage.row[crow-1].buf[ccol-1][0]
            if (c in string.digits + string.ascii_letters):
                break
            ccol += 1
            if ccol > self.screen.mode.width:
                if crow >= self.screen.scroll_height:
                    # nothing found
                    return
                crow += 1
                ccol = 1
        self.set_pos(crow, ccol)

    def skip_word_left(self):
        """ Skip one word to the left (CTRL+LEFT). """
        crow, ccol = self.screen.current_row, self.screen.current_col
        # find alphanumeric chars
        while True:
            ccol -= 1
            if ccol < 1:
                if crow <= state.console_state.view_start:
                    # not found
                    return
                crow -= 1
                ccol = self.screen.mode.width
            c = self.screen.apage.row[crow-1].buf[ccol-1][0]
            if (c in string.digits + string.ascii_letters):
                break
        # find non-alphanumeric chars
        while True:
            last_row, last_col = crow, ccol
            ccol -= 1
            if ccol < 1:
                if crow <= state.console_state.view_start:
                    break
                crow -= 1
                ccol = self.screen.mode.width
            c = self.screen.apage.row[crow-1].buf[ccol-1][0]
            if (c not in string.digits + string.ascii_letters):
                break
        self.set_pos(last_row, last_col)

    def clear(self):
        """ Clear the screen. """
        save_view_set = state.console_state.view_set
        save_view_start = state.console_state.view_start
        save_scroll_height = self.screen.scroll_height
        self.screen.set_view(1, 25)
        self.screen.clear_view()
        if save_view_set:
            self.screen.set_view(save_view_start, save_scroll_height)
        else:
            self.screen.unset_view()
        if self.keys_visible:
            self.show_keys(True)

    ##### output methods

    def write(self, s, scroll_ok=True, do_echo=True):
        """ Write a string to the screen at the current position. """
        if do_echo:
            # CR -> CRLF, CRLF -> CRLF LF
            self.redirect.write(''.join([ ('\r\n' if c == '\r' else c) for c in s ]))
        last = ''
        # if our line wrapped at the end before, it doesn't anymore
        self.screen.apage.row[self.screen.current_row-1].wrap = False
        for c in s:
            row, col = self.screen.current_row, self.screen.current_col
            if c == '\t':
                # TAB
                num = (8 - (col - 1 - 8 * int((col-1) / 8)))
                for _ in range(num):
                    self.put_char(' ')
            elif c == '\n':
                # LF
                # exclude CR/LF
                if last != '\r':
                    # LF connects lines like word wrap
                    self.screen.apage.row[row-1].wrap = True
                    self.set_pos(row + 1, 1, scroll_ok)
            elif c == '\r':
                # CR
                self.screen.apage.row[row-1].wrap = False
                self.set_pos(row + 1, 1, scroll_ok)
            elif c == '\a':
                # BEL
                self.sound.beep()
            elif c == '\x0B':
                # HOME
                self.set_pos(1, 1, scroll_ok)
            elif c == '\x0C':
                # CLS
                self.clear()
            elif c == '\x1C':
                # RIGHT
                self.set_pos(row, col + 1, scroll_ok)
            elif c == '\x1D':
                # LEFT
                self.set_pos(row, col - 1, scroll_ok)
            elif c == '\x1E':
                # UP
                self.set_pos(row - 1, col, scroll_ok)
            elif c == '\x1F':
                # DOWN
                self.set_pos(row + 1, col, scroll_ok)
            else:
                # includes \b, \0, and non-control chars
                self.put_char(c)
            last = c

    def write_line(self, s='', scroll_ok=True, do_echo=True):
        """ Write a string to the screen and end with a newline. """
        self.write(s, scroll_ok, do_echo)
        if do_echo:
            self.redirect.write('\r\n')
        self.check_pos(scroll_ok=True)
        self.screen.apage.row[self.screen.current_row-1].wrap = False
        self.set_pos(self.screen.current_row + 1, 1)

    def list_line(self, line, newline=True):
        """ Print a line from a program listing or EDIT prompt. """
        # no wrap if 80-column line, clear row before printing.
        # flow of listing is visible on screen
        state.session.check_events()
        # replace LF CR with LF
        line = line.replace('\n\r', '\n')
        cuts = line.split('\n')
        for i, l in enumerate(cuts):
            # clear_line looks back along wraps, use clear_rest_of_line instead
            self.clear_rest_of_line(self.screen.current_row, 1)
            self.write(str(l))
            if i != len(cuts)-1:
                self.write('\n')
        if newline:
            self.write_line()
        # remove wrap after 80-column program line
        if len(line) == self.screen.mode.width and self.screen.current_row > 2:
            self.screen.apage.row[self.screen.current_row-3].wrap = False

    #####################
    # key replacement

    def list_keys(self):
        """ Print a list of the function key macros. """
        for i in range(state.session.parser.events.num_fn_keys):
            text = bytearray(self.keyboard.buf.key_replace[i])
            for j in range(len(text)):
                try:
                    text[j] = keys_line_replace_chars[chr(text[j])]
                except KeyError:
                    pass
            self.write_line('F' + str(i+1) + ' ' + str(text))

    def clear_key_row(self):
        """ Clear row 25 on the active page. """
        key_row = self.screen.mode.height
        self.screen.clear_rows(key_row, key_row)

    def show_keys(self, do_show):
        """ Show/hide the function keys line on the active page. """
        # Keys will only be visible on the active page at which KEY ON was given,
        # and only deleted on page at which KEY OFF given.
        if not do_show:
            self.keys_visible = False
            self.clear_key_row()
        else:
            self.keys_visible = True
            self.clear_key_row()
            for i in range(self.screen.mode.width/8):
                text = str(self.keyboard.buf.key_replace[i][:6])
                kcol = 1+8*i
                self.write_for_keys(str(i+1)[-1], kcol, self.screen.attr)
                if not self.screen.mode.is_text_mode:
                    self.write_for_keys(text, kcol+1, self.screen.attr)
                else:
                    if (self.screen.attr>>4) & 0x7 == 0:
                        self.write_for_keys(text, kcol+1, 0x70)
                    else:
                        self.write_for_keys(text, kcol+1, 0x07)
            self.screen.apage.row[24].end = self.screen.mode.width

    def write_for_keys(self, s, col, cattr):
        """ Write chars on the keys line; no echo, some character replacements. """
        for c in s:
            if c == '\0':
                # NUL character terminates display of a word
                break
            else:
                try:
                    c = keys_line_replace_chars[c]
                except KeyError:
                    pass
                self.screen.put_char_attr(self.screen.apagenum, 25, col, c, cattr, for_keys=True)
            col += 1

    #####################
    # screen read/write

    def put_char(self, c, do_scroll_down=False):
        """ Put one byte at the current position. """
        # check if scroll& repositioning needed
        if self.screen.overflow:
            self.screen.current_col += 1
            self.screen.overflow = False
        # see if we need to wrap and scroll down
        self.check_wrap(do_scroll_down)
        # move cursor and see if we need to scroll up
        self.check_pos(scroll_ok=True)
        # put the character
        self.screen.put_char_attr(self.screen.apagenum,
                self.screen.current_row, self.screen.current_col,
                c, self.screen.attr)
        # adjust end of line marker
        if (self.screen.current_col >
                self.screen.apage.row[self.screen.current_row-1].end):
             self.screen.apage.row[self.screen.current_row-1].end = self.screen.current_col
        # move cursor. if on col 80, only move cursor to the next row
        # when the char is printed
        if self.screen.current_col < self.screen.mode.width:
            self.screen.current_col += 1
        else:
            self.screen.overflow = True
        # move cursor and see if we need to scroll up
        self.check_pos(scroll_ok=True)

    def check_wrap(self, do_scroll_down):
        """ Wrap if we need to. """
        if self.screen.current_col > self.screen.mode.width:
            if self.screen.current_row < self.screen.mode.height:
                # wrap line
                self.screen.apage.row[self.screen.current_row-1].wrap = True
                if do_scroll_down:
                    # scroll down (make space by shifting the next rows down)
                    if self.screen.current_row < self.screen.scroll_height:
                        self.screen.scroll_down(self.screen.current_row+1)
                # move cursor and reset cursor attribute
                self.screen.move_cursor(self.screen.current_row + 1, 1)
            else:
                self.screen.current_col = self.screen.mode.width

    def set_pos(self, to_row, to_col, scroll_ok=True):
        """ Set the current position. """
        self.screen.overflow = False
        self.screen.current_row, self.screen.current_col = to_row, to_col
        # this may alter self.screen.current_row, self.screen.current_col
        self.check_pos(scroll_ok)
        # move cursor and reset cursor attribute
        self.screen.move_cursor(self.screen.current_row, self.screen.current_col)

    def check_pos(self, scroll_ok=True):
        """ Check if we have crossed the screen boundaries and move as needed. """
        oldrow, oldcol = self.screen.current_row, self.screen.current_col
        if state.console_state.bottom_row_allowed:
            if self.screen.current_row == self.screen.mode.height:
                self.screen.current_col = min(self.screen.mode.width, self.screen.current_col)
                if self.screen.current_col < 1:
                    self.screen.current_col += 1
                self.screen.move_cursor(self.screen.current_row, self.screen.current_col)
                return self.screen.current_col == oldcol
            else:
                # if row > height, we also end up here
                # (eg if we do INPUT on the bottom row)
                # adjust viewport if necessary
                state.console_state.bottom_row_allowed = False
        # see if we need to move to the next row
        if self.screen.current_col > self.screen.mode.width:
            if self.screen.current_row < self.screen.scroll_height or scroll_ok:
                # either we don't nee to scroll, or we're allowed to
                self.screen.current_col -= self.screen.mode.width
                self.screen.current_row += 1
            else:
                # we can't scroll, so we just stop at the right border
                self.screen.current_col = self.screen.mode.width
        # see if we eed to move a row up
        elif self.screen.current_col < 1:
            if self.screen.current_row > state.console_state.view_start:
                self.screen.current_col += self.screen.mode.width
                self.screen.current_row -= 1
            else:
                self.screen.current_col = 1
        # see if we need to scroll
        if self.screen.current_row > self.screen.scroll_height:
            if scroll_ok:
                self.screen.scroll()
            self.screen.current_row = self.screen.scroll_height
        elif self.screen.current_row < state.console_state.view_start:
            self.screen.current_row = state.console_state.view_start
        self.screen.move_cursor(self.screen.current_row, self.screen.current_col)
        # signal position change
        return (self.screen.current_row == oldrow and
                 self.screen.current_col == oldcol)

    def start_line(self):
        """ Move the cursor to the start of the next line, this line if empty. """
        if self.screen.current_col != 1:
            self.redirect.write('\r\n')
            self.check_pos(scroll_ok=True)
            self.set_pos(self.screen.current_row + 1, 1)
        # ensure line above doesn't wrap
        self.screen.apage.row[self.screen.current_row-2].wrap = False

    def write_error_message(self, msg, linenum):
        """ Write an error message to the console. """
        self.start_line()
        self.write(msg)
        if linenum is not None and linenum > -1 and linenum < 65535:
            self.write(' in %i' % linenum)
        self.write_line(' ')
