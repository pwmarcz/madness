from random import randrange

import libtcodpy as libtcod

from mob import Monster, Player
from item import Item
from settings import *
from util import *
import ui

class Map(object):
    def __init__(self, level, tiles):
        self.tiles = tiles
        self.level = level

        self.player = None
        self.mobs = []

        self.fov_map = libtcod.map_new(MAP_W, MAP_H)
        for x in range(MAP_W):
            for y in range(MAP_H):
                tile = self.tiles[x][y]
                libtcod.map_set_properties(self.fov_map,
                                           x, y,
                                           tile.walkable,
                                           tile.transparent)

        self.populate(level+1)

    def find_tile(self, func):
        for x in range(MAP_W):
            for y in range(MAP_H):
                tile = self.tiles[x][y]
                if func(tile):
                    return (x, y, tile)

    def recalc_fov(self):
        libtcod.map_compute_fov(self.fov_map,
                                self.player.x, self.player.y,
                                MAP_W,
                                True)
        for x in range(MAP_W):
            for y in range(MAP_H):
                if self.is_visible(x, y):
                    self.tiles[x][y].remember_glyph()

    def is_visible(self, x, y):
        return libtcod.map_is_in_fov(self.fov_map, x, y) and \
            distance(x, y, self.player.x, self.player.y) <= self.player.fov_range

    def __del__(self):
        libtcod.map_delete(self.fov_map)

    def do_turn(self, t):
        for mob in self.mobs:
            mob.heartbeat()
            if mob.speed < 0 and \
                    t%(6+max(mob.speed, MIN_SPEED)) == 0:
                continue
            mob.act()
            if mob.speed > 0 and \
                    t%(6-min(mob.speed, MAX_SPEED)) == 0:
                mob.act()

    def populate(self, level=1, n_monsters=10, n_items=10):
        for x, y, tile in self.good_tiles(n_monsters, True):
            mon = random_by_level(level, Monster.ALL)
            mon.put(self, x, y)
        for x, y, tile in self.good_tiles(n_items, False):
            item = random_by_level(level, Item.ALL)
            tile.items.append(item)

    # Yields n random empty tiles: x,y,tile
    def good_tiles(self, n, no_mob, n_tries=1000):
        for i in xrange(n_tries):
            x, y = randrange(MAP_W), randrange(MAP_H)
            tile = self.tiles[x][y]
            if not tile.walkable:
                continue
            if no_mob and tile.mob:
                continue
            yield (x, y, tile)
            n -= 1
            if n == 0:
                return

    def random_empty_tile(self):
        while True:
            x, y = randrange(MAP_W), randrange(MAP_H)
            tile = self.tiles[x][y]
            if tile.walkable and not tile.mob:
                return (x, y, tile)

class Tile(object):
    walkable = True
    transparent = True
    glyph = UNKNOWN_GLYPH
    known_glyph = ' ', libtcod.white
    # if special, describe on entering
    special = False

    def __init__(self):
        self.mob = None
        self.items = []

    def describe(self):
        if self.special:
            ui.message('%s.' % self.name)
        if self.mob and not isinstance(self.mob, Player):
            ui.message('A %s is here.' % self.mob.name)
        for item in self.items:
            ui.message('You see here %s.' % item.a)

    @property
    def visible_glyph(self):
        if self.mob:
            return self.mob.glyph
        elif self.items:
            return self.items[-1].glyph
        else:
            return self.glyph

    def remember_glyph(self):
        if self.items:
            self.known_glyph = self.items[-1].glyph
        else:
            self.known_glyph = self.glyph

class FloorTile(Tile):
    name = 'floor'
    walkable = True
    transparent = True
    glyph = '.', libtcod.grey

class WallTile(Tile):
    name = 'stone wall'
    walkable = False
    transparent = False
    glyph = '#', libtcod.grey
    special = True

class WoodWallTile(Tile):
    name = 'wooden wall'
    walkable = False
    transparent = False
    glyph = '#', libtcod.dark_orange
    special = True

class StairUpTile(Tile):
    name = 'stairs up'
    walkable = True
    transparent = True
    glyph = '<', libtcod.light_grey
    special = True

class StairDownTile(Tile):
    name = 'stairs down'
    walkable = True
    transparent = True
    glyph = '>', libtcod.light_grey
    special = True
