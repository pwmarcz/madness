from random import choice

import libtcodpy as T

from settings import *
from util import distance, describe_dice, in_map

STATUS_W = SCREEN_W-MAP_W-2
STATUS_H = 10
INV_W = SCREEN_W
INV_H = INVENTORY_SIZE + 3

FONT_INDEX = 0

def init(game):
    global CON_MAP, CON_BUFFER, CON_STATUS, CON_INV, MESSAGES, GAME
    GAME = game
    T.console_set_custom_font(*FONTS[FONT_INDEX])
    T.console_init_root(SCREEN_W, SCREEN_H, TITLE, False)
    CON_MAP = T.console_new(MAP_W, MAP_H)
    CON_BUFFER = T.console_new(SCREEN_W, BUFFER_H)
    CON_STATUS = T.console_new(STATUS_W, STATUS_H)
    CON_INV = T.console_new(INV_W, INV_H)
    MESSAGES = []

def cycle_font():
    global FONT_INDEX
    FONT_INDEX = (FONT_INDEX + 1) % len(FONTS)
    T.console_set_custom_font(*FONTS[FONT_INDEX])
    T.console_init_root(SCREEN_W, SCREEN_H, TITLE, False)

def close():
    GAME = None
    T.console_delete(CON_MAP)
    T.console_delete(CON_BUFFER)
    T.console_delete(CON_STATUS)
    T.console_delete(CON_INV)

def insanize_color(color, sanity):
    if sanity < 50:
        color2 = choice([
                T.black, T.white, T.green, T.yellow,
                T.sky, T.red, T.pink])
        d = 0.4*(1 - sanity / 50.0)
        color = T.color_lerp(color, color2, d)
        return color
    else:
        return color

def _draw_map():
    con = CON_MAP
    for x in range(MAP_W):
        for y in range(MAP_H):
            tile = GAME.map.tiles[x][y]
            if GAME.map.is_visible(x, y):
                c, color = tile.visible_glyph
                d = distance(x, y, GAME.map.player.x, GAME.map.player.y)
                if d > GAME.map.player.light_range + 1:
                    color *= 0.6
                color = insanize_color(color, GAME.player.sanity)
            else:
                c, _ = tile.known_glyph
                color = T.color_lerp(T.darker_grey, T.dark_grey,
                                     GAME.player.sanity/100.0)
            T.console_put_char_ex(con, x, y, ord(c),
                                  color, T.black)
    T.console_blit(con, 0, 0, MAP_W, MAP_H,
                   None, 1, 1)


def status_lines():
    return [
        'Dlvl: %d' % GAME.map.level,
        '',
        'L%d%s' % (GAME.player.level, ' [wizard mode]' if GAME.wizard else ''),
        'HP:     %d/%d' % (GAME.player.hp, GAME.player.max_hp),
        'Armor:  %d' % GAME.player.armor,
        'Sanity: %d' % GAME.player.sanity,
        'Speed:  %d' % GAME.player.speed,
        'Damage: %s' % describe_dice(*GAME.player.dice),
        'Turns:  %d' % GAME.turns,
    ]

def _draw_status():
    con = CON_STATUS
    T.console_clear(con)
    T.console_set_foreground_color(con, T.light_grey)
    status = status_lines()
    T.console_print_left(con, 0, 0, T.BKGND_NONE,
                               '\n'.join(status))
    T.console_blit(CON_STATUS, 0, 0, STATUS_W, STATUS_H,
                   None, MAP_W+1, 1)


def _draw_messages():
    con = CON_BUFFER
    n = len(MESSAGES)
    if n == 0:
        return
    start = max(n-BUFFER_H,0)
    T.console_clear(con)
    for i in range(start, n):
        latest, s, color = MESSAGES[i]
        if not latest:
            color *= 0.6
        T.console_set_foreground_color(
            con,
            color)
        T.console_print_left(con, 0, i-start, T.BKGND_NONE, s)
    T.console_blit(con, 0, 0, SCREEN_W, BUFFER_H,
                   None, 1, MAP_H+1)

def _draw_items(title, items):
    con = CON_INV
    T.console_clear(con)
    T.console_set_foreground_color(con, T.white)
    T.console_print_left(con, 1, 0, T.BKGND_NONE, title)
    T.console_set_foreground_color(con, T.light_grey)
    for i, item in enumerate(items):
        T.console_put_char_ex(con, 2, i+2, (i+ord('a')),
                              T.light_grey, T.BKGND_NONE)
        c, color = item.glyph
        T.console_put_char_ex(con, 4, i+2, ord(c), color, T.black)
        s = item.descr
        if GAME.player.has_equipped(item):
            T.console_put_char_ex(con, 0, i+2, ord('*'),
                                  T.light_grey, T.BKGND_NONE)
            T.console_set_foreground_color(con, T.white)
        else:
            T.console_set_foreground_color(con, T.grey)
        T.console_print_left(con, 6, i+2, T.BKGND_NONE, s)
    T.console_blit(con, 0, 0, INV_W, INV_H,
                   None, 1, 1)

def draw_inventory(title='Inventory', items=None):
    _draw_items(title, items or GAME.player.items)
    T.console_flush()

def select_item(title, items):
    items = items[:INVENTORY_SIZE]
    draw_inventory(title, items)
    key = readkey()
    if type(key) == str:
        i = ord(key) - ord('a')
        if 0 <= i < len(items):
            return items[i]
    return None

def draw_all():
    T.console_clear(None)
    _draw_map()
    _draw_messages()
    _draw_status()
    T.console_flush()

def message(s, color=T.white):
    s = s[0].upper() + s[1:]
    print s
    while len(MESSAGES) > BUFFER_H-1 and \
            MESSAGES[-BUFFER_H][0]:
        m = MESSAGES.pop()
        MESSAGES.append((True, '[more]', T.green))
        _draw_messages()
        T.console_flush()
        readkey()
        MESSAGES.pop()
        new_ui_turn()
        MESSAGES.append(m)

    MESSAGES.append((True, s, color))
    _draw_messages()
    T.console_flush()

def prompt(s, choices=None):
    message(s, T.green)
    #draw_all()
    if choices:
        choices = list(choices)
        while True:
            key = readkey()
            if key in choices:
                return key
    else:
        return readkey()

def new_ui_turn():
    for i in reversed(range(len(MESSAGES))):
        latest, s, color = MESSAGES[i]
        if latest:
            MESSAGES[i] = False, s, color
        else:
            break

def title_screen():
    T.console_clear(None)
    for i, txt in enumerate(TITLE_SCREEN):
        if isinstance(txt, tuple):
            color, s = txt
            T.console_set_foreground_color(None, color)
        else:
            s = txt
        T.console_print_center(None, SCREEN_W/2, i+5, T.BKGND_NONE, s)
    T.console_flush()
    readkey()

def help_screen():
    T.console_clear(None)
    T.console_set_foreground_color(None, T.light_grey)
    for i, line in enumerate(HELP_TEXT.split('\n')):
        T.console_print_left(None, 1, 1+i, T.BKGND_NONE, line)
    T.console_flush()
    readkey()

def describe_tile(x, y):
    if GAME.map.is_visible(x, y):
        tile = GAME.map.tiles[x][y]
        message('%s.' % tile.name, tile.glyph[1])
        if tile.mob:
            message('%s.' % tile.mob.name, tile.mob.glyph[1])
        for item in tile.items:
            message('%s.' % item.descr, item.glyph[1])
    else:
        message('Out of sight.', T.grey)


def look_mode():
    global MESSAGES
    from game import decode_key

    x, y = GAME.player.x, GAME.player.y
    _messages = MESSAGES
    MESSAGES = []
    message('Look mode - use movement keys, ESC/q to exit.', T.green)
    new_ui_turn()
    _draw_messages()
    redraw = True
    while True:
        if redraw:
            T.console_blit(CON_MAP, 0, 0, MAP_W, MAP_H,
                           None, 1, 1)
            c = T.console_get_char(CON_MAP, x, y)
            color = T.console_get_fore(CON_MAP, x, y)

            T.console_put_char_ex(None, x+1, y+1, c,
                                  T.black, color)

            describe_tile(x, y)

            _draw_messages()
            T.console_flush()

            # now clear the message buffer of last messages
            while MESSAGES and MESSAGES[-1][0]:
                MESSAGES.pop()

            redraw = False
        cmd = decode_key(readkey())
        if cmd == 'quit':
            break
        elif isinstance(cmd, tuple):
            name, args = cmd
            if name == 'walk':
                dx, dy = args
                if in_map(x+dx, y+dy):
                    x, y = x+dx, y+dy
                    redraw = True

    MESSAGES = _messages

def readkey():
    while True:
        key = T.console_wait_for_keypress(True)
        #print key.vk, repr(chr(key.c))
        if key.vk in [T.KEY_SHIFT, T.KEY_CONTROL, T.KEY_ALT,
                      T.KEY_CAPSLOCK]:
            continue
        if key.c != 0 and chr(key.c) not in '\x1b\n\r\t':
            s = chr(key.c)
            if key.shift:
                s = s.upper()
            return s
        elif key.vk != 0:
            return key.vk
