import libtcodpy as libtcod

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

VERSION = '0.31'
TITLE = 'Madness v' + VERSION

TITLE_SCREEN = [
    (libtcod.white, TITLE),
    '',
    (libtcod.light_grey, 'by hmp <humpolec@gmail.com>'),
    '',
    '',
    'Press any key to continue',
]

HELP_TEXT = '''\
--- Madness - a roguelike ---

  Your task is simple: reach level 10 of the dungeon and defeat the evil
Dungeon Master. Be advised - these are strange dungeons: if you stay long
enough, you may start seeing things that aren't there. If you stay longer,
these things may even kill you...

  You start with a torch in your backpack. It may prove useful - some
creatures don't like light.

--- Keybindings ---
Move:  numpad,             Inventory:    i
       arrow keys,         Pick up:      g, ,
       yuhjklbn            Drop:         d
Wait:  5, .                Descend:      >
Help:  ?                   Change font:  F10
Quit:  q, Esc

[Press any key to continue]'''

UNKNOWN_GLYPH = '?', libtcod.red

MAX_SANITY = 100

MAX_SPEED = 5
MIN_SPEED = -4

MAX_CLEVEL = 6
MAX_DLEVEL = 10

INVENTORY_SLOTS = {
    'w': 'wielded',
    'l': 'carried as light source',
    'a': 'being worn',
    'b': 'being worn',
}
