from random import choice

import libtcodpy as libtcod

from settings import *
from util import distance, describe_dice
from item import SLOTS

STATUS_W = SCREEN_W-MAP_W-1
STATUS_H = 10
INV_W = SCREEN_W
INV_H = INVENTORY_SIZE + 3

def init(game):
    global CON_MAP, CON_BUFFER, CON_STATUS, CON_INV, MESSAGES, GAME
    GAME = game
    libtcod.console_set_custom_font(*FONTS[FONT_INDEX])
    libtcod.console_init_root(SCREEN_W, SCREEN_H, TITLE, False)
    CON_MAP = libtcod.console_new(MAP_W, MAP_H)
    CON_BUFFER = libtcod.console_new(SCREEN_W, BUFFER_H)
    CON_STATUS = libtcod.console_new(STATUS_W, STATUS_H)
    CON_INV = libtcod.console_new(INV_W, INV_H)
    MESSAGES = []

def cycle_font():
    global FONT_INDEX
    FONT_INDEX = (FONT_INDEX + 1) % len(FONTS)
    libtcod.console_set_custom_font(*FONTS[FONT_INDEX])
    libtcod.console_init_root(SCREEN_W, SCREEN_H, TITLE, False)

def close():
    GAME = None
    libtcod.console_delete(CON_MAP)
    libtcod.console_delete(CON_BUFFER)
    libtcod.console_delete(CON_STATUS)
    libtcod.console_delete(CON_INV)

def insanize_color(color, sanity):
    if sanity < 75:
        color2 = choice([
                libtcod.black, libtcod.white, libtcod.green, libtcod.yellow,
                libtcod.sky, libtcod.red, libtcod.pink])
        d = 0.4*(1 - sanity / 75.0)
        color = libtcod.color_lerp(color, color2, d)
        return color
    else:
        return color

def _draw_map(m, con):
    for x in range(MAP_W):
        for y in range(MAP_H):
            tile = m.tiles[x][y]
            if m.is_visible(x, y):
                c, color = tile.visible_glyph
                d = (distance(x, y, m.player.x, m.player.y) /
                     float(m.player.fov_range))
                if d > 0.66:
                    color = libtcod.color_lerp(color, libtcod.dark_grey,
                                               d*3-2)
                color = insanize_color(color, GAME.player.sanity)
            else:
                c, _ = tile.known_glyph
                color = libtcod.dark_grey
            libtcod.console_put_char_ex(con, x, y, ord(c),
                                        color, libtcod.black)

def _draw_status(con):
    libtcod.console_clear(con)
    libtcod.console_set_foreground_color(con, libtcod.light_grey)
    status = [
        'Dlvl: %d' % GAME.map.level,
        '',
        'L%d%s' % (GAME.player.level, ' [wizard mode]' if WIZARD else ''),
        'HP:     %d/%d' % (GAME.player.hp, GAME.player.max_hp),
        'Armor:  %d' % GAME.player.armor,
        'Sanity: %d' % GAME.player.sanity,
        'Speed:  %d' % GAME.player.speed,
        'Damage: %s' % describe_dice(*GAME.player.dice),
        'Turns:  %d' % GAME.turns,
    ]
    libtcod.console_print_left(con, 0, 0, libtcod.BKGND_NONE,
                               '\n'.join(status))

def _draw_messages(m, con):
    if not m:
        return
    n = len(m)
    start = max(n-BUFFER_H,0)
    libtcod.console_clear(con)
    for i in range(start, n):
        latest, s = m[i]
        libtcod.console_set_foreground_color(
            con,
            libtcod.white if latest else libtcod.grey)
        libtcod.console_print_left(con, 0, i-start, libtcod.BKGND_NONE, s)

def _draw_items(title, items, con):
    libtcod.console_clear(con)
    libtcod.console_set_foreground_color(con, libtcod.white)
    libtcod.console_print_left(con, 1, 0, libtcod.BKGND_NONE, title)
    libtcod.console_set_foreground_color(con, libtcod.light_grey)
    for i, item in enumerate(items):
        libtcod.console_put_char_ex(con, 2, i+2, (i+ord('a')),
                                 libtcod.light_grey, libtcod.BKGND_NONE)
        c, color = item.glyph
        libtcod.console_put_char_ex(con, 4, i+2, ord(c), color, libtcod.black)
        s = item.descr
        if GAME.player.is_equipped(item):
            libtcod.console_put_char_ex(con, 0, i+2, ord('*'),
                                        libtcod.light_grey, libtcod.BKGND_NONE)
            libtcod.console_set_foreground_color(con, libtcod.white)
        else:
            libtcod.console_set_foreground_color(con, libtcod.grey)
        libtcod.console_print_left(con, 6, i+2, libtcod.BKGND_NONE, s)

def draw_inventory(title='Inventory', items=None):
    _draw_items(title, items or GAME.player.items, CON_INV)
    libtcod.console_blit(CON_INV, 0, 0, INV_W, INV_H,
                         None, 0, 0)
    libtcod.console_flush()

def select_item(title, items):
    items = items[:INVENTORY_SIZE]
    draw_inventory(title, items)
    key = readkey()
    i = key.c - ord('a')
    if 0 <= i < len(items):
        return items[i]
    else:
        return None

def draw_all():
    libtcod.console_clear(None)
    _draw_map(GAME.map, CON_MAP)
    _draw_messages(MESSAGES, CON_BUFFER)
    _draw_status(CON_STATUS)
    libtcod.console_blit(CON_MAP, 0, 0, MAP_W, MAP_H,
                         None, 0, 0)
    libtcod.console_blit(CON_BUFFER, 0, 0, SCREEN_W, BUFFER_H,
                         None, 0, MAP_H)
    libtcod.console_blit(CON_STATUS, 0, 0, STATUS_W, STATUS_H,
                         None, MAP_W+1, 0)
    libtcod.console_flush()

def message(s):
    s = s[0].upper() + s[1:]
    print s
    MESSAGES.append((True, s))

def prompt(s, choices=None):
    message(s)
    draw_all()
    if choices:
        while True:
            key = readkey()
            if chr(key.c) in choices:
                return key
    else:
        return readkey()

def new_ui_turn():
    for i in reversed(range(len(MESSAGES))):
        latest, s = MESSAGES[i]
        if latest:
            MESSAGES[i] = False, s
        else:
            break

def title_screen():
    libtcod.console_clear(None)
    for i, txt in enumerate(TITLE_SCREEN):
        if isinstance(txt, tuple):
            color, s = txt
            libtcod.console_set_foreground_color(None, color)
        else:
            s = txt
        libtcod.console_print_center(None, SCREEN_W/2, i+5, libtcod.BKGND_NONE, s)
    libtcod.console_flush()


def readkey():
    while True:
        key = libtcod.console_wait_for_keypress(True)
        if key.vk != 0 or key.c != 0:
            return key
