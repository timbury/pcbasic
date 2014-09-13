#
# PC-BASIC 3.23 - backend_pygame.py
#
# Graphical interface based on PyGame
# 
# (c) 2013, 2014 Rob Hagemans 
#
# This file is released under the GNU GPL version 3. 
# please see text file COPYING for licence terms.
#

try:
    import pygame
except ImportError:
    pygame = None

try:
    import numpy
except ImportError:
    numpy = None

import plat
if plat.system == 'Android':
    android = True
    # don't do sound for now on Android
    mixer = None   
    numpy = None
    # Pygame for Android-specific definitions
    if pygame:
        import pygame_android
else:
    android = False
    import pygame.mixer as mixer

import logging

import config
import unicodepage 
import backend
import typeface
#
import state


# default font family
font_families = ['unifont', 'univga', 'freedos']
fonts = {}

if pygame:
    # composite palettes, see http://nerdlypleasures.blogspot.co.uk/2013_11_01_archive.html
    composite_640 = {
        'cga_old': [
            (0x00, 0x00, 0x00),        (0x00, 0x71, 0x00),        (0x00, 0x3f, 0xff),        (0x00, 0xab, 0xff),
            (0xc3, 0x00, 0x67),        (0x73, 0x73, 0x73),        (0xe6, 0x39, 0xff),        (0x8c, 0xa8, 0xff),
            (0x53, 0x44, 0x00),        (0x00, 0xcd, 0x00),        (0x73, 0x73, 0x73),        (0x00, 0xfc, 0x7e),
            (0xff, 0x39, 0x00),        (0xe2, 0xca, 0x00),        (0xff, 0x7c, 0xf4),        (0xff, 0xff, 0xff)    ],
        'cga': [
            (0x00, 0x00, 0x00),        (0x00, 0x6a, 0x2c),        (0x00, 0x39, 0xff),        (0x00, 0x94, 0xff),        
            (0xca, 0x00, 0x2c),        (0x77, 0x77, 0x77),        (0xff, 0x31, 0xff),        (0xc0, 0x98, 0xff),
            (0x1a, 0x57, 0x00),        (0x00, 0xd6, 0x00),        (0x77, 0x77, 0x77),        (0x00, 0xf4, 0xb8),
            (0xff, 0x57, 0x00),        (0xb0, 0xdd, 0x00),        (0xff, 0x7c, 0xb8),        (0xff, 0xff, 0xff)    ],
        'tandy': [
            (0x00, 0x00, 0x00),        (0x7c, 0x30, 0x00),        (0x00, 0x75, 0x00),        (0x00, 0xbe, 0x00),        
            (0x00, 0x47, 0xee),        (0x77, 0x77, 0x77),        (0x00, 0xbb, 0xc4),        (0x00, 0xfb, 0x3f),        
            (0xb2, 0x0f, 0x9d),        (0xff, 0x1e, 0x0f),        (0x77, 0x77, 0x77),        (0xff, 0xb8, 0x00),        
            (0xb2, 0x44, 0xff),        (0xff, 0x78, 0xff),        (0x4b, 0xba, 0xff),        (0xff, 0xff, 0xff)    ],      
        'pcjr': [
            (0x00, 0x00, 0x00),
            (0x98, 0x20, 0xcb),        (0x9f, 0x1c, 0x00),        (0xff, 0x11, 0x71),        (0x00, 0x76, 0x00),
            (0x77, 0x77, 0x77),        (0x5b, 0xaa, 0x00),        (0xff, 0xa5, 0x00),        (0x00, 0x4e, 0xcb),
            (0x74, 0x53, 0xff),        (0x77, 0x77, 0x77),        (0xff, 0x79, 0xff),        (0x00, 0xc8, 0x71),
            (0x00, 0xcc, 0xff),        (0x00, 0xfa, 0x00),        (0xff, 0xff, 0xff) ]        }
                        
    colorburst = False
    composite_artifacts = False
    composite_monitor = False
    mode_has_artifacts = False
    
    workpalette = [(0, b, f) for b in range(16) for f in range(16)]

    # standard palettes
    gamepalette0 = None
    gamepalette1 = None

    # screen width and height in pixels
    display_size = (640, 480)
    display_size_text = (640, 480)
    
    fullscreen = False
    smooth = False
    # ignore ALT+F4 (and consequently window X button)
    noquit = False

    # letter shapes
    glyphs = []
    font = None
    
    # cursor shape
    cursor0 = None
    # screen & updating 
    screen = None
    surface0 = []
        
    screen_changed = True
    cycle = 0
    blink_state = 0
    last_cycle = 0
    cycle_time = 120 
    blink_cycles = 5

    # current cursor location
    last_row = 1
    last_col = 1    
    
    under_cursor = None
    under_top_left = None

    # available joy sticks
    joysticks = []    

    # store for fast get & put arrays
    get_put_store = {}

    keycode_to_scancode = {
        pygame.K_UP:    '\x00\x48',        pygame.K_DOWN:  '\x00\x50',        pygame.K_RIGHT: '\x00\x4D',        
        pygame.K_LEFT:  '\x00\x4B',        pygame.K_INSERT:'\x00\x52',        pygame.K_DELETE:'\x00\x53',
        pygame.K_HOME:  '\x00\x47',        pygame.K_END:   '\x00\x4F',        pygame.K_PAGEUP:'\x00\x49',
        pygame.K_PAGEDOWN:'\x00\x51',      pygame.K_F1:    '\x00\x3B',        pygame.K_F2:    '\x00\x3C',
        pygame.K_F3:    '\x00\x3D',        pygame.K_F4:    '\x00\x3E',        pygame.K_F5:    '\x00\x3F',
        pygame.K_F6:    '\x00\x40',        pygame.K_F7:    '\x00\x41',        pygame.K_F8:    '\x00\x42',
        pygame.K_F9:    '\x00\x43',        pygame.K_F10:   '\x00\x44',        pygame.K_PRINT: '\x00\x37',    
        # explicitly include BACKSPACE as its unicode is '\x7F' on OSX 
        pygame.K_BACKSPACE: '\x08'
        }
    #K_SYSREQ              sysrq

    ctrl_keycode_to_scancode = {
        pygame.K_RIGHT:     '\x00\x74',        pygame.K_LEFT:      '\x00\x73',        pygame.K_HOME:      '\x00\x77',       
        pygame.K_END:       '\x00\x75',        pygame.K_PAGEUP:    '\x00\x84',        pygame.K_PAGEDOWN:  '\x00\x76',
        pygame.K_BACKSPACE: '\x7F',            pygame.K_RETURN:    '\x0A',            pygame.K_TAB:       '',            
        pygame.K_1:         '',                pygame.K_2:         '\x00\x03',        pygame.K_3:         '',
        pygame.K_4:         '',                pygame.K_5:         '',                # <CTRL+6> is passed normally
        pygame.K_7:         '',                pygame.K_8:         '',                pygame.K_9:         '\x00\x84',       
        pygame.K_0:         '',                pygame.K_F2:        '\x00\x5F',        pygame.K_F3:        '\x00\x60',        
        pygame.K_MINUS:     '\x1F',
    }

    alt_keycode_to_scancode = {
        # unknown: ESC, BACKSPACE, TAB, RETURN
        pygame.K_1:         '\x00\x78',        pygame.K_2:         '\x00\x79',        pygame.K_3:         '\x00\x7A',
        pygame.K_4:         '\x00\x7B',        pygame.K_5:         '\x00\x7C',        pygame.K_6:         '\x00\x7D',
        pygame.K_7:         '\x00\x7E',        pygame.K_8:         '\x00\x7F',        pygame.K_9:         '\x00\x80',
        pygame.K_0:         '\x00\x81',        pygame.K_MINUS:     '\x00\x82',        pygame.K_EQUALS:    '\x00\x83',
        # row 1
        pygame.K_q:         '\x00\x10',        pygame.K_w:         '\x00\x11',        pygame.K_e:         '\x00\x12',
        pygame.K_r:         '\x00\x13',        pygame.K_t:         '\x00\x14',        pygame.K_y:         '\x00\x15',
        pygame.K_u:         '\x00\x16',        pygame.K_i:         '\x00\x17',        pygame.K_o:         '\x00\x18',
        pygame.K_p:         '\x00\x19',        
        # row 2
        pygame.K_a:         '\x00\x1E',        pygame.K_s:         '\x00\x1F',        pygame.K_d:         '\x00\x20',
        pygame.K_f:         '\x00\x21',        pygame.K_g:         '\x00\x22',        pygame.K_h:         '\x00\x23',
        pygame.K_j:         '\x00\x24',        pygame.K_k:         '\x00\x25',        pygame.K_l:         '\x00\x26',
        # row 3        
        pygame.K_z:         '\x00\x2C',        pygame.K_x:         '\x00\x2D',        pygame.K_c:         '\x00\x2E',
        pygame.K_v:         '\x00\x2F',        pygame.K_b:         '\x00\x30',        pygame.K_n:         '\x00\x31',
        pygame.K_m:         '\x00\x32',
        # others    
        pygame.K_F1:        '\x00\x68',        pygame.K_F2:        '\x00\x69',        pygame.K_F3:        '\x00\x6A',
        pygame.K_F4:        '\x00\x6B',        pygame.K_F5:        '\x00\x6C',        pygame.K_F6:        '\x00\x6D',
        pygame.K_F7:        '\x00\x6E',        pygame.K_F8:        '\x00\x6F',        pygame.K_F9:        '\x00\x70',
        pygame.K_F10:       '\x00\x71',
    }
       
    keycode_to_inpcode = {
        # top row
        pygame.K_ESCAPE:    '\x01',        pygame.K_1:         '\x02',        pygame.K_2:         '\x03',
        pygame.K_3:         '\x04',        pygame.K_4:         '\x05',        pygame.K_5:         '\x06',
        pygame.K_6:         '\x07',        pygame.K_7:         '\x08',        pygame.K_8:         '\x09',
        pygame.K_9:         '\x0A',        pygame.K_0:         '\x0B',        pygame.K_MINUS:     '\x0C',
        pygame.K_EQUALS:    '\x0D',        pygame.K_BACKSPACE: '\x0E',
                # row 1
        pygame.K_TAB:       '\x0F',        pygame.K_q:         '\x10',        pygame.K_w:         '\x11',
        pygame.K_e:         '\x12',        pygame.K_r:         '\x13',        pygame.K_t:         '\x14',
        pygame.K_y:         '\x15',        pygame.K_u:         '\x16',        pygame.K_i:         '\x17',
        pygame.K_o:         '\x18',        pygame.K_p:         '\x19',        pygame.K_LEFTBRACKET:'\x1A',
        pygame.K_RIGHTBRACKET:'\x1B',        pygame.K_RETURN:    '\x1C',
        # row 2
        pygame.K_RCTRL:     '\x1D',        pygame.K_LCTRL:     '\x1D',        pygame.K_a:         '\x1E',
        pygame.K_s:         '\x1F',        pygame.K_d:         '\x20',        pygame.K_f:         '\x21',
        pygame.K_g:         '\x22',        pygame.K_h:         '\x23',        pygame.K_j:         '\x24',
        pygame.K_k:         '\x25',        pygame.K_l:         '\x26',        pygame.K_SEMICOLON: '\x27',
        pygame.K_QUOTE:     '\x28',        pygame.K_BACKQUOTE :     '\x29',
        # row 3        
        pygame.K_LSHIFT:    '\x2A',        pygame.K_HASH:      '\x2B',     # assumes UK keyboard?
        pygame.K_z:         '\x2C',        pygame.K_x:         '\x2D',        pygame.K_c:         '\x2E',
        pygame.K_v:         '\x2F',        pygame.K_b:         '\x30',        pygame.K_n:         '\x31',
        pygame.K_m:         '\x32',        pygame.K_COMMA:     '\x33',        pygame.K_PERIOD:    '\x34',
        pygame.K_SLASH:     '\x35',        pygame.K_RSHIFT:    '\x36',        pygame.K_PRINT:     '\x37',
        pygame.K_SYSREQ:    '\x37',        pygame.K_RALT:      '\x38',        pygame.K_LALT:      '\x38',      pygame.K_MODE:      '\x38',
        pygame.K_SPACE:     '\x39',        pygame.K_CAPSLOCK:  '\x3A',
        # others    
        pygame.K_F1:        '\x3B',        pygame.K_F2:        '\x3C',        pygame.K_F3:        '\x3D',
        pygame.K_F4:        '\x3E',        pygame.K_F5:        '\x3F',        pygame.K_F6:        '\x40',
        pygame.K_F7:        '\x41',        pygame.K_F8:        '\x42',        pygame.K_F9:        '\x43',
        pygame.K_F10:       '\x44',        pygame.K_NUMLOCK:   '\x45',        pygame.K_SCROLLOCK: '\x46',
        pygame.K_HOME:      '\x47',        pygame.K_UP:        '\x48',        pygame.K_PAGEUP:    '\x49',
        pygame.K_KP_MINUS:  '\x4A',        pygame.K_LEFT:      '\x4B',        pygame.K_KP5:       '\x4C',
        pygame.K_RIGHT:     '\x4D',        pygame.K_KP_PLUS:   '\x4E',        pygame.K_END:       '\x4F',
        pygame.K_DOWN:      '\x50',        pygame.K_PAGEDOWN:  '\x51',        pygame.K_INSERT:    '\x52',
        pygame.K_DELETE:    '\x53',        pygame.K_BACKSLASH: '\x56',
    }

    keypad_numbers = {
        pygame.K_KP0:   '0',    pygame.K_KP1:   '1',    pygame.K_KP2:   '2',    pygame.K_KP3:   '3',    pygame.K_KP4:   '4',
        pygame.K_KP5:   '5',    pygame.K_KP6:   '6',    pygame.K_KP7:   '7',    pygame.K_KP8:   '8',    pygame.K_KP9:   '9',
    }

    keycode_to_keystatus = {
        pygame.K_INSERT: 0x0080, pygame.K_CAPSLOCK: 0x0040, pygame.K_NUMLOCK: 0x0020, pygame.K_SCROLLOCK: 0x0010,
        pygame.K_LALT: 0x0008, pygame.K_RALT: 0x0008, pygame.K_MODE: 0x0008, # altgr activates K_MODE
        pygame.K_LCTRL: 0x0004, pygame.K_RCTRL: 0x0004, pygame.K_LSHIFT: 0x0002, pygame.K_RSHIFT: 0x0001 }

    
    # cursor is visible
    cursor_visible = True

    # this doesn't currently change
    height = 25
    
####################################            
# set constants based on commandline arguments

def prepare():
    global fullscreen, smooth, noquit, display_size
    global display_size_text, composite_monitor, heights_needed
    global composite_640_palette
    # screen width and height in pixels
    display_size = (640, 480)
    display_size_text = (8*80, 16*25)
    if config.options['video'] in ('cga', 'cga_old', 'tandy', 'pcjr'):
        heights_needed = (8, )
    else:
        heights_needed = (16, 14, 8)
    try:
        x, y = config.options['dimensions'].split(',')
        display_size = (int(x), int(y))
    except (ValueError, TypeError):
        pass    
    try:
        x, y = config.options['dimensions_text'].split(',')
        display_size_text = (int(x), int(y))
    except (ValueError, TypeError):
        pass    
    fullscreen = config.options['fullscreen']
    smooth = config.options['smooth']    
    noquit = config.options['noquit']
    composite_monitor = config.options['composite'] and config.options['video'] != 'ega'
    if composite_monitor:
        composite_640_palette = composite_640[config.options['video']]
    if config.options['video'] == 'tandy':
        # enable tandy F11, F12
        # TODO: tandy scancodes are defined for many more keys than PC, e.g. ctrl+F5 and friends; check pcjr too
        keycode_to_scancode[pygame.K_F11] = '\x00\x98'
        keycode_to_scancode[pygame.K_F12] = '\x00\x99'
        ctrl_keycode_to_scancode[pygame.K_F11] = '\x00\xAC'
        ctrl_keycode_to_scancode[pygame.K_F12] = '\x00\xAD'
        alt_keycode_to_scancode[pygame.K_F11] = '\x00\xB6'
        alt_keycode_to_scancode[pygame.K_F12] = '\x00\xB7'
        keycode_to_inpcode[pygame.K_F11] = '\xF9'
        keycode_to_inpcode[pygame.K_F12] = '\xFA'
    if config.options['font']:
        font_families = config.options['font']

        
####################################
# state saving and loading

class PygameDisplayState(state.DisplayState):
    def pickle(self):
        self.display_strings = ([], [])
        for s in surface0:    
            self.display_strings[0].append(pygame.image.tostring(s, 'P'))
        
    def unpickle(self):
        global display_strings, load_flag
        load_flag = True
        display_strings = self.display_strings
        del self.display_strings


# picklable store for surfaces
display_strings = ([], [])
state.display = PygameDisplayState()
load_flag = False

def load_state():        
    global screen_changed
    if load_flag:
        try:
            for i in range(len(surface0)):    
                surface0[i] = pygame.image.fromstring(display_strings[0][i], size, 'P')
                surface0[i].set_palette(workpalette)
            screen_changed = True    
        except (IndexError, ValueError):
            # couldn't load the state correctly; most likely a text screen saved from -t. just redraw what's unpickled.
            backend.redraw_text_screen()
        
####################################
# initialisation

def init():
    global joysticks, physical_size, scrap, display_size, display_size_text
    global text_mode, num_palette
    # set state objects to whatever is now in state (may have been unpickled)
    if not pygame:
        logging.warning('Could not find PyGame module. Failed to initialise graphical interface.')
        return False     
    pre_init_mixer()   
    pygame.init()
    # exclude some backend drivers as they give unusable results
    if pygame.display.get_driver() == 'caca':
        pygame.display.quit()
        logging.warning('Refusing to open libcaca console. Failed to initialise graphical interface.')
        return False
    # get physical screen dimensions (needs to be called before set_mode)
    display_info = pygame.display.Info()
    physical_size = display_info.current_w, display_info.current_h
    # draw the icon
    pygame.display.set_icon(build_icon())
    # first set the screen non-resizeable, to trick things like maximus into not full-screening
    # I hate it when applications do this ;)
    if not fullscreen:
        pygame.display.set_mode(display_size_text, 0, 8)
    resize_display(*display_size_text, initial=True)
    pygame.display.set_caption('PC-BASIC 3.23')
    pygame.key.set_repeat(500, 24)
    # load a game palette
    num_palette = 64
    update_palette(backend.ega_palette)
    if android:
        pygame_android.init()
    init_mixer()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
    for j in joysticks:
        j.init()
    # if one joystick is present, all are active and report 128 for mid, not 0
    if len(joysticks) > 0:
        for joy in range(0, 1):
            for axis in range(0, 1):
                backend.stick_moved(joy, axis, 128)
    scrap = Clipboard() 
    load_fonts(heights_needed)
    text_mode = True    
    return True

def load_fonts(heights_needed):
    """ Load font typefaces. """
    for height in heights_needed:
        if height in fonts:
            # already force loaded
            continue
        # load a Unifont .hex font and take the codepage subset
        fonts[height] = typeface.load(font_families, height, 
                                      unicodepage.cp_to_utf8)
        # fix missing code points font based on 16-line font
        if 16 in fonts:
            typeface.fixfont(height, fonts[height], 
                             unicodepage.cp_to_utf8, fonts[16])

def supports_graphics_mode(mode_info):
    """ Return whether we support a given graphics mode. """
    # unpack mode info struct
    font_height = mode_info[0]
    if not font_height in fonts:
        return False
    return True

def init_screen_mode(mode_info, is_text_mode=False):
    """ Initialise a given text or graphics mode. """
    global glyphs, cursor0
    global screen, screen_changed, surface0
    global font, under_cursor, size, text_mode
    global font_height, attr, num_colours, num_palette
    global width, num_pages, bitsperpixel, font_width
    global mode_has_artifacts, cursor_fixed_attr
    text_mode = is_text_mode
    # unpack mode info struct
    (font_height, attr, num_colours, num_palette, 
           width, num_pages, bitsperpixel, font_width,
           mode_has_artifacts, cursor_fixed_attr) = mode_info
    font = fonts[font_height]
    glyphs = [ build_glyph(chr(c), font, font_width, font_height) 
                    for c in range(256) ]
    # initialise glyph colour
    set_attr(attr, force_rebuild=True)
    if is_text_mode:
        resize_display(*display_size_text)
    else:
        resize_display(*display_size)
    # logical size    
    height = 25
    size = (width * font_width, height * font_height)    
    screen = pygame.Surface(size, depth=8)
    # set standard cursor
    build_cursor(font_width, font_height, 0, font_height)
    # whole screen (blink on & off)
    surface0 = [ pygame.Surface(size, depth=8) for _ in range(num_pages)]
    for i in range(num_pages):
        surface0[i].set_palette(workpalette)
    screen.set_palette(workpalette)
    screen_changed = True
    
def resize_display(width, height, initial=False): 
    global display, screen_changed
    global fullscreen
    display_info = pygame.display.Info()
    flags = pygame.RESIZABLE
    if fullscreen or (width, height) == physical_size:
        fullscreen = True
        flags |= pygame.FULLSCREEN | pygame.NOFRAME
        if (not initial and not text_mode):
            width, height = display_size 
        else:    
            width, height = display_size_text
        # scale suggested dimensions to largest integer times pixel size that fits
        scale = min( physical_size[0]//width, physical_size[1]//height )
        width, height = width * scale, height * scale
    if (width, height) == (display_info.current_w, display_info.current_h) and not initial:
        return
    display = pygame.display.set_mode((width, height), flags)
    # load display if requested    
    screen_changed = True    
    
# build the Ok icon
def build_icon():
    icon = pygame.Surface((17, 17), depth=8)
    icon.fill(255)
    icon.fill(254, (1, 8, 8, 8))
    # hardcoded O and k from freedos cga font
    okfont = { ord('O'): '\x00\x7C\xC6\xC6\xC6\xC6\xC6\x7C', ord('k'): '\x00\xE0\x60\x66\x6C\x78\x6C\xE6' }
    O = build_glyph(ord('O'), okfont, 8, 8)
    k = build_glyph(ord('k'), okfont, 8, 8)
    icon.blit(O, (1, 0, 8, 8))
    icon.blit(k, (9, 0, 8, 8))
    icon.set_palette_at(255, (0, 0, 0))
    icon.set_palette_at(254, (0xff, 0xff, 0xff))
    pygame.transform.scale2x(icon)
    pygame.transform.scale2x(icon)
    return icon

def close():
    if android:
        pygame_android.close()
    pygame.joystick.quit()
    pygame.display.quit()    

####################################
# console commands

def update_palette(palette):
    global gamepalette, screen_changed, gamepalette0, gamepalette1
    if num_palette == 64:
        gamepalette = [pygame.Color(*backend.colours64[i]) for i in palette]
    else:
        if (colorburst or not composite_monitor):
            # take modulo in case we're e.g. resuming ega text into a cga machine
            gamepalette = [pygame.Color(*backend.colours16[i % num_palette]) for i in palette]
        else:
            gamepalette = [pygame.Color(*backend.colours16_mono[i % num_palette]) for i in palette]
    while len(gamepalette) < 16:
        gamepalette.append(pygame.Color(0, 0, 0))
    gamepalette0 = [gamepalette[f] for b in range(16) for f in range(16)]
    gamepalette1 = [gamepalette[b] for b in range(16) for f in range(16)]
    screen_changed = True

def set_colorburst(on, palette):
    global colorburst, composite_artifacts
    if composite_monitor:
        colorburst = on
    update_palette(palette)
    composite_artifacts = colorburst and mode_has_artifacts and composite_monitor
    
def clear_rows(cattr, start, stop):
    global screen_changed
    bg = (cattr>>4) & 0x7
    scroll_area = pygame.Rect(0, (start-1)*font_height, 
                              size[0], (stop-start+1)*font_height) 
    surface0[apagenum].fill(bg, scroll_area)
    screen_changed = True
    
def set_page(vpage, apage):
    global vpagenum, apagenum, screen_changed
    vpagenum, apagenum = vpage, apage
    screen_changed = True

def copy_page(src,dst):
    global screen_changed
    surface0[dst].blit(surface0[src], (0,0))
    screen_changed = True
    
def update_cursor_visibility(cursor_on):
    global screen_changed, cursor_visible
    cursor_visible = cursor_on
    screen_changed = True

def move_cursor(crow, ccol):
    global cursor_row, cursor_col
    cursor_row, cursor_col = crow, ccol

def update_cursor_attr(attr):
    color = screen.get_palette_at(attr).b
    cursor0.set_palette_at(254, pygame.Color(0, color, color))

def scroll(from_line, scroll_height, attr):
    global screen_changed
    temp_scroll_area = pygame.Rect(
                    0, (from_line-1)*font_height,
                    width * font_width, 
                    (scroll_height-from_line+1) * font_height)
    # scroll
    surface0[apagenum].set_clip(temp_scroll_area)
    surface0[apagenum].scroll(0, -font_height)
    # empty new line
    blank = pygame.Surface( (width * font_width, font_height) , depth=8)
    bg = (attr >> 4) & 0x7
    blank.set_palette(workpalette)
    blank.fill(bg)
    surface0[apagenum].blit(blank, (0, (scroll_height-1) * font_height))
    surface0[apagenum].set_clip(None)
    screen_changed = True
   
def scroll_down(from_line, scroll_height, attr):
    global screen_changed
    temp_scroll_area = pygame.Rect(0, (from_line-1) * font_height, width * 8, 
                                   (scroll_height-from_line+1) * font_height)
    surface0[apagenum].set_clip(temp_scroll_area)
    surface0[apagenum].scroll(0, font_height)
    # empty new line
    blank = pygame.Surface( (width * font_width, font_height), depth=8 )
    bg = (attr>>4) & 0x7
    blank.set_palette(workpalette)
    blank.fill(bg)
    surface0[apagenum].blit(blank, (0, (from_line-1) * font_height))
    surface0[apagenum].set_clip(None)
    screen_changed = True

current_attr = None
current_attr_context = None
def set_attr(cattr, force_rebuild=False):
    global current_attr, current_attr_context
    if (not force_rebuild and cattr == current_attr and apagenum == current_attr_context):
        return  
    if cattr >> 7: # blink      
        color = (0, (cattr>>4) & 0x7, cattr & 0xf)
        bg = (0, (cattr>>4) & 0x7, (cattr>>4) & 0x7)    
    else:
        color = (0, cattr & 0xf, cattr & 0xf)
        bg = (0, (cattr>>4) & 0x7, (cattr>>4) & 0x7)    
    for glyph in glyphs:
        glyph.set_palette_at(255, bg)
        glyph.set_palette_at(254, color)
    current_attr = cattr    
    current_attr_context = apagenum
        
def putc_at(row, col, c, for_keys=False):
    global screen_changed
    glyph = glyphs[ord(c)]
    blank = glyphs[0] # using \0 for blank (tyoeface.py guarantees it's empty)
    top_left = ((col-1) * font_width, (row-1) * font_height)
    surface0[apagenum].blit(glyph, top_left)
    screen_changed = True

def putwc_at(row, col, c, d, for_keys=False):
    global screen_changed
    glyph = build_glyph(c+d, font, 16, font_height)
    color = (0, 0, current_attr & 0xf)
    bg = (0, 0, (current_attr>>4) & 0x7)    
    glyph.set_palette_at(255, bg)
    glyph.set_palette_at(254, color)
    blank = pygame.Surface((16, font_height), depth=8)
    blank.fill(255)
    blank.set_palette_at(255, bg)
    top_left = ((col-1) * font_width, (row-1) * font_height)
    surface0[apagenum].blit(glyph, top_left)
    screen_changed = True
    

carry_col_9 = range(0xc0, 0xdf+1)

def build_glyph(c, font_face, req_width, req_height):
    color, bg = 254, 255
    try:
        face = font_face[c]
    except KeyError:
        logging.debug('Byte sequence %s not represented in codepage, replace with blank glyph.', repr(c))
        # codepoint 0 must be blank by our definitions
        face = font_face['\0']
        c = '\0'
    if len(face) < req_height*req_width//8:
        u = unicodepage.cp_to_utf8[c]
        logging.debug('Incorrect glyph width for %s [%s, code point %x].', repr(c), u, ord(u.decode('utf-8')))
    glyph_width, glyph_height = 8*len(face)//req_height, req_height    
    glyph = pygame.Surface((glyph_width, glyph_height), depth=8)
    glyph.fill(bg)
    for yy in range(glyph_height):
        for half in range(glyph_width//8):    
            line = ord(face[yy*(glyph_width//8)+half])
            for xx in range(8):
                if (line >> (7-xx)) & 1 == 1:
                    glyph.set_at((half*8 + xx, yy), color)
        # VGA 9-bit characters        
        if c in carry_col_9 and glyph_width == 9:
            if line & 1 == 1:
                glyph.set_at((8, yy), color)
    if req_width > glyph_width:
        glyph = pygame.transform.scale(glyph, (req_width, req_height))    
    return glyph        
        
def build_cursor(width, height, from_line, to_line):
    global screen_changed, cursor0, under_cursor
    global cursor_width, cursor_from, cursor_to
    cursor_width, cursor_from, cursor_to = width, from_line, to_line
    under_cursor = pygame.Surface((width, height), depth=8)
    under_cursor.set_palette(workpalette)
    cursor0 = pygame.Surface((width, height), depth=8)
    color, bg = 254, 255
    cursor0.set_colorkey(bg)
    cursor0.fill(bg)
    for yy in range(height):
        for xx in range(width):
            if yy < from_line or yy > to_line:
                pass
            else:
                cursor0.set_at((xx, yy), color)
    screen_changed = True            

######################################
# event loop

def refresh_screen():
    screen.blit(surface0[vpagenum], (0, 0))
    
def remove_cursor():
    if not cursor_visible or vpagenum != apagenum:
        return
    if under_top_left != None:
        screen.blit(under_cursor, under_top_left)

def refresh_cursor():
    global under_top_left, last_row, last_col
    if not  cursor_visible or vpagenum != apagenum:
        return
    # copy screen under cursor
    under_top_left = (  (cursor_col-1) * font_width,
                        (cursor_row-1) * font_height)
    under_char_area = pygame.Rect(
            (cursor_col-1) * font_width, 
            (cursor_row-1) * font_height, 
            (cursor_col-1) * font_width + cursor_width,
            cursor_row * font_height)
    under_cursor.blit(screen, (0,0), area=under_char_area)
    if text_mode:
        # cursor is visible - to be done every cycle between 5 and 10, 15 and 20
        if (cycle/blink_cycles==1 or cycle/blink_cycles==3): 
            screen.blit(cursor0, (  (cursor_col-1) * font_width,
                                    (cursor_row-1) * font_height) )
    else:
        if cursor_fixed_attr != None:
            index = cursor_fixed_attr
        else:
            index = current_attr & 0xf
        if numpy:
            # reference the destination area
            dest_array = pygame.surfarray.pixels2d(screen.subsurface(pygame.Rect(
                                (cursor_col-1) * font_width, 
                                (cursor_row-1) * font_height + cursor_from, 
                                cursor_width, 
                                cursor_to - cursor_from + 1))) 
            dest_array ^= index
        else:
            # no surfarray if no numpy    
            for x in range(     (cursor_col-1) * font_width, 
                                  (cursor_col-1) * font_width + cursor_width):
                for y in range((cursor_row-1) * font_height + cursor_from, 
                                (cursor_row-1) * font_height + cursor_to + 1):
                    pixel = get_pixel(x,y)
                    screen.set_at((x,y), pixel^index)
    last_row = cursor_row
    last_col = cursor_col



def check_screen():
    global cycle, last_cycle
    global screen_changed
    global blink_state
    if text_mode:
        if cycle == 0:
            blink_state = 0
            screen_changed = True
        elif cycle == blink_cycles*2: 
            blink_state = 1
            screen_changed = True
    tock = pygame.time.get_ticks() 
    if (tock - last_cycle) >= (cycle_time/blink_cycles):
        last_cycle = tock
        cycle += 1
        if cycle == blink_cycles*4: 
            cycle = 0
        cursor_changed = ( (text_mode and cycle%blink_cycles == 0) 
                           or (cursor_row != last_row) or (cursor_col != last_col) )
        if screen_changed:
            refresh_screen()
            do_flip()
        elif cursor_changed and cursor_visible:
            remove_cursor()
            do_flip()
        screen_changed = False

def apply_composite_artifacts(screen, pixels=4):
    src_array = pygame.surfarray.array2d(screen)
    width, height = src_array.shape
    s = [None]*pixels
    for p in range(pixels):
        s[p] = src_array[p:width:pixels]&(4//pixels)
    for p in range(1,pixels):
        s[0] = s[0]*2 + s[p]
    return pygame.surfarray.make_surface(numpy.repeat(s[0], pixels, axis=0))
    
def do_flip():
    refresh_cursor()
    if composite_artifacts and numpy:
        workscreen = apply_composite_artifacts(screen, 4//bitsperpixel)
    else:
        workscreen = screen
    if scrap.active():
        scrap.create_feedback(workscreen)
    if composite_artifacts and numpy:
        workscreen.set_palette(composite_640_palette)    
    elif blink_state == 0:
        workscreen.set_palette(gamepalette0)
    elif blink_state == 1:
        workscreen.set_palette(gamepalette1)
    if smooth and not composite_artifacts:
        pygame.transform.smoothscale(workscreen.convert(display), display.get_size(), display)
    pygame.transform.scale(workscreen.convert(display), display.get_size(), display)  
    workscreen.set_palette(workpalette)    
    pygame.display.flip()

#######################################################
# event queue

# buffer for alt+numpad ascii character construction
keypad_ascii = ''

def pause_key():
    # pause key press waits for any key down. continues to process screen events (blink) but not user events.
    while not check_events(pause=True):
        # continue playing background music
        backend.audio.check_sound()
        idle()
        
def idle():
    pygame.time.wait(cycle_time/blink_cycles/8)  

def check_events(pause=False):
    global screen_changed, fullscreen
    # handle Android pause/resume
    if android and pygame_android.check_events():
        # force immediate redraw of screen
        refresh_screen()
        do_flip()
        # force redraw on next tick  
        # we seem to have to redraw twice to see anything
        screen_changed = True
    # check and handle pygame events    
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if not pause:
                handle_key_down(event)
            else:
                return True    
        if event.type == pygame.KEYUP:
            if not pause:
                handle_key_up(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # any mouse button is a pen press
            backend.pen_down(*normalise_pos(*event.pos))
            if event.button == 1:
                # LEFT button: copy
                pos = normalise_pos(*event.pos)
                scrap.start(1+pos[1]//font_height, 1+pos[0]//font_width)
            elif event.button == 2:
                # MIDDLE button: paste
                scrap.paste(mouse=True)    
        elif event.type == pygame.MOUSEBUTTONUP: 
            backend.pen_up()
            if event.button == 1:
                scrap.copy(mouse=True)
                scrap.stop()
        elif event.type == pygame.MOUSEMOTION: 
            pos = normalise_pos(*event.pos) 
            backend.pen_moved(*pos)
            if scrap.active():
                scrap.move(1+pos[1]//font_height, 1+pos[0]//font_width)
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.joy < 2 and event.button < 2:
                backend.stick_down(event.joy, event.button)
        elif event.type == pygame.JOYBUTTONUP:
            if event.joy < 2 and event.button < 2:
                backend.stick_up(event.joy, event.button)
        elif event.type == pygame.JOYAXISMOTION:
            if event.joy < 2 and event.axis < 2:
                backend.stick_moved(event.joy, event.axis, 
                                    int(event.value*127 + 128))
        elif event.type == pygame.VIDEORESIZE:
            fullscreen = False
            resize_display(event.w, event.h)
        elif event.type == pygame.QUIT:
            if noquit:
                pygame.display.set_caption('PC-BASIC 3.23 - to exit type <CTRL+BREAK> <ESC> SYSTEM')
            else:
                backend.insert_special_key('quit')
    check_screen()
    return False

def handle_key_down(e):
    global keypad_ascii
    c = ''
    mods = pygame.key.get_mods()
    if android:
        mods |= pygame_android.apply_mods(e) 
    if e.key in (pygame.K_PAUSE, pygame.K_BREAK):
        if mods & pygame.KMOD_CTRL:
            # ctrl-break
            backend.insert_special_key('break')
        else:
            # pause until keypress
            pause_key()    
    elif e.key == pygame.K_DELETE and mods & pygame.KMOD_CTRL and mods & pygame.KMOD_ALT:
        # if not caught by OS, reset the emulator
        backend.insert_special_key('reset')
    elif e.key == pygame.K_NUMLOCK and mods & pygame.KMOD_CTRL:
        # ctrl+numlock is pause
        pause_key()    
    elif e.key == pygame.K_SCROLLOCK and mods & pygame.KMOD_CTRL:
        # ctrl+SCROLLLOCK breaks too
        backend.insert_special_key('break')
    elif e.key == pygame.K_CAPSLOCK:
        backend.insert_special_key('caps')
    elif e.key == pygame.K_NUMLOCK:
        backend.insert_special_key('num')
    elif e.key == pygame.K_SCROLLOCK:
        backend.insert_special_key('scroll')
    elif e.key == pygame.K_PRINT:
        # these can't be caught by INKEY$ etc:
        if mods & pygame.KMOD_CTRL:
            backend.insert_special_key('c+print')
        elif mods & pygame.KMOD_SHIFT:
            backend.insert_special_key('s+print')
    elif e.key == pygame.K_TAB and mods & pygame.KMOD_SHIFT:
        # shift+tab -> \x00\x0F (scancode for TAB) but TAB -> \x09
        c = '\x00\x0F'
    elif e.key == pygame.K_MENU and android:
        # Android: toggle keyboard on menu key
        pygame_android.toggle_keyboard()
    elif e.key == pygame.K_LSUPER: # logo key, doesn't set a modifier
        scrap.start()
    elif scrap.active():
        scrap.handle_key(e)
    else:
        try:
            if (mods & pygame.KMOD_CTRL):
                c = ctrl_keycode_to_scancode[e.key]
            elif (mods & pygame.KMOD_ALT):
                try:
                    keypad_ascii += keypad_numbers[e.key]
                    return
                except KeyError:    
                    c = alt_keycode_to_scancode[e.key]
            else:
                c = keycode_to_scancode[e.key]
        except KeyError:
            if android:
                u = pygame_android.get_unicode(e, mods)
            else:
                u = e.unicode    
            try:
                c = unicodepage.from_utf8(u.encode('utf-8'))
            except KeyError:
                # fallback to ascii if no encoding found (shouldn't happen); if not ascii, ignore
                if u and ord(u) <= 0x7f:
                    c = chr(ord(u))    
    # double NUL characters as single NUL signals scan code
    if len(c) == 1 and ord(c) == 0:
        c = '\0\0'
    # current key pressed; modifiers ignored 
    try:
        inpcode = ord(keycode_to_inpcode[e.key])
    except KeyError:
        inpcode = None    
    # set key-pressed status
    try:
        keystatuscode = keycode_to_keystatus[e.key]
    except KeyError:
        keystatuscode = None
    ## insert into keyboard queue
    backend.key_down(c, inpcode, keystatuscode) 

def handle_key_up(e):
    global keypad_ascii
    # ALT+keycode    
    if e.key in (pygame.K_RALT, pygame.K_LALT) and keypad_ascii:
        char = chr(int(keypad_ascii)%256)
        if char == '\0':
            char = '\0\0'
        backend.insert_key(char)
        keypad_ascii = ''
    elif e.key == pygame.K_LSUPER: # logo key, doesn't set a modifier
        scrap.stop()
    # last key released gets remembered
    try:
        inpcode = ord(keycode_to_inpcode[e.key])
    except KeyError:
        inpcode = None
    # unset key-pressed status
    try:
        keystatuscode = keycode_to_keystatus[e.key]
    except KeyError:
        keystatuscode = None    

def normalise_pos(x, y):
    """ Convert physical to logical coordinates within screen bounds. """
    display_info = pygame.display.Info()
    xscale, yscale = display_info.current_w / (1.*size[0]), display_info.current_h / (1.*size[1])
    xpos = min(size[0]-1, max(0, int(x//xscale)))
    ypos = min(size[1]-1, max(0, int(y//yscale))) 
    return xpos, ypos
    
###############################################
# clipboard handling

class Clipboard(object):
    """ Clipboard handling """    
    
    # text type we look for in the clipboard
    text = ('UTF8_STRING', 'text/plain;charset=utf-8', 'text/plain',
            'TEXT', 'STRING')
        
    def __init__(self):
        """ Initialise pygame scrapboard. """
        self.logo_pressed = False
        self.select_start = None
        self.select_end = None
        self.selection_rect = None
        try:
            pygame.scrap.init()
            pygame.scrap.set_mode(pygame.SCRAP_CLIPBOARD)
            self.ok = True
        except NotImplementedError:
            logging.warning('PyGame.Scrap module not found. Clipboard functions not available.')    
            self.ok = False

    def available(self):
        if not self.ok:
            return False
        """ True if pasteable text is available on clipboard. """
        types = pygame.scrap.get_types()
        for t in types:
            if t in self.text:
                return True
        return False        

    def active(self):
        if not self.ok:
            return False
        """ True if clipboard mode is active. """
        return self.logo_pressed
        
    def start(self, r=None, c=None):
        if not self.ok:
            return 
        """ Enter clipboard mode (Logo key pressed). """
        self.logo_pressed = True
        if r == None or c == None:
            self.select_start = [cursor_row, cursor_col]
            self.select_stop = [cursor_row, cursor_col]
        else:
            self.select_start = [r, c]
            self.select_stop = [r, c]
        self.selection_rect = [pygame.Rect((self.select_start[1]-1) * font_width,
            (self.select_start[0]-1) * font_height, font_width, font_height)]
        
    def stop(self):
        """ Leave clipboard mode (Logo key released). """
        global screen_changed
        if not self.ok:
            return 
        self.logo_pressed = False
        self.select_start = None
        self.select_stop = None
        self.selection_rect = None
        screen_changed = True

    def copy(self, mouse=False):
        """ Copy screen characters from selection into clipboard. """
        if not self.ok:
            return 
        if mouse:
            pygame.scrap.set_mode(pygame.SCRAP_SELECTION)
        else:
            pygame.scrap.set_mode(pygame.SCRAP_CLIPBOARD)
        start, stop = self.select_start, self.select_stop
        if start[0] > stop[0] or (start[0] == stop[0] and start[1] > stop[1]):
            start, stop = stop, start
        full = backend.get_text(start[0], start[1], stop[0], stop[1])
        try: 
            if plat.system == 'Windows':
                pygame.scrap.put('text/plain;charset=utf-8', full.decode('utf-8').encode('utf-16'))
            else:    
                pygame.scrap.put(pygame.SCRAP_TEXT, full)
        except KeyError:
            logging.debug('Clipboard copy failed for clip %s', repr(full))    
        
    def paste(self, mouse=False):
        """ Paste from clipboard into keyboard buffer. """
        if not self.ok:
            return 
        if mouse:
            pygame.scrap.set_mode(pygame.SCRAP_SELECTION)
        else:
            pygame.scrap.set_mode(pygame.SCRAP_CLIPBOARD)
        us = None
        available = pygame.scrap.get_types()
        for text_type in self.text:
            if text_type not in available:
                continue
            us = pygame.scrap.get(text_type)
            if us:
                break            
        if plat.system == 'Windows':
            if text_type == 'text/plain;charset=utf-8':
                # it's lying, it's giving us UTF16
                us = us.decode('utf-16')
            # null-terminated strings
            us = us[:us.find('\0')] #.decode('ascii', 'ignore')
            us = us.encode('utf-8')
        if not us:
            return
        for u in us.decode('utf-8'):
            c = u.encode('utf-8')
            try:
                backend.insert_key(unicodepage.from_utf8(c))
            except KeyError:
                backend.insert_key(c)
                
    def move(self, r, c):
        """ Move the head of the selection and update feedback. """
        self.select_stop = [r, c]
        if self.select_stop[1] < 1: 
            if self.select_stop[0] > 1:       
                self.select_stop[0] -= 1
                self.select_stop[1] = width
            else:
                self.select_stop[1] = 1       
        if self.select_stop[1] > width:        
            if self.select_stop[0] < height:       
                self.select_stop[0] += 1
                self.select_stop[1] = 1
            else:
                self.select_stop[1] = width    
        start, stop = self.select_start, self.select_stop
        if start[0] > stop[0] or (start[0] == stop[0] and start[1] > stop[1]):
            start, stop = stop, start
        rect_left = (start[1] - 1) * font_width
        rect_top = (start[0] - 1) * font_height
        rect_right = stop[1] * font_width
        rect_bot = stop[0] * font_height
        if start[0] == stop[0]:
            self.selection_rect = [pygame.Rect(rect_left, rect_top, rect_right-rect_left, rect_bot-rect_top)]
        else:
            self.selection_rect = [
              pygame.Rect(rect_left, rect_top, size[0]-rect_left, rect_bot-rect_top-font_height),
              pygame.Rect(0, rect_top+font_height, rect_right, rect_bot-rect_top-font_height)
                ]
        screen_changed = True
    
    
    def handle_key(self, e):
        """ Handle logo+key clipboard commands. """
        global screen_changed
        if not self.ok or not self.logo_pressed:
            return
        if e.unicode in (u'c', u'C'):
            self.copy()
        elif e.unicode in (u'v', u'V') and self.available():
            self.paste()
        elif e.key == pygame.K_LEFT:
            self.move(self.select_stop[0], self.select_stop[1]-1)
        elif e.key == pygame.K_RIGHT:
            self.move(self.select_stop[0], self.select_stop[1]+1)

    def create_feedback(self, surface):
        """ Create visual feedback for selection onto a surface. """
        for r in self.selection_rect:
            work_area = surface.subsurface(r)
            work = work_area.copy()
            work.set_colorkey(pygame.Color(0,0,0)) # use bg color 
            work_area.fill(pygame.Color(0x55, 0, 0x55)) 
            work_area.blit(work, (0,0))
        
###############################################
# graphics backend interface
# low-level methods (pygame implementation)

graph_view = None

def put_pixel(x, y, index, pagenum=None):
    global screen_changed
    if pagenum == None:
        pagenum = apagenum
    surface0[pagenum].set_at((x,y), index)
    backend.clear_screen_buffer_at(x, y)
    screen_changed = True

def get_pixel(x, y, pagenum=None):    
    if pagenum == None:
        pagenum = apagenum
    return surface0[pagenum].get_at((x,y)).b

def get_graph_clip():
    view = graph_view if graph_view else surface0[apagenum].get_rect()
    return view.left, view.top, view.right-1, view.bottom-1

def set_graph_clip(x0, y0, x1, y1):
    global graph_view
    graph_view = pygame.Rect(x0, y0, x1-x0+1, y1-y0+1)    
    
def unset_graph_clip():
    global graph_view
    graph_view = None    
    return surface0[apagenum].get_rect().center

def clear_graph_clip(bg):
    global screen_changed
    surface0[apagenum].set_clip(graph_view)
    surface0[apagenum].fill(bg)
    surface0[apagenum].set_clip(None)
    screen_changed = True

def remove_graph_clip():
    surface0[apagenum].set_clip(None)

def apply_graph_clip():
    surface0[apagenum].set_clip(graph_view)

def fill_rect(x0, y0, x1, y1, index):
    global screen_changed
    rect = pygame.Rect(x0, y0, x1-x0+1, y1-y0+1)
    surface0[apagenum].fill(index, rect)
    backend.clear_screen_buffer_area(x0, y0, x1, y1)
    screen_changed = True

def numpy_set(left, right):
    left[:] = right

def numpy_not(left, right):
    left[:] = right
    left ^= (1<<bitsperpixel) - 1

def numpy_iand(left, right):
    left &= right

def numpy_ior(left, right):
    left |= right

def numpy_ixor(left, right):
    left ^= right
        
fast_operations = {
    '\xC6': numpy_set, #PSET
    '\xC7': numpy_not, #PRESET
    '\xEE': numpy_iand,
    '\xEF': numpy_ior,
    '\xF0': numpy_ixor,
    }

def fast_get(x0, y0, x1, y1, varname, version):
    if not numpy:
        return
    # copy a numpy array of the target area
    clip = pygame.surfarray.array2d(surface0[apagenum].subsurface(pygame.Rect(x0, y0, x1-x0+1, y1-y0+1)))
    get_put_store[varname] = ( x1-x0+1, y1-y0+1, clip, version )

def fast_put(x0, y0, varname, new_version, operation_char):
    global screen_changed
    try:
        width, height, clip, version = get_put_store[varname]
    except KeyError:
        # not yet stored, do it the slow way
        return False
    if x0 < 0 or x0+width-1 > size[0] or y0 < 0 or y0+height-1 > size[1]:
        # let the normal version handle errors
        return False    
    # if the versions are not the same, use the slow method 
    # (array has changed since clip was stored)
    if version != new_version:
        return False
    # reference the destination area
    dest_array = pygame.surfarray.pixels2d(
            surface0[apagenum].subsurface(pygame.Rect(x0, y0, width, height))) 
    # apply the operation
    operation = fast_operations[operation_char]
    operation(dest_array, clip)
    backend.clear_screen_buffer_area(x0, y0, x0+width-1, y0+height-1)
    screen_changed = True
    return True

####################################
# sound interface

from math import ceil

def init_sound():
    return (numpy != None)
    
def stop_all_sound():
    global sound_queue, loop_sound
    for voice in range(4):
        stop_channel(voice)
    loop_sound = [ None, None, None, None ]
    sound_queue = [ [], [], [], [] ]
    
# process sound queue in event loop
def check_sound():
    global loop_sound
    current_chunk = [ None, None, None, None ]
    if sound_queue == [ [], [], [], [] ] and loop_sound == [ None, None, None, None ]:
        return
    check_init_mixer()
    for voice in range(4):
        # if there is a sound queue, stop looping sound
        if sound_queue[voice] and loop_sound[voice]:
            stop_channel(voice)
            loop_sound[voice] = None
        if mixer.Channel(voice).get_queue() == None:
            if loop_sound[voice]:
                # loop the current playing sound; ok to interrupt it with play cos it's the same sound as is playing
                current_chunk[voice] = loop_sound[voice].build_chunk()
            elif sound_queue[voice]:
                current_chunk[voice] = sound_queue[voice][0].build_chunk()
                if not current_chunk[voice]:
                    sound_queue[voice].pop(0)
                    try:
                        current_chunk[voice] = sound_queue[voice][0].build_chunk()
                    except IndexError:
                        # sound_queue is empty
                        break
                if sound_queue[voice][0].loop:
                    loop_sound[voice] = sound_queue[voice].pop(0)
                    # any next sound in the sound queue will stop this looping sound
                else:   
                    loop_sound[voice] = None
    for voice in range(4):
        if current_chunk[voice]:
            mixer.Channel(voice).queue(current_chunk[voice])
    for voice in range(4):
        # remove the notes that have been sent to mixer
        backend.sound_done(voice, len(sound_queue[voice]))
            
def busy():
    return (not loop_sound[0] and not loop_sound[1] and not loop_sound[2] and not loop_sound[3]) and mixer.get_busy()
        
def play_sound(frequency, total_duration, fill, loop, voice=0, volume=15):
    sound_queue[voice].append(SoundGenerator(signal_sources[voice], frequency, total_duration, fill, loop, volume))

def set_noise(is_white):
    signal_sources[3].feedback = feedback_noise if is_white else feedback_periodic
    
# implementation

# sound generators for sounds not played yet
sound_queue = [ [], [], [], [] ]
# currently looping sound
loop_sound = [ None, None, None, None ]

# mixer settings
mixer_bits = 16
sample_rate = 44100

# initial condition - see dosbox source
init_noise = 0x0f35
# white noise feedback 
feedback_noise = 0x4400 
# 'periodic' feedback mask (15-bit rotation)
feedback_periodic = 0x4000
# square wave feedback mask
feedback_tone = 0x2 

class SignalSource(object):
    def __init__(self, feedback, init=0x01):
        self.lfsr = init 
        self.feedback = feedback
    
    def next(self):
        # get new sample bit
        bit = self.lfsr & 1
        self.lfsr >>= 1
        if bit:
            self.lfsr ^= self.feedback
        return bit

# three tone voices plus a noise source
signal_sources = [ SignalSource(feedback_tone), SignalSource(feedback_tone), SignalSource(feedback_tone), 
                        SignalSource(feedback_noise, init_noise) ]

# The SN76489 attenuates the volume by 2dB for each step in the volume register.
# see http://www.smspower.org/Development/SN76489
max_amplitude = (1<<(mixer_bits-1)) - 1
# 2 dB steps correspond to a voltage factor of 10**(-2./20.) as power ~ voltage**2 
step_factor = 10**(-2./20.)
# geometric list of amplitudes for volume values 
amplitude = [0]*16 if not numpy else numpy.int16(max_amplitude*(step_factor**numpy.arange(15,-1,-1)))
# zero volume means silent
amplitude[0] = 0


class SoundGenerator(object):
    def __init__(self, signal_source, frequency, total_duration, fill, loop, volume):
        # noise generator
        self.signal_source = signal_source
        # one wavelength at 37 Hz is 1192 samples at 44100 Hz
        self.chunk_length = 1192 * 4
        # actual duration and gap length
        self.duration = fill * total_duration
        self.gap = (1-fill) * total_duration
        self.amplitude = amplitude[volume]
        self.frequency = frequency
        self.loop = loop
        self.bit = 0
        self.count_samples = 0
        self.num_samples = int(self.duration * sample_rate)
        
    def build_chunk(self):
        if self.count_samples >= self.num_samples:
            # done already
            return None
        # work on last element of sound queue
        check_init_mixer()
        if self.frequency == 0 or self.frequency == 32767:
            chunk = numpy.zeros(self.chunk_length, numpy.int16)
        else:
            half_wavelength = sample_rate / (2.*self.frequency)
            num_half_waves = int(ceil(self.chunk_length / half_wavelength))
            # generate bits
            bits = []
            for _ in range(num_half_waves):
                bits.append(-self.amplitude if self.signal_source.next() else self.amplitude)
            # do sampling by averaging the signal over bins of given resolution
            # this allows to use numpy all the way which is *much* faster than looping over an array
            # stretch array by half_wavelength * resolution    
            resolution = 20
            matrix = numpy.repeat(numpy.array(bits, numpy.int16), int(half_wavelength*resolution))
            # cut off on round number of resolution blocks
            matrix = matrix[:len(matrix)-(len(matrix)%resolution)]
            # average over blocks                        
            matrix = matrix.reshape((len(matrix)/resolution, resolution))
            chunk = numpy.int16(numpy.average(matrix, axis=1))
        if not self.loop:    
            # make the last chunk longer than a normal chunk rather than shorter, to avoid jumping sound    
            if self.count_samples + 2*len(chunk) < self.num_samples:
                self.count_samples += len(chunk)
            else:
                # append final chunk
                rest_length = self.num_samples - self.count_samples
                chunk = chunk[:rest_length]
                # append quiet gap if requested
                if self.gap:
                    gap_chunk = numpy.zeros(int(self.gap * sample_rate), numpy.int16)
                    chunk = numpy.concatenate((chunk, gap_chunk))
                # done                
                self.count_samples = self.num_samples
        # if loop, attach one chunk to loop, do not increment count
        return pygame.sndarray.make_sound(chunk)   

def stop_channel(channel):
    if mixer.get_init():
        mixer.Channel(channel).stop()
        # play short silence to avoid blocking the channel - it won't play on queue()
        silence = pygame.sndarray.make_sound(numpy.zeros(1, numpy.int16))
        mixer.Channel(channel).play(silence)
    
def pre_init_mixer():
    if mixer:
        mixer.pre_init(sample_rate, -mixer_bits, channels=1, buffer=1024) #4096

def init_mixer():    
    if mixer:
        mixer.quit()
    
def check_init_mixer():
    if mixer.get_init() == None:
        mixer.init()

def quit_sound():
    if mixer.get_init() != None:
        mixer.quit()
    
                
prepare()

