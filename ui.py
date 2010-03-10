from random import choice

import libtcodpy as T

from settings import *
from util import distance, describe_dice

STATUS_W = SCREEN_W-MAP_W-1
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

def _draw_map(m, con):
    for x in range(MAP_W):
        for y in range(MAP_H):
            tile = m.tiles[x][y]
            if m.is_visible(x, y):
                c, color = tile.visible_glyph
                d = distance(x, y, m.player.x, m.player.y)
                if d > m.player.light_range + 1:
                    color *= 0.6
                color = insanize_color(color, GAME.player.sanity)
            else:
                c, _ = tile.known_glyph
                color = T.color_lerp(T.darker_grey, T.dark_grey,
                                     GAME.player.sanity/100.0)
            T.console_put_char_ex(con, x, y, ord(c),
                                  color, T.black)

def _draw_status(con):
    T.console_clear(con)
    T.console_set_foreground_color(con, T.light_grey)
    status = [
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
    T.console_print_left(con, 0, 0, T.BKGND_NONE,
                               '\n'.join(status))

def _draw_messages(m, con):
    if not m:
        return
    n = len(m)
    start = max(n-BUFFER_H,0)
    T.console_clear(con)
    for i in range(start, n):
        latest, s, color = m[i]
        if not latest:
            color *= 0.6
        T.console_set_foreground_color(
            con,
            color)
        T.console_print_left(con, 0, i-start, T.BKGND_NONE, s)

def _draw_items(title, items, con):
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
        if GAME.player.is_equipped(item):
            T.console_put_char_ex(con, 0, i+2, ord('*'),
                                  T.light_grey, T.BKGND_NONE)
            T.console_set_foreground_color(con, T.white)
        else:
            T.console_set_foreground_color(con, T.grey)
        T.console_print_left(con, 6, i+2, T.BKGND_NONE, s)

def draw_inventory(title='Inventory', items=None):
    _draw_items(title, items or GAME.player.items, CON_INV)
    T.console_blit(CON_INV, 0, 0, INV_W, INV_H,
                   None, 0, 0)
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
    _draw_map(GAME.map, CON_MAP)
    _draw_messages(MESSAGES, CON_BUFFER)
    _draw_status(CON_STATUS)
    T.console_blit(CON_MAP, 0, 0, MAP_W, MAP_H,
                   None, 0, 0)
    T.console_blit(CON_BUFFER, 0, 0, SCREEN_W, BUFFER_H,
                   None, 0, MAP_H)
    T.console_blit(CON_STATUS, 0, 0, STATUS_W, STATUS_H,
                   None, MAP_W+1, 0)
    T.console_flush()

def message(s, color=T.white):
    s = s[0].upper() + s[1:]
    print s
    MESSAGES.append((True, s, color))

def prompt(s, choices=None):
    message(s, T.green)
    draw_all()
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
