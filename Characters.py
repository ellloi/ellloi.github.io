# characters.py
import pygame
import random
import sys
import os
import math

# Character module with animated sprites and improved visuals
BASE_WIDTH, BASE_HEIGHT = 64, 80  # slightly larger to suit higher-res art

# Resource helper (works with PyInstaller)
def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_image(path):
    try:
        return pygame.image.load(resource_path(path)).convert_alpha()
    except Exception:
        return None

# Animated sprite helper
class AnimatedSprite:
    def __init__(self, frames, frame_time=0.08, loop=True):
        self.frames = frames if frames else []
        self.frame_time = frame_time
        self.loop = loop
        self.time = 0.0
        self.index = 0

    def update(self, dt):
        if not self.frames:
            return
        self.time += dt
        if self.time >= self.frame_time:
            self.time -= self.frame_time
            self.index += 1
            if self.index >= len(self.frames):
                if self.loop:
                    self.index = 0
                else:
                    self.index = len(self.frames)-1

    def current(self):
        if not self.frames:
            return None
        return self.frames[self.index]

# Projectile supports optional sprite + animation
class Projectile:
    def __init__(self, x, y, vx, vy, owner, color=(255,255,0), damage=6, knockback=6, size=12, sprite=None):
        self.rect = pygame.Rect(x, y, size, size)
        self.vel = pygame.math.Vector2(vx, vy)
        self.owner = owner
        self.color = color
        self.damage = damage
        self.knockback = knockback
        self.alive = True
        # optional sprite surface
        self.sprite = sprite
        self.anim = None
        if isinstance(sprite, AnimatedSprite):
            self.anim = sprite

    def update(self):
        self.rect.x += int(self.vel.x)
        self.rect.y += int(self.vel.y)
        if self.anim:
            # anim expects dt; provide small step (approx)
            self.anim.update(1/60.0)

    def draw(self, surf):
        if self.sprite:
            if isinstance(self.sprite, AnimatedSprite):
                frame = self.sprite.current()
            else:
                frame = self.sprite
            if frame:
                img = pygame.transform.smoothscale(frame, (self.rect.width, self.rect.height))
                surf.blit(img, self.rect.topleft)
                return
        pygame.draw.rect(surf, self.color, self.rect)

# Base Character with sprite/animation support
class Character:
    def __init__(self, name, color):
        self.ch_name = self.__class__.__name__
        self.player_name = name
        self.color = color
        self.rect = pygame.Rect(0, 0, BASE_WIDTH, BASE_HEIGHT)
        self.vel = pygame.math.Vector2(0, 0)
        self.speed = 4.0
        self.jump_strength = -14
        self.on_ground = False
        self.facing = 1
        self.percent = 0.0
        self.weight = 1.0
        self.active_attacks = []
        self.last_attack_time = 0
        self.attack_cooldown = 300
        self.stocks = 3

        # sprite fields
        self.sprites = {}  # map: 'idle','run','attack','special','portrait'
        self.animations = {}
        self.current_state = 'idle'
        self.portrait = None
        self.scale = 1.0

    def try_load_sprites(self):
        # try load from assets/characters/<ClassName>/
        base = f"assets/characters/{self.ch_name}"
        states = {
            "idle": ("idle", 0.12),
            "run": ("run", 0.08),
            "attack": ("attack", 0.06),
            "special": ("special", 0.08),
            "portrait": ("portrait", None),
            "icon": ("icon", None),
        }
        for key, (fname, ft) in states.items():
            folder = resource_path(os.path.join(base, fname))
            frames = []
            # if folder is a file (single image), try that first
            single_png = resource_path(os.path.join(base, fname + ".png"))
            if os.path.exists(single_png):
                img = load_image(os.path.join(base, fname + ".png"))
                if img:
                    frames = [img]
            elif os.path.isdir(folder):
                # load all pngs in directory sorted
                files = sorted([f for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg", ".webp"))])
                for f in files:
                    img = load_image(os.path.join(base, fname, f))
                    if img:
                        frames.append(img)
            if frames:
                if key == "portrait" or key == "icon":
                    self.sprites[key] = frames[0]
                    if key == "portrait":
                        self.portrait = frames[0]
                else:
                    self.animations[key] = AnimatedSprite(frames, frame_time=ft if ft else 0.08, loop=True)
            else:
                # no frames found; keep fallback
                self.animations[key] = None
        # optional scale config
        cfg = resource_path(os.path.join(base, "scale.txt"))
        try:
            if os.path.exists(cfg):
                with open(cfg, "r") as f:
                    s = float(f.read().strip())
                    self.scale = max(0.5, min(2.0, s))
                    # scale rect accordingly
                    sw = int(BASE_WIDTH * self.scale)
                    sh = int(BASE_HEIGHT * self.scale)
                    self.rect.size = (sw, sh)
        except Exception:
            pass

    def update_animation(self, dt):
        # advance current animation
        anim = self.animations.get(self.current_state)
        if anim:
            anim.update(dt)
        # small friction smoothing
        # choose animation based on velocity
        if abs(self.vel.x) > 1.2 and self.on_ground:
            self.current_state = 'run'
        else:
            self.current_state = 'idle'

    def draw(self, surf):
        # draw using animation frame if available, else colored rect
        anim = self.animations.get(self.current_state)
        frame = anim.current() if anim else None
        if frame is None:
            # fallback rectangle (still looks okay)
            pygame.draw.rect(surf, self.color, self.rect)
        else:
            # flip according to facing
            frame_img = frame
            if self.facing < 0:
                frame_img = pygame.transform.flip(frame, True, False)
            # scale to character rect smoothly
            img = pygame.transform.smoothscale(frame_img, (self.rect.width, self.rect.height))
            # apply simple lighting: slightly brighten top area (drawn by pre-made art better)
            surf.blit(img, self.rect.topleft)
        # draw percent text
        font = pygame.font.SysFont("Arial", 16)
        txt = font.render(f"{int(self.percent)}%", True, (230,230,230))
        surf.blit(txt, (self.rect.centerx - txt.get_width()//2, self.rect.top - 18))

    def update_physics(self, gravity):
        self.vel.y += gravity
        if self.on_ground:
            self.vel.x *= 0.85

    def apply_input(self, move, jump):
        if move != 0:
            self.vel.x += move * self.speed
            self.facing = 1 if move > 0 else -1
        if jump and self.on_ground:
            self.vel.y = self.jump_strength
            self.on_ground = False

    def light_attack(self):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time < self.attack_cooldown:
            return None
        self.last_attack_time = now
        reach = int(self.rect.width * 0.6)
        if self.facing == 1:
            rect = pygame.Rect(self.rect.right, self.rect.centery - 10, reach, 20)
        else:
            rect = pygame.Rect(self.rect.left - reach, self.rect.centery - 10, reach, 20)
        self.active_attacks.append({"rect": rect, "damage": 6, "knockback": 6, "time": now, "alive": True})
        # if there is an attack animation, trigger it
        if self.animations.get("attack"):
            self.current_state = "attack"
        return ("melee",)

    def heavy_attack(self):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time < int(self.attack_cooldown * 1.3):
            return None
        self.last_attack_time = now
        reach = int(self.rect.width * 0.9)
        if self.facing == 1:
            rect = pygame.Rect(self.rect.right, self.rect.centery - 14, reach, 28)
            self.vel.x -= 2
        else:
            rect = pygame.Rect(self.rect.left - reach, self.rect.centery - 14, reach, 28)
            self.vel.x += 2
        self.active_attacks.append({"rect": rect, "damage": 10, "knockback": 12, "time": now, "alive": True})
        if self.animations.get("attack"):
            self.current_state = "attack"
        return ("melee",)

    def special_attack(self):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time < int(self.attack_cooldown * 0.9):
            return None
        self.last_attack_time = now
        self.vel.x += 6 * self.facing
        reach = int(self.rect.width * 0.7)
        if self.facing == 1:
            rect = pygame.Rect(self.rect.right, self.rect.centery - 10, reach, 20)
        else:
            rect = pygame.Rect(self.rect.left - reach, self.rect.centery - 10, reach, 20)
        self.active_attacks.append({"rect": rect, "damage": 8, "knockback": 10, "time": now, "alive": True})
        if self.animations.get("special"):
            self.current_state = "special"
        return ("melee",)

    def receive_hit(self, damage, base_kb, source):
        self.percent += damage
        kb_force = base_kb * (1 + self.percent / 100.0) / max(0.5, self.weight)
        direction = 1 if self.rect.centerx > source.rect.centerx else -1
        self.vel.x += kb_force * direction
        self.vel.y -= kb_force * 0.6

    def on_ko(self):
        self.stocks -= 1
        if self.stocks <= 0:
            self.stocks = 3
            self.percent = 0

# --- Original and new characters (same behaviors as before) ---

class Ninja(Character):
    def __init__(self, name, color):
        super().__init__(name, color)
        self.speed = 5.5
        self.jump_strength = -15
        self.weight = 0.9
        self.attack_cooldown = 220

    def special_attack(self):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time < 400:
            return None
        self.last_attack_time = now
        # teleport dash
        self.rect.x += 60 * self.facing
        reach = 40
        if self.facing == 1:
            rect = pygame.Rect(self.rect.right, self.rect.centery - 12, reach, 24)
        else:
            rect = pygame.Rect(self.rect.left - reach, self.rect.centery - 12, reach, 24)
        self.active_attacks.append({"rect": rect, "damage": 12, "knockback": 14, "time": now, "alive": True})
        if self.animations.get("special"):
            self.current_state = "special"
        return ("melee",)

class Tank(Character):
    def __init__(self, name, color):
        super().__init__(name, color)
        self.speed = 3.2
        self.jump_strength = -13
        self.weight = 1.8
        self.attack_cooldown = 420

    def light_attack(self):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time < self.attack_cooldown:
            return None
        self.last_attack_time = now
        reach = 40
        rect = pygame.Rect(self.rect.right, self.rect.centery - 16, reach, 32) if self.facing==1 else pygame.Rect(self.rect.left - reach, self.rect.centery - 16, reach, 32)
        self.active_attacks.append({"rect": rect, "damage": 8, "knockback": 8, "time": now, "alive": True})
        if self.animations.get("attack"):
            self.current_state = "attack"
        return ("melee",)

    def special_attack(self):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time < 900:
            return None
        self.last_attack_time = now
        reach = 60
        rect = pygame.Rect(self.rect.right, self.rect.centery - 22, reach, 44) if self.facing==1 else pygame.Rect(self.rect.left - reach, self.rect.centery - 22, reach, 44)
        self.active_attacks.append({"rect": rect, "damage": 18, "knockback": 28, "time": now, "alive": True})
        self.vel.x -= 4 * self.facing
        if self.animations.get("special"):
            self.current_state = "special"
        return ("melee",)

class Mage(Character):
    def __init__(self, name, color):
        super().__init__(name, color)
        self.speed = 4.0
        self.jump_strength = -13.5
        self.weight = 1.0
        self.attack_cooldown = 300

    def special_attack(self):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time < 500:
            return None
        self.last_attack_time = now
        vx = 10 * self.facing
        # attempt to use a projectile sprite if available
        proj_sprite = None
        anim = self.animations.get("special")
        if anim:
            proj_sprite = anim  # use special anim as projectile if desired
        proj = Projectile(self.rect.centerx + self.facing * 30, self.rect.centery - 10, vx, 0, self, color=(255,200,60), damage=9, knockback=10, size=14, sprite=proj_sprite)
        return ("proj", proj)

class Archer(Character):
    def __init__(self, name, color):
        super().__init__(name, color)
        self.speed = 4.2
        self.jump_strength = -13.5
        self.weight = 0.95
        self.attack_cooldown = 260

    def special_attack(self):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time < 420:
            return None
        self.last_attack_time = now
        vx = 12 * self.facing
        vy = -2
        proj = Projectile(self.rect.centerx + self.facing * 30, self.rect.centery - 16, vx, vy, self, color=(200,180,80), damage=11, knockback=11, size=12)
        return ("proj", proj)

class Assassin(Character):
    def __init__(self, name, color):
        super().__init__(name, color)
        self.speed = 6.0
        self.jump_strength = -16
        self.weight = 0.8
        self.attack_cooldown = 200

    def light_attack(self):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time < 160:
            return None
        self.last_attack_time = now
        reach = 28
        if self.facing == 1:
            rect = pygame.Rect(self.rect.right, self.rect.centery - 8, reach, 16)
        else:
            rect = pygame.Rect(self.rect.left - reach, self.rect.centery - 8, reach, 16)
        self.active_attacks.append({"rect": rect, "damage": 5, "knockback": 5, "time": now, "alive": True})
        if self.animations.get("attack"):
            self.current_state = "attack"
        return ("melee",)

    def special_attack(self):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time < 700:
            return None
        self.last_attack_time = now
        self.rect.x += 80 * self.facing
        reach = 40
        if self.facing == 1:
            rect = pygame.Rect(self.rect.right, self.rect.centery - 14, reach, 28)
        else:
            rect = pygame.Rect(self.rect.left - reach, self.rect.centery - 14, reach, 28)
        self.active_attacks.append({"rect": rect, "damage": 16, "knockback": 18, "time": now, "alive": True})
        if self.animations.get("special"):
            self.current_state = "special"
        return ("melee",)

class Priest(Character):
    def __init__(self, name, color):
        super().__init__(name, color)
        self.speed = 3.8
        self.jump_strength = -12.5
        self.weight = 1.05
        self.attack_cooldown = 320

    def special_attack(self):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time < 1000:
            return None
        self.last_attack_time = now
        heal_amount = 12
        self.percent = max(0.0, self.percent - heal_amount)
        if self.animations.get("special"):
            self.current_state = "special"
        return ("melee",)

class Boxer(Character):
    def __init__(self, name, color):
        super().__init__(name, color)
        self.speed = 5.0
        self.jump_strength = -13.0
        self.weight = 0.95
        self.attack_cooldown = 180

    def light_attack(self):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time < self.attack_cooldown:
            return None
        self.last_attack_time = now
        reach = 26
        for i in range(3):
            t_offset = i * 60
            ts = now + t_offset
            if self.facing == 1:
                rect = pygame.Rect(self.rect.right, self.rect.centery - 10, reach, 20)
            else:
                rect = pygame.Rect(self.rect.left - reach, self.rect.centery - 10, reach, 20)
            dmg = 4 + i
            kb = 4 + i
            self.active_attacks.append({"rect": rect, "damage": dmg, "knockback": kb, "time": ts, "alive": True})
        if self.animations.get("attack"):
            self.current_state = "attack"
        return ("melee",)

    def special_attack(self):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time < 600:
            return None
        self.last_attack_time = now
        reach = 30
        if self.facing == 1:
            rect = pygame.Rect(self.rect.right, self.rect.top - 10, reach, self.rect.height + 20)
        else:
            rect = pygame.Rect(self.rect.left - reach, self.rect.top - 10, reach, self.rect.height + 20)
        self.active_attacks.append({"rect": rect, "damage": 12, "knockback": 22, "time": now, "alive": True})
        if self.animations.get("special"):
            self.current_state = "special"
        return ("melee",)

class Robot(Character):
    def __init__(self, name, color):
        super().__init__(name, color)
        self.speed = 3.6
        self.jump_strength = -12.0
        self.weight = 1.4
        self.attack_cooldown = 360

    def light_attack(self):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time < self.attack_cooldown:
            return None
        self.last_attack_time = now
        reach = 36
        if self.facing == 1:
            rect = pygame.Rect(self.rect.right, self.rect.centery - 12, reach, 24)
        else:
            rect = pygame.Rect(self.rect.left - reach, self.rect.centery - 12, reach, 24)
        self.active_attacks.append({"rect": rect, "damage": 9, "knockback": 9, "time": now, "alive": True})
        if self.animations.get("attack"):
            self.current_state = "attack"
        return ("melee",)

    def special_attack(self):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time < 900:
            return None
        self.last_attack_time = now
        vx = 7 * self.facing
        proj = Projectile(self.rect.centerx + self.facing * 36, self.rect.centery - 8, vx, 0, self, color=(200,100,100), damage=20, knockback=24, size=18)
        self.vel.x -= 5 * self.facing
        return ("proj", proj)

class Gunner(Character):
    def __init__(self, name, color):
        super().__init__(name, color)
        self.speed = 4.4
        self.jump_strength = -13.0
        self.weight = 1.0
        self.attack_cooldown = 300

    def light_attack(self):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time < 220:
            return None
        self.last_attack_time = now
        vx = 14 * self.facing
        proj = Projectile(self.rect.centerx + self.facing * 28, self.rect.centery - 8, vx, 0, self, color=(180,255,200), damage=7, knockback=7, size=8)
        return ("proj", proj)

    def special_attack(self):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time < 700:
            return None
        self.last_attack_time = now
        vx = 16 * self.facing
        proj = Projectile(self.rect.centerx + self.facing * 28, self.rect.centery - 6, vx, -1, self, color=(120,220,255), damage=14, knockback=16, size=12)
        self.vel.x -= 2 * self.facing
        return ("proj", proj)

class Brawler(Character):
    def __init__(self, name, color):
        super().__init__(name, color)
        self.speed = 3.9
        self.jump_strength = -13.0
        self.weight = 1.2
        self.attack_cooldown = 300

    def heavy_attack(self):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time < int(self.attack_cooldown * 1.2):
            return None
        self.last_attack_time = now
        reach = 48
        if self.facing == 1:
            rect = pygame.Rect(self.rect.right, self.rect.centery - 20, reach, 40)
            self.vel.x -= 3
        else:
            rect = pygame.Rect(self.rect.left - reach, self.rect.centery - 20, reach, 40)
            self.vel.x += 3
        self.active_attacks.append({"rect": rect, "damage": 14, "knockback": 20, "time": now, "alive": True})
        if self.animations.get("attack"):
            self.current_state = "attack"
        return ("melee",)

    def special_attack(self):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time < 900:
            return None
        self.last_attack_time = now
        size = 120
        rect = pygame.Rect(self.rect.centerx - size//2, self.rect.centery - size//2, size, size)
        self.active_attacks.append({"rect": rect, "damage": 16, "knockback": 22, "time": now, "alive": True})
        self.vel.y += 6
        if self.animations.get("special"):
            self.current_state = "special"
        return ("melee",)
