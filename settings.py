import libtcodpy as libtcod

WIZARD = True

INVENTORY_SIZE = 8

SCREEN_W = 80
SCREEN_H = 25

MAP_W = 60
MAP_H = 20

BUFFER_H = 4

FONTS = [
    ('fonts/terminal10x18.png',
     libtcod.FONT_LAYOUT_ASCII_INROW),
    ('fonts/terminal8x15.png',
     libtcod.FONT_LAYOUT_ASCII_INROW),
    ('fonts/terminal8x8.png',
     libtcod.FONT_LAYOUT_ASCII_INCOL),
]
FONT_INDEX = 0

VERSION = '0.2'
TITLE = 'Madness v' + VERSION

TITLE_SCREEN = [
    (libtcod.white, TITLE),
    '',
    (libtcod.light_grey, 'by hmp <humpolec@gmail.com>'),
    '',
    '',
    'Press any key to continue',
]

UNKNOWN_GLYPH = '?', libtcod.red

MAX_SANITY = 100

MAX_SPEED = 5
MIN_SPEED = -4

MAX_CLEVEL = 10
