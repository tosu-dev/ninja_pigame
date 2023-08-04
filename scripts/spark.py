from math import sin, cos, pi
from pygame import draw

class Spark:
    def __init__(self, pos, angle, speed, color=(255, 255, 255)):
        self.pos = list(pos)
        self.angle = angle
        self.speed = speed
        self.color = color
    
    def update(self):
        self.pos[0] += cos(self.angle) * self.speed
        self.pos[1] += sin(self.angle) * self.speed

        self.speed = max(0, self.speed - 0.1)

        return not self.speed
    
    def render(self, surf, offset=[0, 0]):
        render_points = [
            (self.pos[0] + cos(self.angle) * self.speed * 3 - offset[0], self.pos[1] + sin(self.angle) * self.speed * 3 - offset[1]),
            (self.pos[0] + cos(self.angle + pi * 0.5) * self.speed * 0.5 - offset[0], self.pos[1] + sin(self.angle + pi * 0.5) * self.speed * 0.5 - offset[1]),
            (self.pos[0] + cos(self.angle + pi) * self.speed * 0.5 - offset[0], self.pos[1] + sin(self.angle + pi) * self.speed * 0.5 - offset[1]),
            (self.pos[0] + cos(self.angle - pi * 0.5) * self.speed * 0.5 - offset[0], self.pos[1] + sin(self.angle - pi * 0.5) * self.speed * 0.5 - offset[1]),
        ]

        draw.polygon(surf, self.color, render_points)