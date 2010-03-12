from random import choice

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
    letter = 'h'
    add_message = 'You start to notice strange shapes in the darkness.'
    remove_message = 'The darkness is calm once again.'
    long_descr = 'You are hallucinating.'
    sanity_range = 70, 45

    def do_effect(self, severity):
        super(Hallu, self).do_effect(severity)
        m = self.player.map
        for i in range(severity):
            mcls = random_by_level(m.level, UnrealMonster.ALL)
            m.place_monsters(mcls, not_seen=True)

    def remove(self):
        super(Hallu, self).remove()
        for mon in filter(lambda m: isinstance(m, UnrealMonster),
                          self.player.map.mobs):
            mon.remove()

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

EFFECTS = [Hallu, Real, Fear]

def add_insane_effects(player):
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
