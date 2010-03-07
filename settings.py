import libtcodpy as libtcod

INVENTORY_SIZE = 8

SCREEN_W = 70
SCREEN_H = 32

MAP_W = 50
MAP_H = 25

BUFFER_H = 5

FONT = ('fonts/terminal10x10_gs_tc.png',
        libtcod.FONT_LAYOUT_TCOD | libtcod.FONT_TYPE_GREYSCALE)
#FONT = ('fonts/arial12x12.png',
#        libtcod.FONT_LAYOUT_TCOD | libtcod.FONT_TYPE_GREYSCALE)

VERSION = '0.1'
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
