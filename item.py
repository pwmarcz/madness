import libtcodpy as T

from settings import *
from util import *
from random import choice
import ui

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

    def on_use(self, player):
        ui.message('You don\'t know how to use %s.' % self.descr)

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

class Potion(Item):
    ABSTRACT = True

    def on_use(self, player):
        ui.message('You drink the %s.' % self.name)
        player.items.remove(self)

##### LIGHT SOURCES

class Torch(LightSource):
    name = 'torch'
    glyph = '/', T.dark_orange
    level = 1
    turns = 250
    light_range = 6

class Lamp(LightSource):
    name = 'lamp'
    glyph = ']', T.yellow
    level = 3
    turns = 350
    light_range = 10

###### WEAPONS

class Dagger(Weapon):
    name = 'dagger'
    glyph = '(', T.light_grey
    dice = 1, 4, 0
    level = 1

class Stick(Weapon):
    name = 'stick'
    glyph = '(', T.dark_orange
    dice = 1, 3, 1
    level = 1

class ShortSword(Weapon):
    name = 'short sword'
    glyph = '(', T.light_grey
    dice = 1, 6, 0
    level = 2

class HandAxe(Weapon):
    name = 'hand axe'
    glyph = '(', T.grey
    dice = 1, 6, 1
    level = 2

class Spear(Weapon):
    name = 'spear'
    glyph = '(', T.light_sky
    dice = 1, 8, 2
    level = 3

class LongSword(Weapon):
    name = 'long sword'
    glyph = '(', T.cyan
    dice = 1, 10, 0
    level = 3

class TwoSword(Weapon):
    name = 'two-handed sword'
    glyph = '(', T.light_grey
    dice = 2, 8, 0
    speed = -1
    level = 4

class Halberd(Weapon):
    name = 'halberd'
    glyph = '(', T.light_grey
    dice = 3, 6, 0
    speed = -1
    level = 4

class EterniumSword(Weapon):
    name = 'eternium sword'
    glyph = '(', T.white
    dice = 4, 6, 0
    level = 5

##### BOOTS

class LightBoots(Boots):
    name = 'light boots'
    slot = 'b'
    glyph = '[', T.dark_orange
    armor = 1
    level = 2

class HeavyBoots(Boots):
    name = 'heavy boots'
    glyph = '[', T.light_grey
    armor = 2
    speed = -1
    level = 3

class BootsSpeed(Boots):
    name = 'boots of speed'
    glyph = '[', T.light_blue
    speed = 3
    level = 5

##### ARMOR

class UglyClothes(Armor):
    name = 'ugly clothes'
    plural = True
    glyph = '[', T.green
    armor = 1
    level = 1

class RingMail(Armor):
    name = 'ring mail'
    glyph = '[', T.grey
    armor = 4
    speed = -1
    level = 3

class PlateMail(Armor):
    name = 'plate mail'
    glyph = '[', T.white
    armor = 6
    speed = -2
    level = 5

##### POTIONS

class PotionSanity(Potion):
    glyph = '!', T.blue
    name = 'potion of sanity'
    level = 3

    def on_use(self, player):
        super(PotionSanity, self).on_use(player)
        player.restore_sanity(50)
        player.map.clear_insane_effects()

class PotionHealing(Potion):
    glyph = '!', T.green
    name = 'potion of health'
    level = 2

    def on_use(self, player):
        super(PotionHealing, self).on_use(player)
        ui.message('You feel healed.')
        player.hp = player.max_hp
