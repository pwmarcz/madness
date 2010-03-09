import libtcodpy as libtcod
from settings import *
from util import *
from random import choice

SLOTS = {
    'w': 'wielded',
    'l': 'carried as light source',
    'a': 'being worn',
    'b': 'being worn',
}

class Item(object):
    ALL = []
    __metaclass__ = Register
    ABSTRACT = True

    glyph = UNKNOWN_GLYPH
    slot = None
    speed = 0
    armor = 0
    plural = False

    @property
    def descr(self):
        return self.name + self.mod_descr

    @property
    def a(self):
        if self.plural:
            return self.descr
        else:
            d = self.descr
            if d[0].lower() in 'aeiuo':
                return 'an '+self.descr
            else:
                return 'a '+self.descr

    @property
    def mod_descr(self):
        s = ''

        if self.speed != 0:
            s += ' (%s%d speed)' % ('+' if self.speed > 0 else '',
                                    self.speed)
        if self.armor != 0:
            s += ' (%s%d armor)' % ('+' if self.armor > 0 else '',
                                    self.armor)
        return s

    def on_equip(self, player):
        player.speed += self.speed
        player.armor += self.armor

    def on_unequip(self, player):
        player.speed -= self.speed
        player.armor -= self.armor

class LightSource(Item):
    ABSTRACT = True
    slot = 'l'

    @property
    def descr(self):
        if self.turns_left == self.turns:
            s = self.name
        else:
            p = 100*self.turns_left/self.turns
            s = '%s (%s%%)' % (self.name, p)
        return s + self.mod_descr

    def __init__(self):
        super(LightSource, self).__init__()
        self.turns_left = self.turns

    def on_equip(self, player):
        player.change_light_range(self.light_range)

    def on_unequip(self, player):
        player.change_light_range(-self.light_range)

class Weapon(Item):
    ABSTRACT = True
    slot = 'w'

    @property
    def descr(self):
        return '%s (%s)%s' % (self.name, describe_dice(*self.dice),
                              self.mod_descr)

class Boots(Item):
    ABSTRACT = True
    slot = 'b'
    plural = True

class Armor(Item):
    ABSTRACT = True
    slot = 'a'

##### LIGHT SOURCES

class Torch(LightSource):
    name = 'torch'
    glyph = '/', libtcod.dark_orange
    level = 1
    turns = 50
    light_range = 5

class Lamp(LightSource):
    name = 'lamp'
    glyph = ']', libtcod.yellow
    level = 4
    turns = 100
    light_range = 10

###### WEAPONS

class HandAxe(Weapon):
    name = 'hand axe'
    glyph = '(', libtcod.grey
    dice = 1, 6, 0
    level = 1

class ShortSword(Weapon):
    name = 'short sword'
    glyph = '(', libtcod.grey
    dice = 1, 6, 0
    level = 1

class Spear(Weapon):
    name = 'spear'
    glyph = '(', libtcod.light_grey
    dice = 1, 8, 2
    level = 2

class Anvil(Weapon):
    name = 'anvil'
    glyph = '(', libtcod.dark_grey
    dice = 1, 12, 2
    level = 3
    speed = -2

class LongSword(Weapon):
    name = 'long sword'
    glyph = '(', libtcod.light_grey
    dice = 1, 8, 4
    level = 4

class SwordHax(Weapon):
    name = 'sword of hax'
    glyph = '(', libtcod.white
    dice = 2, 20, 20
    armor = 5
    level = 1

##### BOOTS

class LightBoots(Boots):
    name = 'light boots'
    slot = 'b'
    glyph = '[', libtcod.dark_orange
    armor = 1
    level = 1

class HeavyBoots(Boots):
    name = 'heavy boots'
    glyph = '[', libtcod.light_grey
    armor = 2
    speed = -1
    level = 3

class BootsSpeed(Boots):
    name = 'boots of speed'
    glyph = '[', libtcod.light_blue
    speed = 2
    level = 5

##### ARMOR

class UglyClothes(Armor):
    name = 'ugly clothes'
    plural = True
    glyph = '[', libtcod.green
    armor = 1
    level = 1

class RingMail(Armor):
    name = 'ring mail'
    glyph = '[', libtcod.grey
    armor = 4
    level = 3

class PlateMail(Armor):
    name = 'plate mail'
    glyph = '[', libtcod.white
    armor = 10
    speed = -2
    level = 5

