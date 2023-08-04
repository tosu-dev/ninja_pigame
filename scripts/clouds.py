from random import random, choice

class Cloud:
    def __init__(self, img, pos, speed, depth):
        self.img   = img
        self.speed = speed
        self.pos   = list(pos)
        self.depth = depth

    def update(self):
        self.pos[0] += self.speed

    def render(self, surf, offset=[0, 0]):
        render_pos = (self.pos[0] - offset[0] * self.depth, self.pos[1] - offset[1] * self.depth)
        surf.blit(self.img, (render_pos[0] % (surf.get_width() + self.img.get_width()) - self.img.get_width(), render_pos[1] % (surf.get_height() + self.img.get_height()) - self.img.get_height()))

class Clouds:
    def __init__(self, images, count=16):
        self.clouds = []
        for _ in range(count):
            self.clouds.append(Cloud(choice(images), (random()*99999, random()*99999), random()*0.05+0.05, random()*0.6+0.2))
        self.clouds.sort(key=lambda cloud: cloud.depth)

    def update(self):
        for cloud in self.clouds:
            cloud.update()

    def render(self, surf, offset=[0, 0]):
        for cloud in self.clouds:
            cloud.render(surf, offset)