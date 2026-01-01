```markdown
Mini Smash Prototype (Pygame)
=============================

What this is
- A small prototype of a Smash-like 2D fighter with:
  - player character selection
  - AI opponent that picks a random character
  - three characters with different stats and special attacks
  - percent-based damage & knockback
  - simple projectile (Mage), teleport (Ninja), heavy smash (Tank)

Requirements
- Python 3.8+
- pygame (install with `pip install pygame`)

Files
- main.py — game loop, selection, rendering
- characters.py — character classes and projectile class
- ai.py — basic AI controller

How to play
1. Run `python main.py`
2. Use Left/Right to select a character, press Enter.
3. Controls in-game (player on left):
   - Left / Right arrows: move
   - Up arrow: jump
   - Z: light attack
   - X: heavy attack
   - C: special attack

Notes and ideas for extension
- Add sprites/animations and sound effects.
- Add hitstun, recovery frames, directional influence (DI), and ledge mechanics.
- Implement better collision/physics and actual velocities for knockback.
- Create more characters and balance their stats.
- Improve AI to combo and predict player behavior.
- Add menus, rounds, scoring, and network play.

License
- This is example code for learning and prototyping.
```
