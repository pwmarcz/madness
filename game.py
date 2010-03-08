import libtcodpy as libtcod

from settings import *
from mapgen import generate_map
from map import *
from mob import *
from item import *
import ui

KEYS = [
    (['y', '7'], ('walk', (-1, -1))),
    (['k', '8', libtcod.KEY_UP], ('walk', (0, -1))),
    (['u', '9'], ('walk', (1, -1))),
    (['h', '4', libtcod.KEY_LEFT], ('walk', (-1, 0))),
    (['.', '5'], 'wait'),
    (['l', '6', libtcod.KEY_RIGHT], ('walk', (1, 0))),
    (['b', '1'], ('walk', (-1, 1))),
    (['j', '2', libtcod.KEY_DOWN], ('walk', (0, 1))),
    (['n', '3'], ('walk', (1, 1))),
    (['q', libtcod.KEY_ESCAPE], 'quit'),
    (['g', ','], 'pick_up'),
    (['i'], 'inventory'),
    (['d'], 'drop'),
    (['>'], 'descend'),
    (['?'], 'help'),
    ([libtcod.KEY_F10], 'cycle_font'),
]

def decode_key(key):
    for ks, cmd in KEYS:
        for k in ks:
            if isinstance(k, str):
                if key.c == ord(k):
                    return cmd
            elif key.vk == k:
                return cmd
    return None

class Game(object):
    def __init__(self):
        pass

    def start(self):
        self.player = Player()
        self.turns = 0
        self.quitting = False
        ui.message('Welcome to Madness!')
        ui.message('Press ? for help.')
        self.start_map(1)

    def start_map(self, level):
        # some message on enter?
        self.map = Map(level, generate_map())

        x, y, _ = self.map.random_empty_tile()
        self.player.put(self.map, x, y)

    def loop(self):
        ui.draw_all()
        while not self.quitting:
            if self.player.death:
                ui.message('[Press ENTER]')
                ui.draw_all()
                while ui.readkey().vk != libtcod.KEY_ENTER:
                    pass
                break
            while self.player.action_turns > 0:
                key = ui.readkey()
                self.do_command(key)
                ui.draw_all()
                if self.quitting:
                    break
            self.map.do_turn(self.turns)
            self.turns += 1
            ui.draw_all()

    def do_command(self, key):
        cmd = decode_key(key)
        if cmd is None:
            return
        ui.new_ui_turn()
        if isinstance(cmd, str):
            getattr(self, 'cmd_'+cmd)()
        else:
            name, args = cmd
            getattr(self, 'cmd_'+name)(*args)

    def cmd_walk(self, dx, dy):
        destx, desty = self.player.x+dx, self.player.y+dy
        tile = self.map.tiles[destx][desty]
        if not tile.walkable:
            pass
        elif tile.mob:
            self.player.attack(tile.mob)
        else:
            self.player.walk(dx, dy)

    def cmd_wait(self):
        self.player.wait()

    def cmd_pick_up(self):
        tile = self.player.tile
        if tile.items == []:
            ui.message('There is nothing here to pick up.')
        elif len(tile.items) == 1:
            self.player.pick_up(tile.items[0])
        else:
            while True and tile.items:
                item = ui.select_item('Select an item to pick up',
                                      tile.items)
                if item:
                    self.player.pick_up(item)
                    ui.draw_all()
                else:
                    break

    def cmd_drop(self):
        item = ui.select_item('Select an item to drop', self.player.items)
        if item:
            self.player.drop(item)

    def cmd_inventory(self):
        item = ui.select_item('Select an item to use', self.player.items)
        if item:
            self.player.use(item)

    def cmd_descend(self):
        if not isinstance(self.player.tile, StairDownTile):
            ui.message('Stand on a down stairway to descend.')
            return
        ui.message('You climb downwards...')
        self.turns += 1
        self.start_map(self.map.level+1)

    def cmd_quit(self):
        if ui.prompt('Really quit? [yn]').c == ord('y'):
            self.quitting = True

    def cmd_cycle_font(self):
        ui.cycle_font()

game = Game()
ui.init(game)
ui.title_screen()
game.start()
game.loop()
ui.close()
