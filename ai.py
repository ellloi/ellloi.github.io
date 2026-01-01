# ai.py
import random
import pygame

class SimpleAI:
    def __init__(self, character):
        self.char = character
        self.timer = 0
        self.action = {"move": 0, "jump": False, "light": False, "heavy": False, "special": False}
        self.cool = 0

    def update(self, enemy, projectiles):
        # enemy = the player (target)
        self.target = enemy
        self.projectiles = projectiles
        # decrease cooldowns
        if self.cool > 0:
            self.cool -= 1

    def decide(self):
        # Basic behaviour: distance-aware random choices
        if self.cool <= 0 and random.random() < 0.18:
            self.cool = random.randint(15, 40)
            # decide to attack or reposition
            dist_x = self.target.rect.centerx - self.char.rect.centerx
            dist = abs(dist_x)
            move = 0
            jump = False
            light = heavy = special = False

            # avoid projectiles sometimes
            for p in self.projectiles:
                if p.owner is not self.char:
                    if abs(p.rect.centery - self.char.rect.centery) < 40 and abs(p.rect.centerx - self.char.rect.centerx) < 180:
                        # dodge randomly
                        if random.random() < 0.6:
                            move = -1 if p.rect.centerx < self.char.rect.centerx else 1
                            if random.random() < 0.4:
                                jump = True
                            self.cool += 10
                            break

            # If far, approach and throw projectiles if character has them
            if dist > 220:
                move = 1 if dist_x > 0 else -1
                if random.random() < 0.2:
                    special = True
            elif dist > 120:
                # mid-range: use specials or heavy attacks
                move = 1 if dist_x > 0 else -1
                if random.random() < 0.35:
                    special = True
                elif random.random() < 0.4:
                    heavy = True
            else:
                # close range: hit with light/heavy
                if random.random() < 0.6:
                    light = True
                elif random.random() < 0.3:
                    heavy = True
                if random.random() < 0.2:
                    jump = True

            # occasionally retreat if percent is high
            if self.char.percent > 120 and random.random() < 0.5:
                move = -1 if dist_x > 0 else 1  # back away
                if random.random() < 0.6:
                    jump = True

            self.action = {"move": move, "jump": jump, "light": light, "heavy": heavy, "special": special}
            return self.action
        # default: minimal movement to face player
        move = 0
        if abs(self.target.rect.centerx - self.char.rect.centerx) > 30:
            move = 1 if self.target.rect.centerx > self.char.rect.centerx else -1
        # small chance to do something
        action = {"move": move, "jump": False, "light": False, "heavy": False, "special": False}
        if random.random() < 0.02:
            action["light"] = True
        return action
