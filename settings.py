import tcod

INVENTORY_SIZE = 9

SCREEN_W = 80
SCREEN_H = 25

MAP_W = 59
MAP_H = 18

BUFFER_H = 5

FONTS = [
    ('fonts/terminal10x18.png',
     tcod.FONT_LAYOUT_ASCII_INROW),
    ('fonts/terminal8x15.png',
     tcod.FONT_LAYOUT_ASCII_INROW),
    ('fonts/terminal8x8.png',
     tcod.FONT_LAYOUT_ASCII_INCOL),
]

VERSION = '1.0'
TITLE = 'Madness v' + VERSION

TITLE_SCREEN = [
    (tcod.white, TITLE),
    '',
    (tcod.light_grey, 'by hmp <humpolec@gmail.com>'),
    '',
    '',
    'Press any key to continue',
]

HELP_TEXT = '''\
--- Madness - a roguelike ---

  Your task is simple: reach level 10 of the dungeon and defeat the evil
Dungeon Master. Be careful - not all of what you see is real. And not all of
what isn't real is harmless...

  You start with a torch in your backpack. Use it well.

--- Keybindings ---
Move:  numpad,             Inventory:    i
       arrow keys,         Pick up:      g, ,
       yuhjklbn            Drop:         d
Wait:  5, .                Descend:      >
Look:  x                   Change font:  F10
Help:  ?                   Quit:         q, Esc

[Press any key to continue]'''

UNKNOWN_GLYPH = '?', tcod.red

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
