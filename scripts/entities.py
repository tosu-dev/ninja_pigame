from pygame import transform, Rect, mask
from math import sin, cos, pi
from random import random, randint

from scripts.particle import Particle
from scripts.spark import Spark

class PhysicsEntity:
    def __init__(self, game, e_type, pos, size, outline=None):
        self.game        = game
        self.type        = e_type
        self.pos         = list(pos)
        self.size        = size
        self.velocity    = [0, 0]
        self.collisions  = {'top': False, 'bottom': False, 'left': False, 'right': False}
        self.action      = ''
        self.anim_offset = (-3, -3)
        self.flip        = False
        self.set_action('idle')
        self.outline = outline

    def rect(self):
        return Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def set_action(self, action: str):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()

    def update(self, tilemap, movement=(0, 0)):
        self.collisions = {'top': False, 'bottom': False, 'left': False, 'right': False}
        frame_movement = (movement[0]+self.velocity[0], movement[1]+self.velocity[1])

        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                elif frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x

        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['bottom'] = True
                elif frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['top'] = True
                self.pos[1] = entity_rect.y

        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True

        self.velocity[1] = min(3, self.velocity[1] + 0.1)

        if self.collisions['top'] or self.collisions['bottom']:
            self.velocity[1] = 0

        self.animation.update()

    def render(self, surf, offset=[0, 0]):
        pos = (self.pos[0]-offset[0]+self.anim_offset[0], self.pos[1]-offset[1]+self.anim_offset[1])
        if self.outline:
            entity_mask = mask.from_surface(transform.flip(self.animation.img(), self.flip, False))
            entity_silouhette = entity_mask.to_surface(setcolor=self.outline, unsetcolor=(0, 0, 0, 0))
            for mask_offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                surf.blit(entity_silouhette, (pos[0]-mask_offset[0], pos[1]-mask_offset[1]))
        surf.blit(transform.flip(self.animation.img(), self.flip, False), pos)


class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size, outline=(0, 0, 0, 180))
        self.walking: int = 0
        
    def update(self, tilemap, movement=(0, 0)):
        kill = False

        if self.walking:
            if (tilemap.solid_check((self.pos[0] + (-tilemap.tile_size if self.flip else tilemap.tile_size), self.pos[1] + tilemap.tile_size))
                and not(self.collisions['left'] or self.collisions['right'])):
                movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
                self.walking = max(0, self.walking - 1)
            else:
                self.flip = not self.flip
            if not (self.walking):
                distance = (self.game.player.pos[0]-self.pos[0], self.game.player.pos[1]-self.pos[1])
                if abs(distance[1]) < 16 and abs(distance[0]) < 120:
                    self.game.play_sfx('shoot')
                    if self.flip and distance[0] < 0:
                        self.game.projectiles.append([[self.pos[0]-4, self.pos[1]+5], -1.2, 0])
                        for _ in range(8):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random()-0.5+pi, 2+random()))
                    if not self.flip and distance[0] > 0:
                        self.game.projectiles.append([[self.pos[0]+7, self.pos[1]+5], 1.2, 0])
                        for _ in range(8):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random()-0.5, 2+random()))

        elif random() < 0.05:
            self.walking = randint(30, 120)
            if random() < 0.5:
                self.flip = not self.flip

        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')

        if abs(self.game.player.dashing) >= self.game.player.dashing_cooldown-10:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.play_sfx('hit')
                for _ in range(20):
                    self.game.sparks.append(Spark(self.pos, random()*pi*2, 2+random()))
                self.game.sparks.append(Spark(self.pos, 0, 5))
                self.game.sparks.append(Spark(self.pos, pi, 5))
                self.game.sparks.append(Spark(self.pos, pi*0.5, 5))
                self.game.sparks.append(Spark(self.pos, -pi*0.5, 5))
                kill = True
                self.game.screenshake = max(20, self.game.screenshake)

        super().update(tilemap, movement)

        return kill

    def render(self, surf, offset=[0, 0]):
        super().render(surf, offset=offset)
        if self.flip:
            surf.blit(transform.flip(self.game.assets['gun'], True, False), (self.pos[0]-offset[0]-4, self.pos[1]-offset[1]+5))
        else:
            surf.blit(self.game.assets['gun'], (self.pos[0]-offset[0]+7, self.pos[1]-offset[1]+5))

  
class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size, outline=(0, 0, 0, 180))
        self.air_time   = 0
        self.jumps      = 1
        self.max_jumps  = 1
        self.wall_slide = False
        self.dashing    = 0
        self.dashing_cooldown = 90

    def jump(self):
        if self.wall_slide :
            self.game.play_sfx('jump')
            if self.collisions['left']:
                self.velocity[0] = 3.5
                self.velocity[1] = -2.5
                self.air_time = 8
                self.jumps = max(0, self.jumps-1)
            elif self.collisions['right']:
                self.velocity[0] = -3.5
                self.velocity[1] = -2.5
                self.air_time = 8
                self.jumps = max(0, self.jumps-1)
        elif self.jumps > 0 and self.air_time < 8:
            self.game.play_sfx('jump')
            self.velocity[1] = -3
            self.jumps -= 1
            self.air_time = 8

    def dash(self):
        if not self.dashing:
            self.game.play_sfx('dash')
            if self.flip:
                self.dashing = -self.dashing_cooldown
            else:
                self.dashing = self.dashing_cooldown

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement)

        if abs(self.dashing) < self.dashing_cooldown-10: 
            self.air_time += 1

        if self.air_time > 180:
            self.game.screenshake = max(20, self.game.screenshake)
            self.game.dead = 1

        if self.collisions['bottom']:
            self.air_time = 0
            self.jumps = self.max_jumps

        if abs(self.dashing) in {self.dashing_cooldown, self.dashing_cooldown-10}:
            for _ in range(10):
                angle = random() * pi * 2
                speed = random() * 0.5 + 0.5
                p_velocity = [cos(angle) * speed, sin(angle) * speed]
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center, p_velocity, randint(0, 7)))
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        if abs(self.dashing) > self.dashing_cooldown-10:
            self.velocity[1] = 0
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            if abs(self.dashing) == self.dashing_cooldown-9:
                self.velocity[0] *= 0.1
            p_velocity = [abs(self.dashing) / self.dashing * random() * 3, 0]
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, p_velocity, randint(0, 7)))


        self.wall_slide = False
        if (self.collisions['left'] or self.collisions['right']) and self.air_time > 4:
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5)
            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True
            self.set_action('wall_slide')

        if not self.wall_slide:
            if self.air_time > 4:
                self.set_action('jump')
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')

        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

    def render(self, surf, offset=[0, 0]):
        if abs(self.dashing) <= self.dashing_cooldown-10:
            super().render(surf, offset)
