import os
from pygame import image

from scripts.tilemap import TileMap


IMG_PATH = 'data/images/'
MAP_PATH = 'data/maps/'
SFX_PATH = 'data/sfx/'


def load_image(path):
    img = image.load(IMG_PATH + path).convert()
    img.set_colorkey((0, 0, 0))
    return img

def load_images(path):
    imgs = []
    for img_name in sorted(os.listdir(IMG_PATH + path)):
        imgs.append(load_image(path + "/" + img_name))
    return imgs

def load_map(game, path):
    tilemap = TileMap(game)
    tilemap.load(MAP_PATH + '/' + path)
    return tilemap

def load_maps(game):
    maps = []
    for map_name in sorted(os.listdir(MAP_PATH)):
        maps.append(load_map(game, map_name))
    return maps


class Animation:
    def __init__(self, images, img_duration=5, loop=True):
        self.images       = images
        self.img_duration = img_duration
        self.loop         = loop
        self.done         = False
        self.frame        = 0

    def copy(self):
        return Animation(self.images, self.img_duration, self.loop)
    
    def img(self):
        return self.images[int(self.frame / self.img_duration)]
    
    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True