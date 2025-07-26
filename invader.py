import random
import pyxel
from typing import List, Optional

class Bullet:
    def __init__(self, x: int, y: int, dy: int):
        self.x = x
        self.y = y
        self.dy = dy

    def update(self) -> bool:
        self.y += self.dy
        return 0 <= self.y < pyxel.height

    def draw(self, color: int) -> None:
        pyxel.rect(self.x, self.y, 1, 4, color)

class Player:
    def __init__(self) -> None:
        self.x = pyxel.width // 2
        self.lives = 3
        self.bullet: Optional[Bullet] = None

    def update(self) -> None:
        if pyxel.btn(pyxel.KEY_LEFT):
            self.x = max(self.x - 2, 0)
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.x = min(self.x + 2, pyxel.width - 8)
        if pyxel.btnp(pyxel.KEY_SPACE) and self.bullet is None:
            self.bullet = Bullet(self.x + 4, pyxel.height - 10, -4)
        if self.bullet and not self.bullet.update():
            self.bullet = None

    def draw(self) -> None:
        ship_y = pyxel.height - 8
        pyxel.tri(self.x, ship_y + 7, self.x + 4, ship_y, self.x + 8, ship_y + 7, 9)
        pyxel.rect(self.x + 2, ship_y + 4, 4, 3, 11)
        if self.bullet:
            self.bullet.draw(7)

class Invader:
    def __init__(self, x: int, y: int, score: int) -> None:
        self.x = x
        self.y = y
        self.score = score

    def draw(self) -> None:
        px = self.x
        py = self.y
        pyxel.rect(px + 1, py, 6, 2, 11)
        pyxel.rect(px, py + 2, 8, 3, 11)
        pyxel.rect(px + 1, py + 5, 6, 1, 11)

class InvaderGroup:
    def __init__(self) -> None:
        self.invaders: List[Invader] = []
        self.dir = 1
        self.timer = 0
        for row, points in enumerate([30, 20, 10]):
            for col in range(11):
                self.invaders.append(Invader(col * 10 + 20, row * 8 + 20, points))

    def update(self) -> None:
        self.timer += 1
        speed = max(5, len(self.invaders) // 2)
        if self.timer < speed:
            return
        self.timer = 0
        edge = False
        for inv in self.invaders:
            inv.x += self.dir
            if inv.x <= 4 or inv.x >= pyxel.width - 12:
                edge = True
        if edge:
            self.dir *= -1
            for inv in self.invaders:
                inv.y += 8

    def draw(self) -> None:
        for inv in self.invaders:
            inv.draw()

    def bottom(self) -> int:
        return max(inv.y for inv in self.invaders) if self.invaders else 0

class Barrier:
    def __init__(self, x: int, y: int) -> None:
        self.blocks = []
        for bx in range(4):
            for by in range(3):
                self.blocks.append({'x': x + bx * 3, 'y': y + by * 3, 'hp': 3})

    def hit(self, x: int, y: int) -> bool:
        for block in self.blocks:
            if block['hp'] > 0:
                if block['x'] <= x <= block['x'] + 2 and block['y'] <= y <= block['y'] + 2:
                    block['hp'] -= 1
                    return True
        return False

    def draw(self) -> None:
        for block in self.blocks:
            if block['hp'] > 0:
                color = 3 if block['hp'] == 3 else 7 if block['hp'] == 2 else 8
                pyxel.rect(block['x'], block['y'], 3, 3, color)

class UFO:
    def __init__(self) -> None:
        if random.choice([True, False]):
            self.x = -16
            self.dir = 1
        else:
            self.x = pyxel.width
            self.dir = -1
        self.y = 10

    def update(self) -> bool:
        self.x += self.dir
        return -16 <= self.x <= pyxel.width

    def draw(self) -> None:
        px = self.x
        py = self.y
        pyxel.circ(px + 8, py + 2, 3, 8)
        pyxel.rect(px + 2, py + 2, 12, 2, 8)

class Game:
    def __init__(self) -> None:
        pyxel.init(160, 120, title="Pyxel Invader")
        self.player = Player()
        self.invaders = InvaderGroup()
        self.enemy_bullets: List[Bullet] = []
        self.barriers = [Barrier(30, 90), Barrier(70, 90), Barrier(110, 90)]
        self.ufo: Optional[UFO] = None
        self.next_ufo = 300
        self.score = 0
        pyxel.run(self.update, self.draw)

    # ------------------- Game Logic -------------------
    def update(self) -> None:
        if not self.invaders.invaders or self.player.lives <= 0:
            if pyxel.btnp(pyxel.KEY_RETURN):
                self.__init__()
            return

        self.player.update()
        self.invaders.update()
        self.update_enemy_bullets()
        self.handle_collisions()
        self.update_ufo()
        if self.invaders.bottom() >= pyxel.height - 16:
            self.player.lives = 0

    def update_enemy_bullets(self) -> None:
        if pyxel.frame_count % 30 == 0 and self.invaders.invaders:
            shooter = random.choice(self.invaders.invaders)
            self.enemy_bullets.append(Bullet(shooter.x + 4, shooter.y + 8, 3))
        self.enemy_bullets = [b for b in self.enemy_bullets if b.update()]

    def handle_collisions(self) -> None:
        # player bullet vs invader or UFO or barriers
        if self.player.bullet:
            b = self.player.bullet
            for inv in self.invaders.invaders:
                if inv.x < b.x < inv.x + 8 and inv.y < b.y < inv.y + 8:
                    self.invaders.invaders.remove(inv)
                    self.score += inv.score
                    self.player.bullet = None
                    break
            if self.player.bullet:
                if self.ufo and self.ufo.x < b.x < self.ufo.x + 16 and self.ufo.y < b.y < self.ufo.y + 6:
                    self.score += 100
                    self.ufo = None
                    self.player.bullet = None
            if self.player.bullet:
                for barrier in self.barriers:
                    if barrier.hit(b.x, b.y):
                        self.player.bullet = None
                        break

        # enemy bullet vs player or barriers
        for bullet in self.enemy_bullets[:]:
            if self.player.x < bullet.x < self.player.x + 8 and pyxel.height - 8 < bullet.y < pyxel.height:
                self.player.lives -= 1
                self.enemy_bullets.remove(bullet)
                continue
            for barrier in self.barriers:
                if barrier.hit(bullet.x, bullet.y):
                    self.enemy_bullets.remove(bullet)
                    break

    def update_ufo(self) -> None:
        if self.ufo:
            if not self.ufo.update():
                self.ufo = None
        else:
            if pyxel.frame_count >= self.next_ufo:
                self.ufo = UFO()
                self.next_ufo = pyxel.frame_count + random.randint(600, 900)

    # ------------------- Drawing -------------------
    def draw(self) -> None:
        pyxel.cls(0)
        self.player.draw()
        self.invaders.draw()
        for bullet in self.enemy_bullets:
            bullet.draw(6)
        for barrier in self.barriers:
            barrier.draw()
        if self.ufo:
            self.ufo.draw()
        pyxel.text(5, 5, f"Score: {self.score}", 7)
        pyxel.text(pyxel.width - 45, 5, f"Lives: {self.player.lives}", 7)
        if self.player.lives <= 0 or not self.invaders.invaders:
            msg = "GAME OVER" if self.player.lives <= 0 else "YOU WIN"
            pyxel.text(pyxel.width // 2 - 20, pyxel.height // 2, msg, 7)
            pyxel.text(pyxel.width // 2 - 40, pyxel.height // 2 + 10, "PRESS ENTER TO RESTART", 7)

# ★ Web用Pyxelランチャー対応：この1行だけでOK！
Game()
