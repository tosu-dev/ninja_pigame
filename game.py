import sys
import os
import pygame
from math import sin, cos, pi
from random import randint, random

from scripts.utils import load_image, load_images, load_maps, Animation, SFX_PATH
from scripts.entities import Player, Enemy
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.tilemap import TileMap
from scripts.spark import Spark
from scripts.minimap import Minimap
from scripts.utils import MAP_PATH


class Game:
    # ===== SINGLETON =====
    __instance = None
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Game, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if (self.__initialized): return
        self.__initialized = True

        pygame.init()

        pygame.display.set_caption('PiGame')
        self.screen             = pygame.display.set_mode((640, 480))
        self.display_transition = pygame.Surface((320, 240), pygame.SRCALPHA)
        self.display_entities   = pygame.Surface((320, 240), pygame.SRCALPHA)
        self.display_elements   = pygame.Surface((320, 240), pygame.SRCALPHA)
        self.display_cooldown   = pygame.Surface((20, 20), pygame.SRCALPHA)
        self.display            = pygame.Surface((320, 240))
        self.clock              = pygame.time.Clock()

        self.movement = [False, False]

        self.assets = {
            'player'     : load_image('entities/player.png'),
            'decor'      : load_images('tiles/decor'),
            'grass'      : load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'spawners'   : load_images('tiles/spawners'),
            'stone'      : load_images('tiles/stone'),
            'bg'         : load_image('background.png'),
            'clouds'     : load_images('clouds'),
            'gun'        : load_image('gun.png'),
            'projectile' : load_image('projectile.png'),

            'particles/leaf'    : Animation(load_images('particles/leaf'), 20, loop=False),
            'particles/particle': Animation(load_images('particles/particle'), 6, loop=False),

            'player/idle'      : Animation(load_images('entities/player/idle'), 6),
            'player/run'       : Animation(load_images('entities/player/run'), 4),
            'player/jump'      : Animation(load_images('entities/player/jump')),
            'player/slide'     : Animation(load_images('entities/player/slide')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
            
            'enemy/idle': Animation(load_images('entities/enemy/idle'), 6),
            'enemy/run' : Animation(load_images('entities/enemy/run'), 4),
        }

        self.sfx = {
            'ambience': pygame.mixer.Sound(SFX_PATH + 'ambience.wav'),
            'dash': pygame.mixer.Sound(SFX_PATH + 'dash.wav'),
            'hit': pygame.mixer.Sound(SFX_PATH + 'hit.wav'),
            'jump': pygame.mixer.Sound(SFX_PATH + 'jump.wav'),
            'shoot': pygame.mixer.Sound(SFX_PATH + 'shoot.wav'),
        }
        self.sfx['ambience'].set_volume(0.2)
        self.sfx['dash'].set_volume(0.3)
        self.sfx['hit'].set_volume(0.8)
        self.sfx['jump'].set_volume(0.7) 
        self.sfx['shoot'].set_volume(0.4)

        self.minimap       = Minimap(self, (10, 10), (320, 240), size_ratio=3, unzoom=2)
        self.player        = Player(self, (0, 0), (8, 15))
        self.tilemap       = TileMap(self)
        self.level         = 0
        self.level_max     = len(os.listdir(MAP_PATH))
        self.load_level(self.level)
        
        self.cd_points = []
        self.godmod = False


    def load_level(self, map_id):
        self.dead = 0
        self.player.air_time = 0
        self.tilemap.load('data/maps/' + str(map_id) + '.json')
        self.transition    = -60
        self.scroll        = [0, 0]
        self.screenshake   = 0
        self.enemies       = []
        self.projectiles   = []
        self.particles     = []
        self.sparks        = []
        self.clouds        = Clouds(self.assets['clouds'])
        self.leaf_spawners = [pygame.Rect(4+tree['pos'][0], 4+tree['pos'][1], 23, 13) for tree in self.tilemap.extract([('large_decor', 2)], keep=True)]
 
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))
        
        self.scroll[0] = self.player.rect().centerx - self.display.get_width()/2 
        self.scroll[1] = self.player.rect().centery - self.display.get_height()/2

    def play_sfx(self, name):
        if self.sfx.get(name):
            self.sfx.get(name).stop()
            self.sfx.get(name).play()

    def run(self):
        pygame.mixer.music.load('data/music.wav')
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)

        self.sfx['ambience'].play(-1)

        while True:
            self.display_transition.fill((0, 0, 0, 0))
            self.display_elements.fill((0, 0, 0, 0))
            self.display_entities.fill((0, 0, 0, 0))
            self.display.blit(self.assets['bg'], (0, 0))

            if self.godmod:
                self.player.air_time = 0

            if not len(self.enemies):
                self.transition += 1
                if self.transition > 60:
                    self.level = (self.level + 1) % self.level_max
                    self.load_level(self.level)
            if self.transition < 0:
                self.transition += 1

            self.screenshake = max(0, self.screenshake-1)

            self.scroll[0] += (self.player.rect().centerx - self.display.get_width()/2 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.display.get_height()/2 - self.scroll[1]) / 30
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            if self.dead:
                if self.dead == 1:
                    self.play_sfx('hit')
                    for _ in range(20):
                        self.sparks.append(Spark(self.player.rect().center, random()*pi*2, 2+random(), color=(255, 0, 0)))
                        self.particles.append(Particle(self, 'particle', self.player.rect().center, [(random()-0.5)*3.5, (random()-0.5)*3.5]))
                self.dead += 1
                if self.dead > 60:
                    self.load_level(self.level)

            for rect in self.leaf_spawners:
                #if random() * 49_999 < rect.width * rect.height:
                if random() < 0.01:
                    pos = (rect.x+random()*rect.width, rect.y+random()*rect.height)
                    self.particles.append(Particle(self, 'leaf', pos, [round(random()%0.2-0.1, 1), round(random()%0.4+0.1, 1)], frame=randint(0, 20)))

            self.clouds.update()
            self.clouds.render(self.display, offset=render_scroll)

            self.tilemap.render(self.display_elements, offset=render_scroll)

            # [[x, y], direction timer]
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                projectile_img = self.assets['projectile']
                self.display_elements.blit(projectile_img, (projectile[0][0]-projectile_img.get_width()/2-render_scroll[0], projectile[0][1]-projectile_img.get_height()/2-render_scroll[1]))
                if self.tilemap.solid_check(projectile[0]) or projectile[2] > 360:
                    self.play_sfx('hit')
                    for _ in range(8):
                        self.sparks.append(Spark(projectile[0], random()-0.5+(pi if projectile[1] > 0 else 0), 2+random()))
                    self.projectiles.remove(projectile)
                elif not self.dead and abs(self.player.dashing) < self.player.dashing_cooldown-10:
                    if self.player.rect().collidepoint(projectile[0]):
                        self.projectiles.remove(projectile)
                        if not self.godmod:
                            self.dead = 1
                        self.screenshake = max(20, self.screenshake)

            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display_elements, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)

            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += sin(particle.animation.frame * 0.05) * 0.3
                if kill: 
                    self.particles.remove(particle)

            display_mask = pygame.mask.from_surface(self.display_elements)
            display_silhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display.blit(display_silhouette, offset)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = True
                    if event.key == pygame.K_UP:
                        self.player.jump()
                    if event.key == pygame.K_DOWN:
                        self.player.dash()
                    if event.key == pygame.K_g:
                        print(f"GODMOD = {self.godmod}")
                        self.godmod = not self.godmod
                        self.player.max_jumps = 999_999
                        self.player.dashing_cooldown = 11
                    if event.key == pygame.K_k and self.godmod:
                        self.enemies.clear()

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = False
            
            if self.player.dashing:
                angle = 360/self.player.dashing_cooldown * (self.player.dashing_cooldown - abs(self.player.dashing))
                self.cd_points.append((20*sin(pi*2*angle/360)+10, -20*cos(pi*2*angle/360)+10))
            else:
                self.cd_points = [(10, 10), (10, 0)]

            if len(self.cd_points) > 2:
                pygame.draw.rect(self.display_cooldown, (0, 0, 0, 255), (0, 0, 20, 20))
                pygame.draw.polygon(self.display_cooldown, (255, 255, 255, 255), self.cd_points)
            else:
                pygame.draw.rect(self.display_cooldown, (255, 255, 255, 255), (0, 0, 20, 20))

            if self.transition:
                transition_surf = pygame.Surface(self.display_transition.get_size())
                center = self.player.rect().center
                pygame.draw.circle(transition_surf, (255, 255, 255), (center[0]-render_scroll[0], center[1]-render_scroll[1]), (60 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255))
                self.display_transition.blit(transition_surf, (0, 0))

            if not self.dead:
                self.player.update(self.tilemap, movement=(self.movement[1] - self.movement[0], 0))
                self.player.render(self.display_entities, offset=render_scroll)

            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap)
                enemy.render(self.display_entities, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)

            self.display.blit(self.display_elements, (0, 0))
            self.display.blit(self.display_entities, (0, 0))
            self.minimap.render(self.display, offset=render_scroll)
            self.display.blit(self.display_cooldown, (10, self.display.get_height()-30))
            self.display.blit(self.display_transition, (0, 0))
            

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), ((random() * self.screenshake - self.screenshake / 2), (random() * self.screenshake - self.screenshake / 2)))
            pygame.display.update()
            self.clock.tick(60)
            #print(int(self.clock.get_fps()))


# ========================================
Game().run()
