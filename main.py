# main.py
import pygame
import random
import sys
import os
import math
from characters import (Ninja, Tank, Mage, Archer, Assassin, Priest,
                        Boxer, Robot, Gunner, Brawler, Projectile, Character)

pygame.init()
WIDTH, HEIGHT = 1000, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mini Smash Prototype - Enhanced Graphics")
CLOCK = pygame.time.Clock()
FONT = pygame.font.SysFont("Arial", 20)

GRAVITY = 0.9
GROUND_Y = HEIGHT - 80

# Simple stage/platforms
PLATFORMS = [
    pygame.Rect(0, GROUND_Y, WIDTH, 80),
    pygame.Rect(WIDTH // 2 - 100, GROUND_Y - 150, 200, 20),
    pygame.Rect(150, GROUND_Y - 90, 200, 20),
    pygame.Rect(WIDTH - 350, GROUND_Y - 90, 200, 20),
]

# Colors
BG = (30, 30, 40)
WHITE = (240, 240, 240)
COLOR_SWATCH = {
    "Ninja": (40, 180, 180),
    "Tank": (200, 80, 80),
    "Mage": (150, 120, 240),
    "Archer": (200, 160, 80),
    "Assassin": (50, 50, 50),
    "Priest": (200, 220, 250),
    "Boxer": (220, 120, 80),
    "Robot": (180, 180, 200),
    "Gunner": (120, 200, 180),
    "Brawler": (170, 110, 140),
}

# Paths & resource helper for PyInstaller compatibility
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller bundle """
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Load background and UI images (optional)
def load_image(path, colorkey=None):
    try:
        surf = pygame.image.load(resource_path(path)).convert_alpha()
        return surf
    except Exception:
        return None

BG_IMG = load_image("assets/backgrounds/stage_bg.png")  # optional nice background

# Particle system for hits and special effects
class Particle:
    def __init__(self, pos, vel, color, life, size):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.color = color
        self.life = life
        self.size = size
        self.age = 0

    def update(self, dt):
        self.pos += self.vel * dt
        self.age += dt

    def draw(self, surf):
        alpha = max(0, 255 * (1 - self.age / self.life))
        if alpha <= 0:
            return
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, int(alpha)), (self.size, self.size), self.size)
        surf.blit(s, (self.pos.x - self.size, self.pos.y - self.size))

# Small visual helper: soft shadow below characters
def draw_shadow(surf, rect):
    w = int(rect.width * 1.1)
    h = int(rect.height * 0.35)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, 120), (0, 0, w, h))
    surf.blit(s, (rect.centerx - w // 2, rect.bottom - h // 2))

# Selection UI: list all classes
CHARACTER_CLASSES = [Ninja, Tank, Mage, Archer, Assassin, Priest, Boxer, Robot, Gunner, Brawler]

def load_icon_for(cls):
    # assets/<ClassName>/icon.png
    path = f"assets/characters/{cls.__name__}/icon.png"
    img = load_image(path)
    if img:
        return img
    # fallback: generated color square
    surf = pygame.Surface((160, 160))
    surf.fill(COLOR_SWATCH.get(cls.__name__, (120, 120, 120)))
    font = pygame.font.SysFont("Arial", 28)
    txt = font.render(cls.__name__, True, (20, 20, 20))
    surf.blit(txt, (8, 60))
    return surf

def draw_text(surf, text, x, y, col=WHITE):
    txt = FONT.render(text, True, col)
    surf.blit(txt, (x, y))

def character_selection():
    running = True
    choices = CHARACTER_CLASSES
    idx = 0
    icons = [load_icon_for(c) for c in choices]
    while running:
        CLOCK.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RIGHT:
                    idx = (idx + 1) % len(choices)
                elif e.key == pygame.K_LEFT:
                    idx = (idx - 1) % len(choices)
                elif e.key == pygame.K_RETURN:
                    return choices[idx]
        SCREEN.fill(BG)
        if BG_IMG:
            SCREEN.blit(pygame.transform.scale(BG_IMG, (WIDTH, HEIGHT)), (0, 0))
        draw_text(SCREEN, "Choose your character (Left/Right). Enter to pick.", 20, 20)
        for i, cls in enumerate(choices):
            x = 60 + (i % 5) * 180
            y = 120 + (i // 5) * 240
            rect = pygame.Rect(x, y, 160, 160)
            icon = icons[i]
            SCREEN.blit(icon, rect.topleft)
            draw_text(SCREEN, cls.__name__, x + 8, y + 166)
            if i == idx:
                pygame.draw.rect(SCREEN, WHITE, rect, 4)
        pygame.display.flip()

def reset_positions(player, enemy):
    player.rect.center = (int(WIDTH * 0.25), GROUND_Y - player.rect.height // 2)
    enemy.rect.center = (int(WIDTH * 0.75), GROUND_Y - enemy.rect.height // 2)
    player.vel = pygame.math.Vector2(0, 0)
    enemy.vel = pygame.math.Vector2(0, 0)
    player.on_ground = False
    enemy.on_ground = False

def handle_platform_collisions(entity):
    entity.on_ground = False
    for plat in PLATFORMS:
        if entity.rect.colliderect(plat):
            # simple ground collision from above
            if entity.vel.y >= 0 and entity.rect.bottom - entity.vel.y <= plat.top + 6:
                entity.rect.bottom = plat.top
                entity.vel.y = 0
                entity.on_ground = True

# Screen shake helper
shake_offset = pygame.math.Vector2(0, 0)
shake_timer = 0
def start_screen_shake(intensity=6, duration=0.25):
    global shake_timer, shake_intensity
    shake_timer = duration
    shake_intensity = intensity

def update_shake(dt):
    global shake_offset, shake_timer
    if shake_timer > 0:
        shake_timer -= dt
        shake_offset.x = random.uniform(-1, 1) * shake_intensity
        shake_offset.y = random.uniform(-1, 1) * (shake_intensity * 0.5)
    else:
        shake_offset.x = 0
        shake_offset.y = 0

# Simple button helper used on win/lose screen
def draw_button(surf, rect, text, mouse_pos, mouse_down):
    hovered = rect.collidepoint(mouse_pos)
    color = (220, 220, 220) if hovered else (200, 200, 200)
    pygame.draw.rect(surf, color, rect, border_radius=8)
    pygame.draw.rect(surf, (100, 100, 100), rect, 2, border_radius=8)
    txt = FONT.render(text, True, (20, 20, 20))
    surf.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))
    return hovered and mouse_down

def main_game(player_cls, enemy_cls):
    # instantiate characters and load sprites if available
    player = player_cls("Player", COLOR_SWATCH.get(player_cls.__name__, (200, 200, 200)))
    enemy = enemy_cls("AI", COLOR_SWATCH.get(enemy_cls.__name__, (200, 200, 200)))
    # tell characters to try load their sprite sets (characters handle loading)
    if hasattr(player, "try_load_sprites"):
        player.try_load_sprites()
    if hasattr(enemy, "try_load_sprites"):
        enemy.try_load_sprites()

    from ai import SimpleAI
    ai = SimpleAI(enemy)
    projectiles = []
    particles = []

    reset_positions(player, enemy)

    game_over = False
    winner = None  # 'player' or 'enemy' or 'draw'

    running = True
    while running:
        dt = CLOCK.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        mouse_down = False
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mouse_down = True
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                # return to selection on ESC
                return "selection"

        if not game_over:
            # --- Input (player)
            keys = pygame.key.get_pressed()
            move_input = 0
            if keys[pygame.K_LEFT]:
                move_input -= 1
            if keys[pygame.K_RIGHT]:
                move_input += 1
            jump_pressed = keys[pygame.K_UP]
            attack_light = keys[pygame.K_z]
            attack_heavy = keys[pygame.K_x]
            attack_special = keys[pygame.K_c]

            # Player updates
            player.update_physics(GRAVITY)
            player.apply_input(move_input, jump_pressed)
            if attack_light:
                maybe = player.light_attack()
                if maybe and maybe[0] == "proj":
                    projectiles.append(maybe[1])
            if attack_heavy:
                player.heavy_attack()
            if attack_special:
                maybe = player.special_attack()
                if maybe and maybe[0] == "proj":
                    projectiles.append(maybe[1])

            # AI makes decision
            ai.update(player, projectiles)
            ai_action = ai.decide()
            enemy.update_physics(GRAVITY)
            enemy.apply_input(ai_action["move"], ai_action["jump"])
            if ai_action["light"]:
                maybe = enemy.light_attack()
                if maybe and maybe[0] == "proj":
                    projectiles.append(maybe[1])
            if ai_action["heavy"]:
                enemy.heavy_attack()
            if ai_action["special"]:
                maybe = enemy.special_attack()
                if maybe and maybe[0] == "proj":
                    projectiles.append(maybe[1])

            # Update projectiles
            for p in projectiles[:]:
                p.update()
                # spawn trail particles for fancy projectiles
                if random.random() < 0.25:
                    particles.append(Particle((p.rect.centerx, p.rect.centery),
                                              (random.uniform(-5, 5) * 0.1, random.uniform(-5, 5) * 0.1),
                                              (255, 220, 160), 0.35, 3))
                if not p.alive or p.rect.right < -100 or p.rect.left > WIDTH + 100:
                    projectiles.remove(p)

            # Platform collisions and clamping
            player.rect.clamp_ip(pygame.Rect(-500, -500, WIDTH + 1000, HEIGHT + 1000))
            enemy.rect.clamp_ip(pygame.Rect(-500, -500, WIDTH + 1000, HEIGHT + 1000))
            handle_platform_collisions(player)
            handle_platform_collisions(enemy)

            # Attacks: check hitboxes from last attacks
            for owner in (player, enemy):
                for atk in owner.active_attacks[:]:
                    atk_rect, damage, kb = atk["rect"], atk["damage"], atk["knockback"]
                    target = enemy if owner is player else player
                    if atk_rect.colliderect(target.rect) and atk["alive"]:
                        target.receive_hit(damage, kb, owner)
                        atk["alive"] = False
                        # spawn hit particles and screen shake for strong hits
                        for i in range(8):
                            particles.append(Particle((target.rect.centerx + random.uniform(-8, 8),
                                                       target.rect.centery + random.uniform(-8, 8)),
                                                      (random.uniform(-60, 60) * 0.02,
                                                       random.uniform(-120, -20) * 0.02),
                                                      (255, 220, 120), 0.4, random.randint(2, 5)))
                        if kb > 15:
                            start_screen_shake(intensity=min(14, kb / 1.5), duration=0.25)
                owner.active_attacks = [a for a in owner.active_attacks if a["alive"] and pygame.time.get_ticks() - a["time"] < 600]

            # Projectiles hitting players
            for p in projectiles[:]:
                if p.owner is player and p.rect.colliderect(enemy.rect):
                    enemy.receive_hit(p.damage, p.knockback, p.owner)
                    # big spark
                    for i in range(6):
                        particles.append(Particle((p.rect.centerx, p.rect.centery),
                                                  (random.uniform(-90, 90) * 0.02,
                                                   random.uniform(-120, -20) * 0.02),
                                                  (255, 200, 60), 0.35, 4))
                    if p.knockback > 16:
                        start_screen_shake(intensity=8, duration=0.18)
                    p.alive = False
                elif p.owner is enemy and p.rect.colliderect(player.rect):
                    player.receive_hit(p.damage, p.knockback, p.owner)
                    for i in range(6):
                        particles.append(Particle((p.rect.centerx, p.rect.centery),
                                                  (random.uniform(-90, 90) * 0.02,
                                                   random.uniform(-120, -20) * 0.02),
                                                  (255, 200, 60), 0.35, 4))
                    if p.knockback > 16:
                        start_screen_shake(intensity=8, duration=0.18)
                    p.alive = False
                if not p.alive and p in projectiles:
                    projectiles.remove(p)

            # Apply continuous knockback movement (they already receive velocity changes)
            player.rect.x += int(player.vel.x)
            player.rect.y += int(player.vel.y)
            enemy.rect.x += int(enemy.vel.x)
            enemy.rect.y += int(enemy.vel.y)

            # KO check & respawn or set game over
            def check_ko(ent, spawn_x):
                nonlocal game_over, winner
                if ent.rect.top > HEIGHT + 200 or ent.rect.right < -200 or ent.rect.left > WIDTH + 200:
                    # If this KO would reduce stocks to zero or below, declare match end
                    if ent.stocks <= 1:
                        # Other entity wins
                        other = enemy if ent is player else player
                        winner = "player" if other is player else "enemy"
                        game_over = True
                        return
                    # Otherwise, call on_ko to reduce stocks (characters.on_ko handles reduction)
                    ent.on_ko()
                    ent.percent = 0
                    ent.rect.center = (int(spawn_x), GROUND_Y - ent.rect.height // 2)
                    ent.vel = pygame.math.Vector2(0, 0)

            check_ko(player, WIDTH * 0.25)
            check_ko(enemy, WIDTH * 0.75)

            # Update animations & particles & shake
            if hasattr(player, "update_animation"):
                player.update_animation(dt)
            if hasattr(enemy, "update_animation"):
                enemy.update_animation(dt)
            for p in projectiles:
                if hasattr(p, "update_animation"):
                    p.update_animation(dt)

            for part in particles[:]:
                part.update(dt)
                if part.age >= part.life:
                    particles.remove(part)

            update_shake(dt)

        # ---- Rendering
        # draw background
        SCREEN.fill(BG)
        if BG_IMG:
            SCREEN.blit(pygame.transform.scale(BG_IMG, (WIDTH, HEIGHT)), (0, 0))
        # world surface to apply shake
        world = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        # Platforms
        for plat in PLATFORMS:
            pygame.draw.rect(world, (60, 60, 80), plat)

        # Draw projectiles (with shadows)
        for p in projectiles:
            # shadow
            shadow_rect = p.rect.copy()
            shadow_rect.y += 6
            s = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (0, 0, 0, 120), (0, 0, shadow_rect.width, shadow_rect.height))
            world.blit(s, (shadow_rect.x, shadow_rect.y))
            p.draw(world)

        # Characters (draw shadow, sprite, name/percent)
        for ent in (player, enemy):
            draw_shadow(world, ent.rect)
            ent.draw(world)

        # Particles above everything
        for part in particles:
            part.draw(world)

        # UI overlay on top of world: health/percent bars and controls
        ui = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        # Player info
        def draw_hud(surf, ent, x, y):
            name_txt = FONT.render(f"{ent.player_name} - {ent.ch_name}", True, WHITE)
            surf.blit(name_txt, (x, y))
            # percent bar (stylized)
            pct = int(ent.percent)
            pct_txt = FONT.render(f"{pct}%", True, WHITE)
            surf.blit(pct_txt, (x, y + 22))
            # portrait if available
            if hasattr(ent, "portrait") and ent.portrait:
                portrait = pygame.transform.smoothscale(ent.portrait, (64, 64))
                surf.blit(portrait, (x + 120, y))
            # stocks
            stxt = FONT.render("Stocks: " + "❤" * ent.stocks, True, WHITE)
            surf.blit(stxt, (x, y + 44))

        draw_hud(ui, player, 10, 10)
        draw_hud(ui, enemy, WIDTH - 240, 10)
        draw_text(ui, "Controls: ← → jump: ↑  Z:light  X:heavy  C:special", 10, HEIGHT - 30)

        # If game over, display win/lose screen overlay with button back to selection
        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            title = "You Win!" if winner == "player" else ("You Lose!" if winner == "enemy" else "Draw")
            title_txt = pygame.font.SysFont("Arial", 56).render(title, True, (255, 255, 255))
            overlay.blit(title_txt, (WIDTH // 2 - title_txt.get_width() // 2, HEIGHT // 2 - 120))

            # Button: Return to Character Select
            btn_rect = pygame.Rect(WIDTH // 2 - 140 // 2, HEIGHT // 2 - 20, 140, 48)
            clicked = draw_button(overlay, btn_rect, "Character Select", (mouse_pos[0] - int(shake_offset.x), mouse_pos[1] - int(shake_offset.y)), mouse_down)
            # Also allow restart same matchup button if desired (not requested, so just selection)
            SCREEN.blit(world, (shake_offset.x, shake_offset.y))
            SCREEN.blit(ui, (0, 0))
            SCREEN.blit(overlay, (0, 0))
            pygame.display.flip()
            if clicked:
                return "selection"
            # Continue looping on the overlay (wait for click/ESC/quit)
            continue

        # blit world with shake
        SCREEN.blit(world, (shake_offset.x, shake_offset.y))
        SCREEN.blit(ui, (0, 0))

        pygame.display.flip()

    pygame.quit()
    return "quit"

if __name__ == "__main__":
    # top-level loop: go from selection -> game -> selection when player clicks button
    while True:
        player_cls = character_selection()
        enemy_cls = random.choice(CHARACTER_CLASSES)
        result = main_game(player_cls, enemy_cls)
        if result == "quit":
            break
        # if result == "selection", loop continues and character_selection() runs again
