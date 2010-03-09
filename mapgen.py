from random import randrange
from sys import stdout

import libtcodpy as T

from settings import *
from map import *
from util import *

TILE_TABLE = {
    '.': FloorTile,
    '#': WoodWallTile,
    ' ': WallTile,
    '>': StairDownTile,
    '<': StairUpTile,
}

def array_to_tiles(arr):
    return [[TILE_TABLE[c]() for c in line] for line in arr]

def try_put_room(arr, w, h):
    x1, y1 = randrange(MAP_W-w-2), randrange(MAP_H-h-2)
    for x in range(x1, x1+w):
        for y in range(y1, y1+h):
            if arr[x][y] != ' ':
                return None
    for x in range(x1, x1+w):
        for y in range(y1, y1+h):
            arr[x][y] = '.'
    for x in range(x1, x1+w):
        arr[x][y1] = '#'
        arr[x][y1+h-1] = '#'
    for y in range(y1, y1+h):
        arr[x1][y] = '#'
        arr[x1+w-1][y] = '#'
    return (x1, y1, w, h)

def print_array(arr):
    for y in range(len(arr[0])):
        for line in arr:
            stdout.write(line[y])
        stdout.write('\n')

def corridor_path_func(x1, y1, x2, y2, arr):
    if x2 == 0 or x2 == MAP_W-1 or y2 == 0 or y2 == MAP_H-1:
        return 0
    c = arr[x2][y2]
    if c == ' ':
        return 5
    elif c == '#':
        return 40
    else:
        return 1

def generate_map():
    arr = array(MAP_W, MAP_H, lambda: ' ')
    rooms = []
    for i in xrange(500):
        w, h = randrange(5,15), randrange(5,10)
        room = try_put_room(arr, w, h)
        if room:
            rooms.append(room)

    #randomly_place(arr, '<')
    randomly_place(arr, '>')

    path = T.path_new_using_function(
        MAP_W, MAP_H, corridor_path_func, arr, 0.0)

    def connect(x1, y1, x2, y2):
        T.path_compute(path, x1, y1, x2, y2)
        for i in range(T.path_size(path)):
            x, y = T.path_get(path, i)
            c = arr[x][y]
            if c == '#' or c == ' ':
                arr[x][y] = '.'

    for i in range(len(rooms)-1):
        x1, y1, w1, h1 = rooms[i]
        x2, y2, w2, h2 = rooms[i+1]
        connect(x1+w1/2, y1+h1/2, x2+w2/2, y2+h2/2)

    #print_array(arr)

    return array_to_tiles(arr)

def randomly_place(arr, c):
    x, y = random_empty_space(arr)
    arr[x][y] = c

def random_empty_space(arr):
    while True:
        x, y = randrange(MAP_W), randrange(MAP_H)
        if arr[x][y] == '.':
            return (x, y)
