from .scancode import *


SDLK_SCANCODE_MASK = 1 << 30
SDL_SCANCODE_TO_KEYCODE = lambda x: (x | SDLK_SCANCODE_MASK)

KMOD_NONE = 0x0000
KMOD_LSHIFT = 0x0001
KMOD_RSHIFT = 0x0002
KMOD_LCTRL = 0x0040
KMOD_RCTRL = 0x0080
KMOD_LALT = 0x0100
KMOD_RALT = 0x0200
KMOD_LGUI = 0x0400
KMOD_RGUI = 0x0800
KMOD_NUM = 0x1000
KMOD_CAPS = 0x2000
KMOD_MODE = 0x4000
KMOD_RESERVED = 0x8000

KMOD_CTRL = KMOD_LCTRL | KMOD_RCTRL
KMOD_SHIFT = KMOD_LSHIFT | KMOD_RSHIFT
KMOD_ALT = KMOD_LALT | KMOD_RALT
KMOD_GUI = KMOD_LGUI | KMOD_RGUI

SDLK_UNKNOWN = 0

SDLK_RETURN = ord('\r')
SDLK_ESCAPE = ord('\033')
SDLK_BACKSPACE = ord('\b')
SDLK_TAB = ord('\t')
SDLK_SPACE = ord(' ')
SDLK_EXCLAIM = ord('!')
SDLK_QUOTEDBL = ord('"')
SDLK_HASH = ord('#')
SDLK_PERCENT = ord('%')
SDLK_DOLLAR = ord('$')
SDLK_AMPERSAND = ord('&')
SDLK_QUOTE = ord('\'')
SDLK_LEFTPAREN = ord('(')
SDLK_RIGHTPAREN = ord(')')
SDLK_ASTERISK = ord('*')
SDLK_PLUS = ord('+')
SDLK_COMMA = ord(',')
SDLK_MINUS = ord('-')
SDLK_PERIOD = ord('.')
SDLK_SLASH = ord('/')

SDLK_0 = ord('0')
SDLK_1 = ord('1')
SDLK_2 = ord('2')
SDLK_3 = ord('3')
SDLK_4 = ord('4')
SDLK_5 = ord('5')
SDLK_6 = ord('6')
SDLK_7 = ord('7')
SDLK_8 = ord('8')
SDLK_9 = ord('9')

SDLK_COLON = ord(':')
SDLK_SEMICOLON = ord(';')
SDLK_LESS = ord('<')
SDLK_EQUALS = ord('=')
SDLK_GREATER = ord('>')
SDLK_QUESTION = ord('?')
SDLK_AT = ord('@')

SDLK_LEFTBRACKET = ord('[')
SDLK_BACKSLASH = ord('\\')
SDLK_RIGHTBRACKET = ord(']')
SDLK_CARET = ord('^')
SDLK_UNDERSCORE = ord('_')
SDLK_BACKQUOTE = ord('`')

SDLK_a = ord('a')
SDLK_b = ord('b')
SDLK_c = ord('c')
SDLK_d = ord('d')
SDLK_e = ord('e')
SDLK_f = ord('f')
SDLK_g = ord('g')
SDLK_h = ord('h')
SDLK_i = ord('i')
SDLK_j = ord('j')
SDLK_k = ord('k')
SDLK_l = ord('l')
SDLK_m = ord('m')
SDLK_n = ord('n')
SDLK_o = ord('o')
SDLK_p = ord('p')
SDLK_q = ord('q')
SDLK_r = ord('r')
SDLK_s = ord('s')
SDLK_t = ord('t')
SDLK_u = ord('u')
SDLK_v = ord('v')
SDLK_w = ord('w')
SDLK_x = ord('x')
SDLK_y = ord('y')
SDLK_z = ord('z')

SDLK_CAPSLOCK = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_CAPSLOCK)

SDLK_F1 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_F1)
SDLK_F2 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_F2)
SDLK_F3 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_F3)
SDLK_F4 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_F4)
SDLK_F5 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_F5)
SDLK_F6 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_F6)
SDLK_F7 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_F7)
SDLK_F8 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_F8)
SDLK_F9 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_F9)
SDLK_F10 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_F10)
SDLK_F11 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_F11)
SDLK_F12 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_F12)

SDLK_PRINTSCREEN = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_PRINTSCREEN)
SDLK_SCROLLLOCK = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_SCROLLLOCK)
SDLK_PAUSE = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_PAUSE)
SDLK_INSERT = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_INSERT)
SDLK_HOME = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_HOME)
SDLK_PAGEUP = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_PAGEUP)
SDLK_DELETE = ord('\177')
SDLK_END = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_END)
SDLK_PAGEDOWN = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_PAGEDOWN)
SDLK_RIGHT = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_RIGHT)
SDLK_LEFT = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_LEFT)
SDLK_DOWN = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_DOWN)
SDLK_UP = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_UP)

SDLK_NUMLOCKCLEAR = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_NUMLOCKCLEAR)
SDLK_KP_DIVIDE = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_KP_DIVIDE)
SDLK_KP_MULTIPLY = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_KP_MULTIPLY)
SDLK_KP_MINUS = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_KP_MINUS)
SDLK_KP_PLUS = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_KP_PLUS)
SDLK_KP_ENTER = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_KP_ENTER)
SDLK_KP_1 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_KP_1)
SDLK_KP_2 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_KP_2)
SDLK_KP_3 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_KP_3)
SDLK_KP_4 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_KP_4)
SDLK_KP_5 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_KP_5)
SDLK_KP_6 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_KP_6)
SDLK_KP_7 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_KP_7)
SDLK_KP_8 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_KP_8)
SDLK_KP_9 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_KP_9)
SDLK_KP_0 = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_KP_0)
SDLK_KP_PERIOD = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_KP_PERIOD)

SDLK_KP_EQUALS = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_KP_EQUALS)

SDLK_LCTRL = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_LCTRL)
SDLK_LSHIFT = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_LSHIFT)
SDLK_LALT = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_LALT)
SDLK_LGUI = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_LGUI)
SDLK_RCTRL = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_RCTRL)
SDLK_RSHIFT = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_RSHIFT)
SDLK_RALT = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_RALT)
SDLK_RGUI = SDL_SCANCODE_TO_KEYCODE(SDL_SCANCODE_RGUI)
