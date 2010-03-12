from random import choice, shuffle

from util import *
from mob import *
import ui

class InsaneEffect(object):
    letter = '?'

    add_message = ''
    remove_message = ''
    long_descr = '<description>'

    def add(self, player):
        self.player = player
        assert self.letter not in player.effects
        player.effects[self.letter] = self
        if self.add_message:
            ui.message(self.add_message, T.yellow)

    def remove(self):
        assert self.letter in self.player.effects
        del self.player.effects[self.letter]
        if self.remove_message:
            ui.message(self.remove_message, T.yellow)

    def do_effect(self, severity):
        pass

class Hallu(InsaneEffect):
    sanity_range = 70, 45

    def add(self, player):
        if self.exclude not in player.effects:
            super(Hallu, self).add(player)

    def do_effect(self, severity):
        super(Hallu, self).do_effect(severity)
        m = self.player.map
        for i in range(severity):
            mcls = random_by_level(m.level, self.monsters_from.ALL)
            m.place_monsters(mcls, not_seen=True)

    def remove(self):
        super(Hallu, self).remove()
        for mon in filter(lambda m: not m.real,
                          self.player.map.mobs):
            mon.remove()

class Happy(Hallu):
    letter = 'h'
    exclude = 'd'
    add_message = 'You see a rainbow in the distance.'
    remove_message = 'The darkness is calm once again.'
    long_descr = 'You are hallucinating.'
    monsters_from = HappyMonster

class Dark(Hallu):
    letter = 'd'
    exclude = 'h'
    remove_message = 'The darkness is calm once again.'
    long_descr = 'You are afraid of the dark.'
    monsters_from = DarkMonster

    @property
    def add_message(self):
        if self.player.light_range > 0:
            return 'The light suddenly becomes dim.'
        else:
            return 'You notice strange shapes in the darkness.'

class Real(InsaneEffect):
    sanity_range = 40, 30
    letter = 'r'
    long_descr = 'Figments of your imagination can hurt you.'

class Fear(InsaneEffect):
    sanity_range = 30, 10
    letter = 'f'
    add_message = 'You suddenly feel very uneasy.'
    remove_message = 'You feel less frightened.'
    long_descr = 'You are paralyzed by fear.'

EFFECTS = [Dark, Happy, Real, Fear]

def add_insane_effects(player):
    shuffle(EFFECTS)
    for ecls in EFFECTS:
        if ecls.letter in player.effects:
            continue
        upper, lower = ecls.sanity_range
        if player.sanity > upper:
            continue
        elif player.sanity <= lower:
            ecls().add(player)
        else: # in range
            if roll(1, 20) == 1:
                ecls().add(player)
