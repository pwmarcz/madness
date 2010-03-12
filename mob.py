from random import choice, random, shuffle
from math import log

import libtcodpy as T

from settings import *
from util import *
from item import Item
import ui

class Mob(object):
    x, y = None, None
    glyph = UNKNOWN_GLYPH
    map = None

    enters_walls = False
    sanity_dice = None
    real = True

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
        if not in_map(destx, desty):
            return False
        tile = self.map.tiles[destx][desty]
        return (tile.walkable or self.enters_walls) and \
            not tile.mob

    def walk(self, dx, dy):
        self.move(self.x+dx, self.y+dy)

    def is_besides(self, mob):
        return max(abs(self.x-mob.x),abs(self.y-mob.y)) == 1

    # Called every time a mob has an opportunity to act (depending on speed)
    def act(self):
        if self.hp < self.max_hp:
            self.to_regen += self.regen
            if self.to_regen > 10:
                self.hp = min(self.max_hp, self.to_regen/10+self.hp)
                self.to_regen %= 10

    # Called every turn
    def heartbeat(self):
        pass

class Player(Mob):
    glyph = '@', T.white
    regen = 4
    name = 'you'

    def __init__(self, wizard):
        super(Player, self).__init__()
        self.level = 1
        self.sanity = MAX_SANITY
        # dict letter -> effect
        self.effects = {}
        self.max_hp = 28
        self.speed = 0
        self.hp = self.max_hp

        import item
        self.items = [item.Torch(), item.PotionSanity()]
        if wizard:
            self.items += [item.Torch(), item.EterniumSword()]

        self.equipment = dict((slot, None) for slot in INVENTORY_SLOTS)
        self.fov_range = 3
        self.light_range = 0
        self.action_turns = 1
        self.armor = 0
        self.exp = 0
        self.death = None
        self.won = False

    @property
    def dice(self):
        weapon = self.equipment['w']
        if weapon:
            a, b, c = weapon.dice
        else:
            a, b, c = 1, 3, 0
        c += self.level-1
        return a, b, c

    def add_exp(self, mob):
        self.exp += int(1.7 ** mob.level)
        new_level = min(int(log(self.exp/5+2, 2)), MAX_CLEVEL)
        while new_level > self.level:
            self.advance()

    def advance(self):
        self.level += 1
        hp_inc = roll(2,6,self.level)
        self.max_hp += hp_inc
        self.hp += hp_inc
        ui.message('Congratulations! You advance to level %d.' % self.level,
                   T.yellow)

    def change_light_range(self, n):
        self.light_range += n
        self.fov_range += n
        self.map.recalc_fov()

    def has_equipped(self, item):
        return item.slot and self.equipment[item.slot] == item

    def put(self, m, x, y):
        super(Player, self).put(m, x, y)
        self.map.player = self
        self.map.recalc_fov()

    def move(self, x, y):
        super(Player, self).move(x, y)
        self.map.recalc_fov()
        self.tile.on_enter()
        if self.tile.items:
            if len(self.tile.items) == 1:
                ui.message('You see here %s.' % self.tile.items[0].a)
            else:
                ui.message('Several items are lying here.')
        self.use_energy()

    def walk(self, dx, dy, panic=True):
        destx, desty = self.x+dx, self.y+dy
        if not in_map(destx, desty):
            return False
        tile = self.map.tiles[destx][desty]
        if panic and 'f' in self.effects:
            neighbors = self.map.neighbor_tiles(self.x, self.y)
            n_monsters = sum(1 if tile.mob else 0 for tile in neighbors)
            if roll(1, 8) <= min(5, n_monsters):
                ui.message('You panic!', T.yellow)
                dx, dy = choice(ALL_DIRS)
                self.walk(dx, dy, False)
                return
        if tile.mob:
            self.attack(tile.mob)
        elif not tile.walkable:
            ui.message('You bump into a wall.')
            pass
        else:
            self.move(destx, desty)

    def use(self, item):
        if item.slot is None:
            item.on_use(self)
            self.use_energy()
        elif self.has_equipped(item):
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
            ui.message('You critically hit the %s!' % mon.name, T.yellow)
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
                self.death = 'killed by %s%s' % (
                    ('imaginary ' if not mon.real else ''),
                    mon.name)

    def pick_up(self, item):
        if len(self.items) == INVENTORY_SIZE:
            ui.message('You can\'t carry anymore items.', T.red)
            return
        assert item in self.tile.items
        self.tile.items.remove(item)
        self.items.append(item)
        ui.message('You pick up the %s.' % item.descr)
        self.use_energy()

    def drop(self, item):
        if self.has_equipped(item):
            self.unequip(item)
        self.items.remove(item)
        self.tile.items.append(item)
        ui.message('You drop the %s.' % item.descr)
        self.use_energy()

    def act(self):
        if not self.death:
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
        if roll(1, 7) == 1:
            self.decrease_sanity(roll(1, max(1, self.map.level/2-3)))

    def decrease_sanity(self, n):
        from effect import add_insane_effects
        self.sanity -= n
        if self.sanity <= 0:
            ui.message('You feel reality slipping away...')
            self.death = 'insane'
        else:
            add_insane_effects(self)
            for eff in self.effects.values():
                if roll(1, 80) > self.sanity:
                    severity = roll(1, (8-self.sanity/10))
                    eff.do_effect(severity)

    def restore_sanity(self):
        self.sanity = MAX_SANITY
        ui.message('You feel more awake.', T.yellow)
        for eff in self.effects.values():
            eff.remove()

    def resurrect(self):
        self.death = None
        if self.hp <= 0:
            self.hp = self.max_hp
        if self.sanity <= 0:
            self.restore_sanity()

class Monster(Mob):
    ALL = []
    __metaclass__ = Register
    ABSTRACT = True
    real = True
    multi = 1
    common = 10

    summoner = False
    fov_range = 5
    # n/30 is probability of item drop
    drop_rate = 2
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
        if not (self.real or ('r' in self.map.player.effects)):
            self.disappear()
            return
        dmg -= self.armor
        if dmg < 0:
            ui.message('The %s shrugs off the hit.' % self.name)
            return
        self.hp -= dmg
        if self.hp <= 0:
            if roll(1, 30) <= self.drop_rate:
                item = random_by_level(self.map.level, Item.ALL)()
                self.tile.items.append(item)
            self.die()
        else:
            ui.message('The %s is %s.' % (self.name, self.get_wounds()))

    def die(self):
        self.look_normal()
        if self.map.is_visible(self.x, self.y):
            ui.message('The %s dies!' % self.name)
        self.remove()
        self.map.player.add_exp(self)

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
        if T.map_is_in_fov(self.map.fov_map, self.x, self.y):
            d = distance(self.x, self.y, player.x, player.y)
            if d <= fov_range:
                return d
        return None

    def walk_randomly(self):
        dirs = filter(lambda (dx, dy): self.can_walk(dx, dy),
                      ALL_DIRS)
        if dirs != []:
            self.walk(*choice(dirs))

    def summon_monsters(self):
        if self.map.is_visible(self.x, self.y):
            ui.message('The %s summons monsters!' % self.name)
        else:
            ui.message('You hear arcane mumbling.')
        n = roll(2, 3)
        mcls = random_by_level(self.map.level, Monster.ALL)
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        shuffle(dirs)
        for dx, dy in dirs:
            n = self.map.flood(self.x+dx, self.y+dy, mcls, n)

    def act(self):
        player = self.map.player
        d = self.see_player()
        if d:
            if self.summoner and roll(1, 6) == 1:
                self.summon_monsters()
                return
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

    def attack_player(self):
        player = self.map.player
        dmg = roll(*self.dice)
        if roll(1, 20) < 20:
            ui.message('The %s hits you.' % self.name)
        else:
            ui.message('The %s critically hits you!' % self.name, T.yellow)
            dmg *= 2
        if self.real or ('r' in player.effects):
            player.damage(dmg, self)
        if self.sanity_dice and not player.death:
            d = roll(*self.sanity_dice)
            ui.message('You have trouble thinking straight!', T.yellow)
            player.decrease_sanity(d)

class UnrealMonster(Monster):
    ABSTRACT = True
    real = False
    drop_rate = 0

class HappyMonster(UnrealMonster):
    ABSTRACT = True
    ALL = []

class DarkMonster(UnrealMonster):
    ABSTRACT = True
    ALL = []
    fears_light = True
    enters_walls = True

##### MONSTERS

class Rat(Monster):
    name = 'rat'
    glyph = 'r', T.dark_orange
    max_hp = 4
    dice = 1, 3, 0
    drop_rate = 1
    multi = 4
    level = 1

class Bat(Monster):
    name = 'bat'
    glyph = 'B', T.dark_orange
    max_hp = 5
    speed = 2
    dice = 1, 3, 0
    fears_light = True
    level = 1

class Goblin(Monster):
    name = 'goblin'
    glyph = 'g', T.light_blue
    max_hp = 3
    dice = 1, 6, 1
    armor = 2
    level = 2

class Orc(Monster):
    name = 'orc'
    glyph = 'o', T.red
    max_hp = 6
    dice = 1, 6, 2
    armor = 4
    level = 3

class MadAdventurer(Monster):
    name = 'mad adventurer'
    glyph = '@', T.violet
    max_hp = 15
    dice = 1, 10, 1
    armor = 5
    drop_rate = 18
    common = 5
    level = 4

class Ogre(Monster):
    name = 'ogre'
    glyph = 'O', T.dark_green
    max_hp = 18
    speed = -2
    dice = 1, 8, 4
    armor = 4
    level = 4

class KillerBat(Monster):
    name = 'killer bat'
    glyph = 'B', T.orange
    max_hp = 8
    speed = 2
    dice = 2, 8, 0
    fears_light = True
    multi = 5
    armor = 4
    level = 4

class Dragon(Monster):
    name = 'dragon'
    glyph = rainbow_glyph('D')
    max_hp = 20
    speed = -1
    dice = 2, 8, 2
    drop_rate = 30
    armor = 7
    level = 5

class Giant(Monster):
    name = 'giant'
    glyph = 'H', T.light_grey
    max_hp = 20
    speed = -2
    dice = 3, 6, 0
    armor = 6
    level = 5

class Boss(Monster):
    ABSTRACT = True # suppress random generation
    name = 'Dungeon Master'
    glyph = '@', T.grey
    max_hp = 30
    dice = 3, 3, 4
    sanity_dice = 1, 8, 0
    armor = 5
    summoner = True
    level = 6

    def die(self):
        super(Boss, self).die()
        self.map.player.won = True

##### HAPPY (UNREAL) MONSTERS

class Butterfly(HappyMonster):
    name = 'butterfly'
    glyph = rainbow_glyph('b')
    max_hp = 2
    speed = 3
    dice = 1, 3, 0
    armor = 2
    multi = 4
    level = 1

class LittlePony(HappyMonster):
    name = 'little pony'
    glyph = rainbow_glyph('u')
    max_hp = 7
    dice = 1, 6, 3
    multi = 3
    level = 3

class PinkUnicorn(HappyMonster):
    name = 'pink unicorn'
    glyph = 'U', T.pink
    max_hp = 10
    dice = 1, 8, 4
    level = 4

class RobotUnicorn(HappyMonster):
    name = 'robot unicorn'
    glyph = rainbow_glyph('U', remember=False)
    max_hp = 10
    dice = 1, 8, 6
    level = 4

class FSM(HappyMonster):
    name = 'flying spaghetti monster'
    glyph = 'S', T.yellow
    max_hp = 15
    dice = 2, 6, 0
    sanity_dice = 2, 4, 0
    level = 5

##### DARK (UNREAL) MONSTERS

class GhostBat(DarkMonster):
    name = 'ghost bat'
    glyph = 'B', T.white
    max_hp = 3
    speed = 2
    dice = 1, 4, 0
    multi = 3
    level = 1

class Ghost(DarkMonster):
    name = 'ghost'
    glyph = '@', T.white
    max_hp = 6
    dice = 1, 6, 0
    level = 2

class Phantom(DarkMonster):
    name = 'phantom'
    glyph = '@', T.grey
    max_hp = 6
    dice = 1, 8, 0
    sanity_dice = 1, 4, 0
    enters_walls = True
    multi = 3
    level = 3

class Grue(DarkMonster):
    name = 'grue'
    glyph = 'G', T.grey
    max_hp = 20
    dice = 1, 10, 0
    sanity_dice = 1, 6, 0
    level = 4

class Horror(DarkMonster):
    name = 'grue'
    glyph = '&', T.grey
    max_hp = 20
    dice = 1, 8, 0
    sanity_dice = 1, 8, 0
    level = 5
