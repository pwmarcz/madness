import tcod as T

from settings import *
from map import *
from mob import *
from item import *
from util import in_map
import ui

KEYS = [
    (['y', '7', T.KEY_KP7], ('walk', (-1, -1))),
    (['k', '8', T.KEY_KP8, T.KEY_UP], ('walk', (0, -1))),
    (['u', '9', T.KEY_KP9], ('walk', (1, -1))),
    (['h', '4', T.KEY_KP4, T.KEY_LEFT], ('walk', (-1, 0))),
    (['.', '5', T.KEY_KP5], 'wait'),
    (['l', '6', T.KEY_KP6, T.KEY_RIGHT], ('walk', (1, 0))),
    (['b', '1', T.KEY_KP1], ('walk', (-1, 1))),
    (['j', '2', T.KEY_KP2, T.KEY_DOWN], ('walk', (0, 1))),
    (['n', '3', T.KEY_KP3], ('walk', (1, 1))),
    (['q', T.KEY_ESCAPE], 'quit'),
    (['g', ','], 'pick_up'),
    (['i'], 'inventory'),
    (['d'], 'drop'),
    (['>'], 'descend'),
    (['x'], 'look'),
    (['?'], 'help'),
    ([T.KEY_F10], 'cycle_font'),
    (['W'], 'wizard'),
]

def decode_key(key):
    for keys, cmd in KEYS:
        if key in keys:
            return cmd
    return None

class Quit(Exception):
    pass

class Game(object):
    def __init__(self, wizard):
        self.wizard = wizard

    def play(self):
        ui.init(self)
        ui.title_screen()
        self.start()
        self.loop()
        ui.close()

    def start(self):
        self.player = Player(self.wizard)
        self.turns = 0
        ui.message('Welcome to Madness!')
        ui.message('Press ? for help.')
        self.start_map(1)

    def start_map(self, level):
        # some message on enter?
        self.map = Map(level)

        x, y, _ = self.map.random_empty_tile()
        self.player.put(self.map, x, y)

    def loop(self):
        ui.draw_all()
        try:
            while True:
                if self.player.death:
                    if self.wizard:
                        if ui.prompt('Die? [yn]', 'yn') == 'n':
                            ui.new_ui_turn()
                            self.player.resurrect()
                            ui.draw_all()
                            continue
                    ui.prompt(
                        '[Game over: %s. Press ENTER]' % self.player.death,
                        [T.KEY_ENTER, T.KEY_KPENTER])
                    self.save_character_dump()
                    raise Quit()
                if self.player.won:
                    ui.prompt(
                        'Congratulations! You have won. Press ENTER',
                        [T.KEY_ENTER, T.KEY_KPENTER])
                    self.save_character_dump()
                    raise Quit()
                while self.player.action_turns > 0:
                    key = ui.readkey()
                    self.do_command(key)
                self.map.do_turn(self.turns)
                self.turns += 1
                ui.draw_all()
        except Quit:
            pass

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
        ui.draw_all()

    def cmd_walk(self, dx, dy):
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
        if ui.prompt('Quit? [yn]', 'yn') == 'y':
            raise Quit()
        else:
            ui.new_ui_turn()

    def cmd_cycle_font(self):
        ui.cycle_font()

    def cmd_help(self):
        ui.help_screen()

    def cmd_wizard(self):
        if self.wizard and self.map.level < MAX_DLEVEL:
            self.start_map(self.map.level+1)

    def cmd_look(self):
        ui.look_mode()

    def save_character_dump(self):
        from datetime import datetime

        try:
            with open('character.txt', 'w') as f:
                f.write('%s - character dump\n\n' % TITLE)
                f.write(datetime.strftime(datetime.now(), '%d/%m/%Y %H:%M')+'\n\n')
                f.write('  MAP\n\n')
                for y in range(MAP_H):
                    for x in range(MAP_W):
                        tile = self.map.tiles[x][y]
                        if tile.mob and not isinstance(tile.mob, UnrealMonster):
                            c, _ = tile.mob.glyph
                        elif tile.items:
                            c, _ = tile.items[-1].glyph
                        elif all(not tile.transparent
                                 for tile in self.map.neighbor_tiles(x, y)):
                            c = ' '
                        else:
                            c, _ = tile.glyph
                        f.write(c)
                    f.write('\n')
                f.write('\n  LAST MESSAGES\n\n')
                for _, s, _ in ui.MESSAGES[-10:]:
                    f.write(s+'\n')
                f.write('\n  STATUS\n\n')
                f.write('\n'.join(ui.status_lines()))
                f.write('\n\n  INVENTORY\n\n')
                for item in self.player.items:
                    f.write('%s%s\n' %
                            ('*' if self.player.has_equipped(item) else ' ',
                             item.descr))
                if self.player.effects:
                    f.write('\n  INSANITY\n\n')
                    for eff in list(self.player.effects.values()):
                        f.write(eff.long_descr + '\n')
        except IOError:
            pass
