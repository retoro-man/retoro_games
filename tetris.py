# Simple Tetris using Pyxel
import random
try:
    import pyxel
except ImportError:
    print('Pyxel is required to run this game.')
    raise

WIDTH = 10
HEIGHT = 20
BLOCK_SIZE = 8

# Tetris shapes (4x4 matrices)
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1],
     [1, 1]],         # O
    [[0,1,0],
     [1,1,1]],        # T
    [[1,0,0],
     [1,1,1]],        # J
    [[0,0,1],
     [1,1,1]],        # L
    [[1,1,0],
     [0,1,1]],        # S
    [[0,1,1],
     [1,1,0]]         # Z
]

COLORS = [1, 2, 3, 4, 5, 6, 7]


def rotate(shape):
    return [list(row) for row in zip(*shape[::-1])]


class Piece:
    def __init__(self):
        self.shape = random.choice(SHAPES)
        self.color = random.choice(COLORS)
        self.x = WIDTH // 2 - len(self.shape[0]) // 2
        self.y = 0

    def rotate(self):
        new_shape = rotate(self.shape)
        self.shape = new_shape


class Tetris:
    def __init__(self):
        # 'caption' was renamed to 'title' in newer versions of Pyxel
        pyxel.init(WIDTH * BLOCK_SIZE, HEIGHT * BLOCK_SIZE, title="Pyxel Tetris")
        self.board = [[0 for _ in range(WIDTH)] for _ in range(HEIGHT)]
        self.piece = Piece()
        self.tick = 0
        pyxel.run(self.update, self.draw)

    def collision(self, nx, ny, shape=None):
        if shape is None:
            shape = self.piece.shape
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    px = nx + x
                    py = ny + y
                    if px < 0 or px >= WIDTH or py >= HEIGHT:
                        return True
                    if py >= 0 and self.board[py][px]:
                        return True
        return False

    def merge_piece(self):
        for y, row in enumerate(self.piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    px = self.piece.x + x
                    py = self.piece.y + y
                    if 0 <= py < HEIGHT:
                        self.board[py][px] = self.piece.color
        self.clear_lines()
        self.piece = Piece()
        if self.collision(self.piece.x, self.piece.y):
            # Game over
            self.board = [[0 for _ in range(WIDTH)] for _ in range(HEIGHT)]

    def clear_lines(self):
        new_board = [row for row in self.board if any(cell == 0 for cell in row)]
        lines_cleared = HEIGHT - len(new_board)
        for _ in range(lines_cleared):
            new_board.insert(0, [0 for _ in range(WIDTH)])
        self.board = new_board

    def update(self):
        self.tick += 1
        if pyxel.btnp(pyxel.KEY_LEFT) and not self.collision(self.piece.x - 1, self.piece.y):
            self.piece.x -= 1
        if pyxel.btnp(pyxel.KEY_RIGHT) and not self.collision(self.piece.x + 1, self.piece.y):
            self.piece.x += 1
        if pyxel.btnp(pyxel.KEY_DOWN):
            while not self.collision(self.piece.x, self.piece.y + 1):
                self.piece.y += 1
            self.merge_piece()
        if pyxel.btnp(pyxel.KEY_UP):
            new_shape = rotate(self.piece.shape)
            if not self.collision(self.piece.x, self.piece.y, new_shape):
                self.piece.shape = new_shape
        if self.tick % 30 == 0:
            if not self.collision(self.piece.x, self.piece.y + 1):
                self.piece.y += 1
            else:
                self.merge_piece()

    def draw(self):
        pyxel.cls(0)
        # Draw board
        for y, row in enumerate(self.board):
            for x, cell in enumerate(row):
                if cell:
                    pyxel.rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE, cell)
        # Draw current piece
        for y, row in enumerate(self.piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    px = (self.piece.x + x) * BLOCK_SIZE
                    py = (self.piece.y + y) * BLOCK_SIZE
                    pyxel.rect(px, py, BLOCK_SIZE, BLOCK_SIZE, self.piece.color)


if __name__ == "__main__":
    Tetris()
