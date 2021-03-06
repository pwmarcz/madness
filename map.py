from random import randrange, choice, shuffle

import tcod as T

from mob import Monster, UnrealMonster, Player, Boss
from item import Item
from mapgen import generate_map
from settings import *
from util import *
import ui

class Map(object):
    def __init__(self, level):
        self.tiles = generate_map(level)
        self.level = level

        self.player = None
        self.mobs = []

        self.fov_map = T.map_new(MAP_W, MAP_H)
        for x in range(MAP_W):
            for y in range(MAP_H):
                tile = self.tiles[x][y]
                T.map_set_properties(self.fov_map,
                                           x, y,
                                           tile.transparent,
                                           tile.walkable)

        self.populate()
        if self.level == MAX_DLEVEL:
            self.place_monsters(Boss)

    # def __del__(self):
    #     T.map_delete(self.fov_map)

    def find_tile(self, func):
        for x in range(MAP_W):
            for y in range(MAP_H):
                tile = self.tiles[x][y]
                if func(tile):
                    return (x, y, tile)

    def recalc_fov(self):
        T.map_compute_fov(self.fov_map,
                                self.player.x, self.player.y,
                                MAP_W,
                                True)
        for x in range(MAP_W):
            for y in range(MAP_H):
                if self.is_visible(x, y):
                    self.tiles[x][y].remember_glyph()

    def is_visible(self, x, y):
        return T.map_is_in_fov(self.fov_map, x, y) and \
            distance(x, y, self.player.x, self.player.y) <= \
            self.player.fov_range

    def neighbor_tiles(self, x, y):
        for dx, dy in ALL_DIRS:
            if in_map(x+dx, y+dy):
                yield self.tiles[x+dx][y+dy]

    # def __del__(self):
    #     T.map_delete(self.fov_map)

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

    def populate(self):
        n_monsters = 3 + roll(2, self.level)
        n_items = roll(2, 4, 1)
        for i in range(n_monsters):
            mcls = random_by_level(self.level, Monster.ALL)
            self.place_monsters(mcls)
        for i in range(n_items):
            x, y, tile = self.random_empty_tile(no_mob=False, no_stair=True)
            item = random_by_level(self.level, Item.ALL)()
            tile.items.append(item)

    def flood(self, x, y, mcls, n):
        if n == 0:
            return n
        if x < 0 or x >= MAP_W or y < 0 or y >= MAP_H:
            return n
        tile = self.tiles[x][y]
        if tile.mob or not tile.walkable:
            return n
        mcls().put(self, x, y)
        n -= 1
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        shuffle(dirs)
        for dx, dy in dirs:
            n = self.flood(x+dx, y+dy, mcls, n)
        return n

    def place_monsters(self, mcls, *args, **kwargs):
        x, y, tile = self.random_empty_tile(*args, **kwargs)
        self.flood(x, y, mcls, mcls.multi)

    def random_empty_tile(self, no_mob=True, not_seen=False, no_stair=False):
        while True:
            x, y = randrange(MAP_W), randrange(MAP_H)
            tile = self.tiles[x][y]
            if not tile.walkable:
                continue
            if no_mob and tile.mob:
                continue
            if not_seen and self.is_visible(x, y):
                continue
            if no_stair and isinstance(tile, StairDownTile):
                continue
            return (x, y, tile)

class Tile(object):
    walkable = True
    transparent = True
    glyph = UNKNOWN_GLYPH
    known_glyph = ' ', T.white

    def __init__(self):
        self.mob = None
        self.items = []

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

    def on_enter(self):
        pass

class FloorTile(Tile):
    name = 'floor'
    walkable = True
    transparent = True
    glyph = '.', T.grey

class WallTile(Tile):
    name = 'stone wall'
    walkable = False
    transparent = False
    glyph = '#', T.grey

class WoodWallTile(Tile):
    name = 'wooden wall'
    walkable = False
    transparent = False
    glyph = '#', T.dark_orange

class StairUpTile(Tile):
    name = 'stairs up'
    walkable = True
    transparent = True
    glyph = '<', T.light_grey

class StairDownTile(Tile):
    name = 'stairs down'
    walkable = True
    transparent = True
    glyph = '>', T.light_grey

    def on_enter(self):
        ui.message('There is a down stairway here.')
