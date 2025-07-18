# Simple Mario-like side scroller using Pyxel

import pyxel

TILE_SIZE = 8
WIDTH = 160
HEIGHT = 120
PLAYER_W = 8
PLAYER_H = 8

LEVEL = [
    '................................................................................',
    '................................................................................',
    '................................................................................',
    '................................................................................',
    '................................................................................',
    '.................###....................###......................................',
    '................................................................................',
    '.......................###......................E...............................',
    '................................................................................',
    '......###..............................###......................................',
    '................................................................................',
    '###############################....############################################',
    '................................................................................',
    '................................................................................',
    '################################################################################'
]

LEVEL_WIDTH = len(LEVEL[0]) * TILE_SIZE


def tile_at(tx: int, ty: int) -> str:
    if 0 <= ty < len(LEVEL) and 0 <= tx < len(LEVEL[0]):
        return LEVEL[ty][tx]
    return '#'


def is_solid(tile: str) -> bool:
    return tile == '#'


class Enemy:
    def __init__(self, x1: int, x2: int, y: int) -> None:
        self.x1 = x1
        self.x2 = x2
        self.x = x1
        self.y = y
        self.dir = 1

    def update(self) -> None:
        self.x += self.dir * 0.5
        if self.x < self.x1 or self.x > self.x2:
            self.dir *= -1

    def draw(self, cam_x: int) -> None:
        pyxel.rect(self.x - cam_x, self.y, PLAYER_W, PLAYER_H, 8)


class Player:
    def __init__(self) -> None:
        self.x = 16
        self.y = HEIGHT - PLAYER_H - 16
        self.dx = 0.0
        self.dy = 0.0
        self.on_ground = False

    def update(self) -> None:
        self.dx = 0
        if pyxel.btn(pyxel.KEY_LEFT):
            self.dx = -1.5
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.dx = 1.5
        if self.on_ground and (pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_UP)):
            self.dy = -4
            self.on_ground = False
        self.dy += 0.2
        if self.dy > 3:
            self.dy = 3

        # horizontal movement
        new_x = self.x + self.dx
        if self.dx > 0:
            tx = int((new_x + PLAYER_W - 1) // TILE_SIZE)
            for ty in range(int(self.y) // TILE_SIZE, int((self.y + PLAYER_H - 1) // TILE_SIZE) + 1):
                if is_solid(tile_at(tx, ty)):
                    new_x = tx * TILE_SIZE - PLAYER_W
                    break
        elif self.dx < 0:
            tx = int(new_x // TILE_SIZE)
            for ty in range(int(self.y) // TILE_SIZE, int((self.y + PLAYER_H - 1) // TILE_SIZE) + 1):
                if is_solid(tile_at(tx, ty)):
                    new_x = (tx + 1) * TILE_SIZE
                    break
        self.x = new_x

        # vertical movement
        new_y = self.y + self.dy
        if self.dy > 0:
            ty = int((new_y + PLAYER_H - 1) // TILE_SIZE)
            for tx in range(int(self.x) // TILE_SIZE, int((self.x + PLAYER_W - 1) // TILE_SIZE) + 1):
                if is_solid(tile_at(tx, ty)):
                    new_y = ty * TILE_SIZE - PLAYER_H
                    self.dy = 0
                    self.on_ground = True
                    break
        elif self.dy < 0:
            ty = int(new_y // TILE_SIZE)
            for tx in range(int(self.x) // TILE_SIZE, int((self.x + PLAYER_W - 1) // TILE_SIZE) + 1):
                if is_solid(tile_at(tx, ty)):
                    new_y = (ty + 1) * TILE_SIZE
                    self.dy = 0
                    break
        self.y = new_y

    def draw(self, cam_x: int) -> None:
        pyxel.rect(self.x - cam_x, self.y, PLAYER_W, PLAYER_H, 9)


class Game:
    def __init__(self) -> None:
        pyxel.init(WIDTH, HEIGHT, title="Pyxel Mario")
        self.player = Player()
        self.enemy = Enemy(220, 260, HEIGHT - PLAYER_H - 16)
        self.win = False
        self.game_over = False
        pyxel.run(self.update, self.draw)

    def update(self) -> None:
        if self.win or self.game_over:
            if pyxel.btnp(pyxel.KEY_RETURN):
                self.__init__()
            return
        self.player.update()
        self.enemy.update()
        if abs(self.player.x - self.enemy.x) < PLAYER_W and abs(self.player.y - self.enemy.y) < PLAYER_H:
            self.game_over = True
        if self.player.x > LEVEL_WIDTH - 2 * TILE_SIZE:
            self.win = True

    def draw(self) -> None:
        cam_x = max(0, min(int(self.player.x) - WIDTH // 2, LEVEL_WIDTH - WIDTH))
        pyxel.cls(6)
        for y, row in enumerate(LEVEL):
            for x, tile in enumerate(row):
                px = x * TILE_SIZE - cam_x
                py = y * TILE_SIZE
                if tile == '#':
                    pyxel.rect(px, py, TILE_SIZE, TILE_SIZE, 3)
                elif tile == 'E':
                    pyxel.rect(px, py, PLAYER_W, PLAYER_H, 8)
        self.player.draw(cam_x)
        self.enemy.draw(cam_x)
        if self.win:
            pyxel.text(WIDTH // 2 - 20, HEIGHT // 2, "YOU WIN", 7)
            pyxel.text(WIDTH // 2 - 40, HEIGHT // 2 + 10, "PRESS ENTER TO RESTART", 7)
        if self.game_over:
            pyxel.text(WIDTH // 2 - 20, HEIGHT // 2, "GAME OVER", 7)
            pyxel.text(WIDTH // 2 - 40, HEIGHT // 2 + 10, "PRESS ENTER TO RESTART", 7)


if __name__ == "__main__":
    Game()
