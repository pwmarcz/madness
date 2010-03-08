from random import randrange, choice

ALL_DIRS = []
for dx in range(-1,2):
    for dy in range(-1,2):
        if (dx, dy) != (0, 0):
            ALL_DIRS.append((dx, dy))

def distance(x1, y1, x2, y2):
    dx = abs(x2-x1)
    dy = abs(y2-y1)
    return (dx+dy+max(dx,dy))/2

def sgn(a):
    if a < 0:
        return -1
    elif a == 0:
        return 0
    else:
        return 1

def dir_towards(x1, y1, x2, y2):
    return sgn(x2-x1), sgn(y2-y1)

# Roll AdB+C
def roll(a, b, c=0):
    return sum(randrange(1,b+1) for i in range(a))+c

def describe_dice(a, b, c):
    if c == 0:
        return '%dd%d' % (a, b)
    else:
        return '%dd%d+%d' % (a, b, c)

def random_by_level(level, items):
    items = filter(lambda a: a.level <= level, items)
    return choice(items)

def array(w, h, func):
    def line():
        return [func() for y in range(h)]
    return [line() for x in range(w)]

class Register(type):
    def __new__(mcs, name, bases, dict):
        cls = type.__new__(mcs, name, bases, dict)
        if not dict.get('ABSTRACT'):
            cls.ALL.append(cls)
        return cls
