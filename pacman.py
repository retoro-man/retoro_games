import pyxel

TILE_SIZE = 8
WIDTH = TILE_SIZE * 20
HEIGHT = TILE_SIZE * 15

BOARD_TEMPLATE = [
    "####################",
    "#........##........#",
    "#.####.#....#.####.#",
    "#.#..#.#.##.#.#..#.#",
    "#.#..#.#.##.#.#..#.#",
    "#.####.#.##.#.####.#",
    "#........##........#",
    "########.##.########",
    "#........##........#",
    "#.####.#....#.####.#",
    "#.#..#.#.##.#.#..#.#",
    "#.#..#.#.##.#.#..#.#",
    "#.####.#.##.#.####.#",
    "#........##........#",
    "####################",
]

DIRECTIONS = {
    pyxel.KEY_UP: (0, -1),
    pyxel.KEY_DOWN: (0, 1),
    pyxel.KEY_LEFT: (-1, 0),
    pyxel.KEY_RIGHT: (1, 0),
}

class Character:
    def __init__(self, tile_x: int, tile_y: int):
        self.x = tile_x * TILE_SIZE + TILE_SIZE // 2
        self.y = tile_y * TILE_SIZE + TILE_SIZE // 2
        self.target_x = self.x
        self.target_y = self.y
        self.dx = 0
        self.dy = 0

    def move_towards_target(self, speed: int = 1) -> None:
        if self.x < self.target_x:
            self.x = min(self.x + speed, self.target_x)
        elif self.x > self.target_x:
            self.x = max(self.x - speed, self.target_x)
        if self.y < self.target_y:
            self.y = min(self.y + speed, self.target_y)
        elif self.y > self.target_y:
            self.y = max(self.y - speed, self.target_y)

    def at_target(self) -> bool:
        return self.x == self.target_x and self.y == self.target_y

class Game:
    def __init__(self) -> None:
        pyxel.init(WIDTH, HEIGHT, title="Pyxel Pac-Man")
        self.reset()
        pyxel.run(self.update, self.draw)

    def reset(self) -> None:
        self.board = [list(row) for row in BOARD_TEMPLATE]
        self.pellets = sum(row.count('.') for row in BOARD_TEMPLATE)
        self.player = Character(1, 1)
        self.ghost = Character(18, 13)
        self.game_over = False

    def tile_at(self, tx: int, ty: int) -> str:
        if 0 <= ty < len(self.board) and 0 <= tx < len(self.board[0]):
            return self.board[ty][tx]
        return '#'

    def update(self) -> None:
        if self.game_over:
            if pyxel.btnp(pyxel.KEY_RETURN):
                self.reset()
            return
        self.update_player()
        self.update_ghost()
        self.check_collisions()

    def update_player(self) -> None:
        if self.player.at_target():
            for key, (dx, dy) in DIRECTIONS.items():
                if pyxel.btn(key):
                    tx = self.player.x // TILE_SIZE + dx
                    ty = self.player.y // TILE_SIZE + dy
                    if self.tile_at(tx, ty) != '#':
                        self.player.dx, self.player.dy = dx, dy
                        self.player.target_x = tx * TILE_SIZE + TILE_SIZE // 2
                        self.player.target_y = ty * TILE_SIZE + TILE_SIZE // 2
                        break
        self.player.move_towards_target(2)
        if self.player.at_target():
            tx = self.player.x // TILE_SIZE
            ty = self.player.y // TILE_SIZE
            if self.board[ty][tx] == '.':
                self.board[ty][tx] = ' '
                self.pellets -= 1
                if self.pellets == 0:
                    self.game_over = True

    def update_ghost(self) -> None:
        if self.ghost.at_target():
            tx = self.ghost.x // TILE_SIZE
            ty = self.ghost.y // TILE_SIZE
            options = []
            for dx, dy in DIRECTIONS.values():
                if (-dx, -dy) == (self.ghost.dx, self.ghost.dy):
                    continue
                if self.tile_at(tx + dx, ty + dy) != '#':
                    options.append((dx, dy))
            if options:
                def score(opt):
                    dx, dy = opt
                    px = self.player.x // TILE_SIZE
                    py = self.player.y // TILE_SIZE
                    return abs(px - (tx + dx)) + abs(py - (ty + dy))
                best = min(options, key=score)
                self.ghost.dx, self.ghost.dy = best
                self.ghost.target_x = (tx + self.ghost.dx) * TILE_SIZE + TILE_SIZE // 2
                self.ghost.target_y = (ty + self.ghost.dy) * TILE_SIZE + TILE_SIZE // 2
        self.ghost.move_towards_target(1)

    def check_collisions(self) -> None:
        if abs(self.player.x - self.ghost.x) < TILE_SIZE // 2 and abs(self.player.y - self.ghost.y) < TILE_SIZE // 2:
            self.game_over = True

    def draw(self) -> None:
        pyxel.cls(0)
        for y, row in enumerate(self.board):
            for x, cell in enumerate(row):
                if cell == '#':
                    pyxel.rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE, 1)
                elif cell == '.':
                    pyxel.pset(x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2, 7)
        pyxel.circ(self.player.x, self.player.y, 3, 10)
        pyxel.circ(self.ghost.x, self.ghost.y, 3, 8)
        if self.game_over:
            msg = "GAME CLEAR" if self.pellets == 0 else "GAME OVER"
            pyxel.text(WIDTH // 2 - 20, HEIGHT // 2, msg, 7)
            pyxel.text(WIDTH // 2 - 40, HEIGHT // 2 + 10, "PRESS ENTER TO RESTART", 7)

if __name__ == '__main__':
    Game()
