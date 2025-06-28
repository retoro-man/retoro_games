# Simple Othello (Reversi) game for two players on the command line

BOARD_SIZE = 8
EMPTY = '.'
BLACK = 'B'
WHITE = 'W'
DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),          (0, 1),
    (1, -1),  (1, 0), (1, 1)
]

def create_board():
    board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    mid = BOARD_SIZE // 2
    board[mid - 1][mid - 1] = WHITE
    board[mid][mid] = WHITE
    board[mid - 1][mid] = BLACK
    board[mid][mid - 1] = BLACK
    return board

def in_bounds(row, col):
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

def display_board(board):
    print('  ' + ' '.join(chr(ord('a') + i) for i in range(BOARD_SIZE)))
    for i, row in enumerate(board):
        print(f"{i+1} " + ' '.join(row))

def opposite(color):
    return BLACK if color == WHITE else WHITE

def valid_moves(board, color):
    moves = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY:
                continue
            for dr, dc in DIRECTIONS:
                n = 1
                while True:
                    nr, nc = r + dr * n, c + dc * n
                    if not in_bounds(nr, nc) or board[nr][nc] == EMPTY:
                        break
                    if board[nr][nc] == color and n == 1:
                        break
                    if board[nr][nc] == color:
                        moves.append((r, c))
                        break
                    n += 1
    return list(set(moves))

def apply_move(board, row, col, color):
    board[row][col] = color
    for dr, dc in DIRECTIONS:
        captured = []
        nr, nc = row + dr, col + dc
        while in_bounds(nr, nc) and board[nr][nc] == opposite(color):
            captured.append((nr, nc))
            nr += dr
            nc += dc
        if in_bounds(nr, nc) and board[nr][nc] == color:
            for rr, cc in captured:
                board[rr][cc] = color

def score(board):
    black = sum(row.count(BLACK) for row in board)
    white = sum(row.count(WHITE) for row in board)
    return black, white

def board_full(board):
    return all(cell != EMPTY for row in board for cell in row)


def main():
    board = create_board()
    current = BLACK
    while True:
        display_board(board)
        black_score, white_score = score(board)
        print(f"Score - Black: {black_score}, White: {white_score}")
        moves = valid_moves(board, current)
        if not moves:
            if not valid_moves(board, opposite(current)):
                break
            print(f"{current} has no moves. Skipping turn.")
            current = opposite(current)
            continue
        move_str = input(f"{current}'s move (e.g., d3), or 'q' to quit: ")
        if move_str.lower() == 'q':
            break
        if len(move_str) < 2:
            print('Invalid input')
            continue
        col = ord(move_str[0].lower()) - ord('a')
        row = int(move_str[1]) - 1
        if not in_bounds(row, col) or (row, col) not in moves:
            print('Invalid move')
            continue
        apply_move(board, row, col, current)
        current = opposite(current)
        if board_full(board):
            break
    display_board(board)
    black_score, white_score = score(board)
    print(f"Final Score - Black: {black_score}, White: {white_score}")
    if black_score > white_score:
        print('Black wins!')
    elif white_score > black_score:
        print('White wins!')
    else:
        print('It\'s a tie!')

if __name__ == "__main__":
    main()
