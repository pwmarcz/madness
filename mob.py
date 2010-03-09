from random import choice, random
from math import log

import libtcodpy as libtcod

from settings import *
from util import *
from item import *
import ui

class Mob(object):
    x, y = None, None
    glyph = UNKNOWN_GLYPH
    map = None

    # -4 = rests every other turn
    # -1 = rests every 5th turn
    # +1 = extra move every 5th turn
    # +4 = extra move every other turn
    speed = 0

    # N = regens N/10 health points every turn
    regen = 1

    # damage reduction
    armor = 0

    def __init__(self):
        self.to_regen = 0

    @property
    def tile(self):
        return self.map.tiles[self.x][self.y]

    def put(self, m, x, y):
        tile = m.tiles[x][y]
        self.map = m
        self.x, self.y = x, y
        assert self.tile.mob is None
        self.tile.mob = self
        m.mobs.append(self)

    def remove(self):
        self.tile.mob = None
        self.map.mobs.remove(self)

    def move(self, x, y):
        self.tile.mob = None
        self.x, self.y = x, y
        assert self.tile.mob is None
        self.tile.mob = self

    def can_walk(self, dx, dy):
        destx, desty = self.x+dx, self.y+dy
        tile = self.map.tiles[destx][desty]
        return tile.walkable and not tile.mob

    def walk(self, dx, dy):
        self.move(self.x+dx, self.y+dy)

    def is_besides(self, mob):
        return max(abs(self.x-mob.x),abs(self.y-mob.y)) == 1

    # Called every time a mob has an opportunity to act (depending on speed)
    def act(self):
        self.to_regen += self.regen
        if self.to_regen > 10:
            self.hp = min(self.max_hp, self.to_regen/10+self.hp)
            self.to_regen %= 10

    # Called every turn
    def heartbeat(self):
        pass

class Player(Mob):
    glyph = '@', libtcod.white
    regen = 4

    def __init__(self):
        super(Player, self).__init__()
        self.level = 1
        self.sanity = MAX_SANITY
        self.max_hp = 15
        self.hp = self.max_hp
        self.items = [Torch(), SwordHax()]
        self.equipment = dict((slot, None) for slot in SLOTS)
        self.fov_range = 3
        self.light_range = 0
        self.action_turns = 1
        self.armor = 0
        self.exp = 0
        self.death = None

    @property
    def dice(self):
        weapon = self.equipment['w']
        if weapon:
            a, b, c = weapon.dice
        else:
            a, b, c = 1, 3, 0
        c += self.level
        return a, b, c

    def add_exp(self, mob):
        self.exp += int(1.7 ** mob.level)
        print self.exp
        new_level = min(int(log(self.exp/3+2, 2)), MAX_CLEVEL)
        while new_level > self.level:
            self.advance()

    def advance(self):
        self.level += 1
        hp_inc = roll(1,6,2*self.level)
        self.max_hp += hp_inc
        self.hp += hp_inc
        ui.message('Congratulations! You advance to level %d.' % self.level)

    def change_light_range(self, n):
        self.light_range += n
        self.fov_range += n
        self.map.recalc_fov()

    def is_equipped(self, item):
        return item.slot and self.equipment[item.slot] == item

    def put(self, m, x, y):
        super(Player, self).put(m, x, y)
        self.map.player = self
        self.map.recalc_fov()

    def move(self, x, y):
        super(Player, self).move(x, y)
        self.map.recalc_fov()
        self.tile.describe()
        self.use_energy()

    def use(self, item):
        if item.slot is None:
            ui.message('You don\'t know how to use the %s.' % item.descr)
        elif self.is_equipped(item):
            self.unequip(item)
        else:
            self.equip(item)

    def unequip(self, item):
        ui.message('You unequip the %s.' % item.descr)
        item.on_unequip(self)
        self.equipment[item.slot] = None
        self.use_energy()

    def equip(self, item):
        old_item = self.equipment[item.slot]
        if old_item:
            self.unequip(old_item)
        ui.message('You equip the %s.' % item.descr)
        item.on_equip(self)
        self.equipment[item.slot] = item
        self.use_energy()

    def attack(self, mon):
        dmg = roll(*self.dice)
        if roll(1, 20) < 20:
            ui.message('You hit the %s.' % mon.name)
        else:
            ui.message('You critically hit the %s!' % mon.name)
            dmg *= 2
        mon.damage(dmg)
        self.use_energy()

    def damage(self, dmg, mon):
        dmg -= self.armor
        if dmg < 0:
            ui.message('Your armor protects you.')
            return
        self.hp -= dmg
        if self.hp <= 0:
            if not self.death:
                ui.message('You die...')
                # everything has to look normal?
                mon.look_normal()
                self.death = 'killed by a %s' % mon.name

    def pick_up(self, item):
        if len(self.items) == INVENTORY_SIZE:
            ui.message('You can\'t carry anymore items.')
            return
        assert item in self.tile.items
        self.tile.items.remove(item)
        self.items.append(item)
        ui.message('You pick up the %s.' % item.descr)
        self.use_energy()

    def drop(self, item):
        if self.is_equipped(item):
            self.unequip(item)
        self.items.remove(item)
        self.tile.items.append(item)
        ui.message('You drop the %s.' % item.descr)
        self.use_energy()

    def act(self):
        super(Player, self).act()
        self.action_turns += 1

    def use_energy(self):
        self.action_turns -= 1

    def wait(self):
        self.use_energy()

    def extinguish(self, light):
        ui.message('Your %s is extinguished!' % light.descr)
        light.on_unequip(self)
        self.equipment['l'] = None
        self.items.remove(light)

    def heartbeat(self):
        super(Player, self).heartbeat()
        light = self.equipment['l']
        if light:
            light.turns_left -= 1
            if light.turns_left <= 0:
                self.extinguish(light)
        if roll(1, 5) == 1:
            self.decrease_sanity(roll(1, 2+self.map.level))

    def decrease_sanity(self, n):
        self.sanity -= n
        if self.sanity <= 0:
            ui.message('Your mind is gone!')
            self.death = 'went insane'
        else:
            if roll(1, 130) > self.sanity:
                severity = roll(1, (10-self.sanity/10))
                self.map.insane_effect(severity)

    def resurrect(self):
        self.death = None
        if self.hp <= 0:
            self.hp = self.max_hp
        if self.sanity <= 0:
            self.sanity = 100

    def is_affected_by_unreal(self):
        return self.sanity <= 20

class Monster(Mob):
    ALL = []
    __metaclass__ = Register
    ABSTRACT = True
    real = True

    fov_range = 12
    # n/20 is probability of item drop
    drop_rate = 1
    fears_light = False

    def __init__(self):
        super(Monster, self).__init__()
        self.hp = self.max_hp
        #self.real = real

    def look_like(self, cls):
        self.name = cls.name
        self.glyph = cls.glyph

    def look_normal(self):
        try:
            del self.name
            del self.glyph
        except AttributeError:
            pass

    def disappear(self):
        ui.message('The %s disappears!' % self.name)
        self.remove()

    def damage(self, dmg):
        if not (self.real or self.map.player.is_affected_by_unreal()):
            self.disappear()
            return
        dmg -= self.armor
        if dmg < 0:
            ui.message('The %s shrugs off the hit.' % self.name)
            return
        self.hp -= dmg
        if self.hp <= 0:
            if roll(1, 20) <= self.drop_rate:
                item = random_by_level(self.level, Item.ALL)()
                self.tile.items.append(item)
            self.look_normal()
            ui.message('The %s dies!' % self.name)
            self.remove()
            self.map.player.add_exp(self)
        else:
            ui.message('The %s is %s.' % (self.name, self.get_wounds()))

    def get_wounds(self):
        p = 100*self.hp/self.max_hp
        if p < 10:
            return 'almost dead'
        elif p < 30:
            return 'severely wounded'
        elif p < 70:
            return 'moderately wounded'
        else:
            return 'lightly wounded'

    # return distance if monster can see player, None if not
    def see_player(self):
        player = self.map.player
        fov_range = self.fov_range + player.light_range/2
        if libtcod.map_is_in_fov(
            self.map.fov_map, self.x, self.y):
            d = distance(self.x, self.y, player.x, player.y)
            if d <= fov_range:
                return d
        return None

    def walk_randomly(self):
        dirs = filter(lambda (dx, dy): self.can_walk(dx, dy),
                      ALL_DIRS)
        if dirs != []:
            self.walk(*choice(dirs))

    def act(self):
        player = self.map.player
        d = self.see_player()
        if d:
            dx, dy = dir_towards(self.x, self.y,
                                 player.x, player.y)
            if player.light_range > 0 and self.fears_light:
                if self.can_walk(-dx, -dy):
                    self.walk(-dx, -dy)
                elif player.is_besides(self):
                    self.attack_player()
                else:
                    self.walk_randomly()
            else:
                if player.is_besides(self):
                    self.attack_player()
                elif self.can_walk(dx, dy):
                    self.walk(dx, dy)
                else:
                    self.walk_randomly()
        else:
            self.walk_randomly()

        dirs = filter(lambda (dx, dy): self.can_walk(dx, dy),
                      ALL_DIRS)

    def attack_player(self):
        player = self.map.player
        dmg = roll(*self.dice)
        if roll(1, 20) < 20:
            ui.message('The %s hits you.' % self.name)
        else:
            ui.message('The %s critically hits you!' % self.name)
            dmg *= 2
        if self.real or player.is_affected_by_unreal():
            player.damage(dmg, self)

class UnrealMonster(Monster):
    ALL = []
    ABSTRACT = True
    real = False

##### MONSTERS

class Bat(Monster):
    name = 'bat'
    glyph = 'B', libtcod.dark_orange
    max_hp = 3
    speed = 2
    dice = 1, 3, 0
    fears_light = True
    level = 1

class Goblin(Monster):
    name = 'goblin'
    glyph = 'g', libtcod.light_blue
    max_hp = 5
    dice = 1, 6, 0
    armor = 3
    level = 2

class Giant(Monster):
    name = 'giant'
    glyph = 'H', libtcod.light_grey
    max_hp = 20
    dice = 5, 4, 0
    fov_range = 6
    speed = -2
    armor = 10
    level = 10

class Orc(Monster):
    name = 'orc'
    glyph = 'o', libtcod.red
    max_hp = 10
    dice = 1, 6, 0
    armor = 6
    level = 4

class Orc(Monster):
    name = 'orc'
    glyph = 'o', libtcod.red
    max_hp = 10
    dice = 1, 6, 0
    armor = 6
    level = 4

##### UNREAL MONSTERS

class Pony(UnrealMonster):
    name = 'pony'
    glyph = 'u', libtcod.white
    max_hp = 10
    dice = 1, 8, 0
    armor = 2
    level = 3

class Unicorn(UnrealMonster):
    name = 'unicorn'
    glyph = 'U', libtcod.white
    max_hp = 20
    dice = 1, 10, 0
    level = 5

class Wookiee(UnrealMonster):
    name = 'Wookiee'
    glyph = 'W', libtcod.dark_orange
    max_hp = 7
    dice = 1, 7, 2
    level = 3
