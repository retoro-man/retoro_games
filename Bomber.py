# Bomber-Pyxel (Bomberman-like) - Pyxel Web Launcher & local compatible
# Controls:
#   Arrow Keys / WASD : Move (grid step)
#   Z / SPACE         : Drop Bomb
#   P                 : Pause
#   R                 : Restart
#   Q                 : Back to Title
#
# No external assets. Works on Pyxel 1.9+ (Web OK).
# Grid-step movement, bombs with chain reactions, destructible blocks, simple enemy AI, two powerups.

import random
from dataclasses import dataclass

import pyxel
# === Mobile/Gamepad Input Bridge (production) ===
# - Adds a mapping so keyboard checks also react to virtual gamepad (A/B/START/DPAD)
# - Provides a compatible mouse-left constant
# - Keeps existing game logic unchanged

# Mouse left (compat across Pyxel versions)
try:
    MOUSE_LEFT = pyxel.MOUSE_BUTTON_LEFT
except AttributeError:
    MOUSE_LEFT = getattr(pyxel, "MOUSE_LEFT_BUTTON", None)

# Resolve gamepad button constants safely (named + numbered fallback)
def _gp(name, idx=None):
    c = getattr(pyxel, name, None)
    if c is not None:
        return c
    if idx is not None:
        return getattr(pyxel, f"GAMEPAD1_BUTTON_{idx}", None)
    return None

# Prefer named DPAD/A/B/START/SELECT, but fall back to 0..15 indices if needed
_GP = {
    "RIGHT":  _gp("GAMEPAD1_BUTTON_DPAD_RIGHT"),
    "LEFT":   _gp("GAMEPAD1_BUTTON_DPAD_LEFT"),
    "DOWN":   _gp("GAMEPAD1_BUTTON_DPAD_DOWN"),
    "UP":     _gp("GAMEPAD1_BUTTON_DPAD_UP"),
    "A":      _gp("GAMEPAD1_BUTTON_A", 0),
    "B":      _gp("GAMEPAD1_BUTTON_B", 1),
    "START":  _gp("GAMEPAD1_BUTTON_START", 7),
    "SELECT": _gp("GAMEPAD1_BUTTON_SELECT", 6),
}

# Map keyboard codes -> tuple of gamepad buttons that should count as the same input
_KEY_TO_PAD = {
    pyxel.KEY_RIGHT: tuple(c for c in (_GP["RIGHT"],) if c),
    pyxel.KEY_LEFT:  tuple(c for c in (_GP["LEFT"],) if c),
    pyxel.KEY_DOWN:  tuple(c for c in (_GP["DOWN"],) if c),
    pyxel.KEY_UP:    tuple(c for c in (_GP["UP"],) if c),

    # WASD -> DPAD
    pyxel.KEY_D: tuple(c for c in (_GP["RIGHT"],) if c),
    pyxel.KEY_A: tuple(c for c in (_GP["LEFT"],) if c),
    pyxel.KEY_S: tuple(c for c in (_GP["DOWN"],) if c),
    pyxel.KEY_W: tuple(c for c in (_GP["UP"],) if c),

    # Actions / Start / Select
    pyxel.KEY_Z:      tuple(c for c in (_GP["A"], _GP["B"]) if c),
    pyxel.KEY_SPACE:  tuple(c for c in (_GP["A"],) if c),
    pyxel.KEY_RETURN: tuple(c for c in (_GP["START"],) if c),
    pyxel.KEY_P:      tuple(c for c in (_GP["START"],) if c),
    pyxel.KEY_R:      tuple(c for c in (_GP["SELECT"],) if c),
}

# Monkey-patch pyxel.btn/btnp to also check mapped gamepad buttons.
# (Keeps original behavior + adds OR with the mapped pads.)
_orig_btn, _orig_btnp = pyxel.btn, pyxel.btnp
def _btn(code):
    if _orig_btn(code):
        return True
    pads = _KEY_TO_PAD.get(code, ())
    return any(_orig_btn(p) for p in pads)

def _btnp(code):
    if _orig_btnp(code):
        return True
    pads = _KEY_TO_PAD.get(code, ())
    # iOS/Safari may miss a single-frame edge; also allow a slow poll fallback
    return any(_orig_btnp(p) for p in pads) or (pyxel.frame_count % 3 == 0 and any(_orig_btn(p) for p in pads))

pyxel.btn, pyxel.btnp = _btn, _btnp

# Helper: edge-or-held check to make title-start robust on mobile
def _btn_edge(*codes, grace=3):
    return any(pyxel.btnp(c) for c in codes) or (pyxel.frame_count % grace == 0 and any(pyxel.btn(c) for c in codes))
# === end Mobile/Gamepad Input Bridge ===


# --------------- Constants ---------------
TILE = 16
GRID_W = 13
GRID_H = 11
HUD_H = 16
W = GRID_W * TILE
H = GRID_H * TILE + HUD_H
FPS = 60

# Tiles
EMPTY, WALL, SOFT, PWR_FIRE, PWR_BOMB = 0, 1, 2, 4, 5

# Game states
TITLE, PLAYING, GAMEOVER, CLEAR = 0, 1, 2, 3

# Colors (Pyxel palette index)
COL_BG = 1
COL_WALL_1 = 5
COL_WALL_2 = 7
COL_SOFT = 9
COL_PLAYER = 10
COL_BOMB = 0
COL_FIRE = 8
COL_ENEMY = 14
COL_UI = 7
COL_SHADOW = 13

# NEW: Floor colors (avoid black so bombs stand out)
COL_FLOOR_A = 1
COL_FLOOR_B = 2

# Params
BOMB_FUSE_FRAMES = FPS * 2          # 2 seconds
EXPLOSION_FRAMES = int(FPS * 0.35)

# Player grid-step speed (pixels per frame). 16px（1タイル）を 8フレで移動 => 2.0 が目安
PLAYER_STEP_SPEED = 2.0

ENEMY_SPEED = 1.2
MAX_ENEMIES = 6
INITIAL_BOMBS = 1
INITIAL_POWER = 2
MAX_BOMBS_CAP = 8
MAX_POWER_CAP = 8


def seed_for(stage):
    random.seed(1337 + stage * 97)


def clamp(v, a, b):
    return a if v < a else b if v > b else v


def in_bounds(tx, ty):
    return 0 <= tx < GRID_W and 0 <= ty < GRID_H


def to_tile(px, py):
    return int(px // TILE), int((py - HUD_H) // TILE)


def to_pix(tx, ty, center=True):
    x = tx * TILE + (TILE // 2 if center else 0)
    y = ty * TILE + HUD_H + (TILE // 2 if center else 0)
    return x, y


@dataclass
class Bomb:
    tx: int
    ty: int
    fuse: int
    power: int
    owner: str = "player"
    pass_through_owner: bool = True  # （互換のため残置; 実処理は self.pass_tile で制御）


@dataclass
class Flame:
    tiles: list  # list[(tx, ty)]
    timer: int


@dataclass
class Enemy:
    x: float
    y: float
    dirx: int = 0
    diry: int = 0
    alive: bool = True

    def rect(self):
        return (self.x - 6, self.y - 6, self.x + 6, self.y + 6)


@dataclass
class Player:
    x: float
    y: float
    bombs: int = INITIAL_BOMBS
    power: int = INITIAL_POWER
    lives: int = 3
    inv_frames: int = 0
    alive: bool = True

    def rect(self):
        return (self.x - 6, self.y - 6, self.x + 6, self.y + 6)


class Game:
    def __init__(self):
        pyxel.init(W, H, title="Bomber-Pyxel", fps=FPS, display_scale=3)
        self.state = TITLE
        self.stage = 1
        self._init_sounds()
        self.reset_stage()
        pyxel.run(self.update, self.draw)

    # --------------- Setup ---------------
    def _init_sounds(self):
        # 0..7 の音量のみ。pyxel.sound() は非推奨なので pyxel.sounds[] を使用
        pyxel.sounds[0].set("C1C2",      "P", "7",    "N", 10)
        pyxel.sounds[1].set("C3G2C2",    "N", "777",  "N", 8)   # ← "787"→"777"
        pyxel.sounds[2].set("C3E3G3",    "P", "777",  "N", 6)
        pyxel.sounds[3].set("C2",        "N", "7",    "N", 8)
        pyxel.sounds[4].set("C4E4G4C4",  "P", "7777", "N", 12)  # ← C5→C4

    def reset_stage(self):
        self.frame = 0
        self.pause = False
        seed_for(self.stage)
        self.map = [[EMPTY for _ in range(GRID_H)] for _ in range(GRID_W)]
        self._make_walls()
        self._place_soft_blocks()
        self.explosions = []
        self.bombs = []
        self.player = Player(*to_pix(1, 1))
        self._clear_spawn_area()
        self.enemies = self._spawn_enemies()
        self.title_blink = 0

        # 爆弾すり抜けフラグ（自分が置いた直後のタイル）
        self.pass_tile = None

        # --- Grid-step movement state ---
        self.p_moving = False          # 現在、タイル間を移動中か
        self.p_dirx = 0                # 移動方向（-1/0/1）
        self.p_diry = 0
        self.p_target_x = self.player.x  # 目標ピクセル座標（タイルセンター）
        self.p_target_y = self.player.y

    def _make_walls(self):
        for x in range(GRID_W):
            for y in range(GRID_H):
                if x == 0 or y == 0 or x == GRID_W - 1 or y == GRID_H - 1:
                    self.map[x][y] = WALL
                elif x % 2 == 0 and y % 2 == 0:
                    self.map[x][y] = WALL

    def _place_soft_blocks(self):
        for x in range(GRID_W):
            for y in range(GRID_H):
                if self.map[x][y] != EMPTY:
                    continue
                if random.random() < 0.70:
                    self.map[x][y] = SOFT

    def _clear_spawn_area(self):
        for dx, dy in [(0,0),(1,0),(0,1),(1,1),(2,1),(1,2)]:
            tx, ty = 1 + dx, 1 + dy
            if in_bounds(tx, ty) and self.map[tx][ty] == SOFT:
                self.map[tx][ty] = EMPTY

    def _spawn_enemies(self):
        spots = []
        for x in range(1, GRID_W - 1):
            for y in range(1, GRID_H - 1):
                if self.map[x][y] == EMPTY and (x + y) > 6:
                    spots.append((x, y))
        random.shuffle(spots)
        n = clamp(3 + self.stage // 2, 3, MAX_ENEMIES)
        enemies = []
        for i in range(min(n, len(spots))):
            px, py = to_pix(*spots[i])
            e = Enemy(px, py, *random.choice([(1,0),(-1,0),(0,1),(0,-1)]))
            enemies.append(e)
        return enemies

    # --------------- Update Loop ---------------
    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            self.state = TITLE

        if self.state == TITLE:
            self.update_title()
        elif self.state == PLAYING:
            if pyxel.btnp(pyxel.KEY_P):
                self.pause = not self.pause
            if self.pause:
                return
            self.update_playing()
        else:  # GAMEOVER / CLEAR
            self.update_result()

    def update_title(self):

        # --- Early start for mobile (A/B/START or Z/SPACE/ENTER or tap) ---
        if _btn_edge(pyxel.KEY_Z, pyxel.KEY_SPACE, pyxel.KEY_RETURN) \
           or (MOUSE_LEFT is not None and pyxel.btnp(MOUSE_LEFT)):
            try:
                self.state = PLAYING
            except Exception:
                try:
                    self.mode = PLAYING
                except Exception:
                    try:
                        self.scene = PLAYING
                    except Exception:
                        pass
            return
        # --- End early start ---
        self.title_blink = (self.title_blink + 1) % FPS
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN):
            self.state = PLAYING
        if pyxel.btnp(pyxel.KEY_R):
            self.stage = 1
            self.reset_stage()

    def update_result(self):
        if pyxel.btnp(pyxel.KEY_R) or pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            if self.state == CLEAR:
                self.stage += 1
            self.reset_stage()
            self.state = PLAYING

    def update_playing(self):
        self.frame += 1
        if pyxel.btnp(pyxel.KEY_R):
            self.reset_stage()
            return
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            self._place_bomb()

        self._update_player_gridstep()
        self._update_bombs_and_flames()
        self._update_enemies()

        if self.player.lives <= 0:
            self.state = GAMEOVER
        elif all(not e.alive for e in self.enemies):
            self.state = CLEAR
            pyxel.play(0, 4)

    # --------------- Player (grid-step) ---------------
    def _is_solid_tile(self, tx, ty):
        return not in_bounds(tx, ty) or self.map[tx][ty] == WALL

    def _is_blocking_tile(self, tx, ty):
        if not in_bounds(tx, ty):
            return True
        if self.map[tx][ty] in (WALL, SOFT):
            return True
        for b in self.bombs:
            if b.tx == tx and b.ty == ty:
                return True
        return False

    def _bomb_at(self, tx, ty):
        for b in self.bombs:
            if b.tx == tx and b.ty == ty:
                return b
        return None

    def _read_dir_priority(self):
        # まず「押された瞬間(btnp)」を優先、なければ「押されている(btn)」順で採用
        choices = [
            ((1,0), (pyxel.KEY_RIGHT, pyxel.KEY_D)),
            ((-1,0), (pyxel.KEY_LEFT,  pyxel.KEY_A)),
            ((0,1),  (pyxel.KEY_DOWN,  pyxel.KEY_S)),
            ((0,-1), (pyxel.KEY_UP,    pyxel.KEY_W)),
        ]
        # btnp 優先
        for (dx,dy), (k1,k2) in choices:
            if pyxel.btnp(k1) or pyxel.btnp(k2):
                return dx, dy
        # btn のフォールバック
        for (dx,dy), (k1,k2) in choices:
            if pyxel.btn(k1) or pyxel.btn(k2):
                return dx, dy
        return 0, 0

    def _start_step_if_possible(self, dx, dy):
        if dx == 0 and dy == 0:
            return False
        tx, ty = to_tile(self.player.x, self.player.y)
        ntx, nty = tx + dx, ty + dy
        if not in_bounds(ntx, nty):
            return False
        if self._is_blocking_tile(ntx, nty):
            return False
        self.p_moving = True
        self.p_dirx, self.p_diry = dx, dy
        self.p_target_x, self.p_target_y = to_pix(ntx, nty)
        return True

    def _update_player_gridstep(self):
        # すり抜け解除：プレイヤー矩形が爆弾タイル矩形と重ならなくなったら解除
        if self.pass_tile:
            txp, typ = self.pass_tile
            x0r, y0r, x1r, y1r = self.player.x - 6, self.player.y - 6, self.player.x + 6, self.player.y + 6
            bx0, by0 = txp * TILE, typ * TILE + HUD_H
            bx1, by1 = bx0 + TILE, by0 + TILE
            if (x1r <= bx0 or x0r >= bx1 or y1r <= by0 or y0r >= by1):
                self.pass_tile = None

        # 現在タイル中心かを確認（誤差吸収のため丸め）
        tx, ty = to_tile(self.player.x, self.player.y)
        cx, cy = to_pix(tx, ty)
        if abs(self.player.x - cx) < 0.5 and abs(self.player.y - cy) < 0.5:
            self.player.x, self.player.y = cx, cy
            at_center = True
        else:
            at_center = False

        # 次の一歩を開始（中心にいる＆停止中のときにのみ方向入力を読む）
        if not self.p_moving and at_center:
            dx, dy = self._read_dir_priority()
            self._start_step_if_possible(dx, dy)

        # 移動中なら目標センターへ直進
        if self.p_moving:
            spd = PLAYER_STEP_SPEED
            if self.p_dirx != 0:
                nxt = self.player.x + self.p_dirx * spd
                if (self.p_dirx > 0 and nxt >= self.p_target_x) or (self.p_dirx < 0 and nxt <= self.p_target_x):
                    self.player.x = self.p_target_x
                    self.p_moving = False
                else:
                    self.player.x = nxt
            elif self.p_diry != 0:
                nyt = self.player.y + self.p_diry * spd
                if (self.p_diry > 0 and nyt >= self.p_target_y) or (self.p_diry < 0 and nyt <= self.p_target_y):
                    self.player.y = self.p_target_y
                    self.p_moving = False
                else:
                    self.player.y = nyt

            # タイルに到達した瞬間、同じ方向が押されていれば自動で次の一歩を開始
            if not self.p_moving:
                dx, dy = self._read_dir_priority()
                # 同方向が押されているなら連続ステップ（押しっぱなし歩き）
                if (dx, dy) == (self.p_dirx, self.p_diry):
                    if not self._start_step_if_possible(dx, dy):
                        self.p_dirx = self.p_diry = 0
                else:
                    # 別方向入力があればそちらを優先（L字ターン）
                    if not self._start_step_if_possible(dx, dy):
                        self.p_dirx = self.p_diry = 0

        # ピックアップ判定（タイルベースでOK）
        ptx, pty = to_tile(self.player.x, self.player.y)
        tile = self.map[ptx][pty]
        if tile == PWR_BOMB:
            self.map[ptx][pty] = EMPTY
            self.player.bombs = min(MAX_BOMBS_CAP, self.player.bombs + 1)
            pyxel.play(0, 2)
        elif tile == PWR_FIRE:
            self.map[ptx][pty] = EMPTY
            self.player.power = min(MAX_POWER_CAP, self.player.power + 1)
            pyxel.play(0, 2)

        # 炎ダメージ
        if self.player.inv_frames > 0:
            self.player.inv_frames -= 1
        else:
            if self._tile_in_flame(ptx, pty):
                self.player.lives -= 1
                self.player.inv_frames = FPS
                pyxel.play(0, 3)
                self.player.x, self.player.y = to_pix(1, 1)
                # 移動状態をリセット
                self.p_moving = False
                self.p_dirx = self.p_diry = 0
                self.p_target_x, self.p_target_y = self.player.x, self.player.y

    # --------------- Bombs / Explosions ---------------
    def _place_bomb(self):
        # 自分が設置可能上限まで
        if len([b for b in self.bombs if b.owner == "player"]) >= self.player.bombs:
            return
        tx, ty = to_tile(self.player.x, self.player.y)
        if self._is_solid_tile(tx, ty) or self._bomb_at(tx, ty):
            return
        self.bombs.append(Bomb(tx, ty, BOMB_FUSE_FRAMES, self.player.power, "player", True))
        self.pass_tile = (tx, ty)  # 設置タイル在室中はすり抜け
        pyxel.play(0, 0)

    def _explode(self, bomb: Bomb):
        tiles = [(bomb.tx, bomb.ty)]
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            for r in range(1, bomb.power + 1):
                tx, ty = bomb.tx + dx * r, bomb.ty + dy * r
                if not in_bounds(tx, ty):
                    break
                if self.map[tx][ty] == WALL:
                    break
                tiles.append((tx, ty))
                if self.map[tx][ty] == SOFT:
                    break

        self.explosions.append(Flame(tiles, EXPLOSION_FRAMES))
        pyxel.play(0, 1)

        # Destroy soft blocks and maybe spawn powerups
        for tx, ty in tiles:
            if in_bounds(tx, ty) and self.map[tx][ty] == SOFT:
                roll = random.random()
                if roll < 0.06:
                    self.map[tx][ty] = PWR_BOMB
                elif roll < 0.12:
                    self.map[tx][ty] = PWR_FIRE
                else:
                    self.map[tx][ty] = EMPTY

        # Chain reaction
        to_detonate = []
        for other in self.bombs:
            if other is bomb:
                continue
            for tx, ty in tiles:
                if other.tx == tx and other.ty == ty:
                    to_detonate.append(other)
                    break
        for ob in to_detonate:
            if ob in self.bombs:
                self.bombs.remove(ob)
                self._explode(ob)

    def _tile_in_flame(self, tx, ty):
        for f in self.explosions:
            if (tx, ty) in f.tiles:
                return True
        return False

    def _update_bombs_and_flames(self):
        # Fuse
        for b in list(self.bombs):
            b.fuse -= 1
            if b.fuse <= 0:
                self.bombs.remove(b)
                self._explode(b)
        # Flames
        for f in list(self.explosions):
            f.timer -= 1
            if f.timer <= 0:
                self.explosions.remove(f)

    # --------------- Enemies ---------------
    def _rect_vs_blocking(self, x0, y0, x1, y1):
        min_tx, min_ty = to_tile(x0, y0)
        max_tx, max_ty = to_tile(x1, y1)
        for tx in range(min_tx, max_tx + 1):
            for ty in range(min_ty, max_ty + 1):
                if self._is_blocking_tile(tx, ty):
                    bx0, by0 = tx * TILE, ty * TILE + HUD_H
                    bx1, by1 = bx0 + TILE, by0 + TILE
                    if not (x1 <= bx0 or x0 >= bx1 or y1 <= by0 or y0 >= by1):
                        return True
        return False

    def _update_enemies(self):
        for e in self.enemies:
            if not e.alive:
                continue
            tx, ty = to_tile(e.x, e.y)
            if self._tile_in_flame(tx, ty):
                e.alive = False
                continue

            cx, cy = to_pix(tx, ty)
            at_center = abs(e.x - cx) < 1 and abs(e.y - cy) < 1
            spd = ENEMY_SPEED

            if at_center:
                e.x, e.y = cx, cy
                choices = []
                for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                    ntx, nty = tx + dx, ty + dy
                    if not in_bounds(ntx, nty):
                        continue
                    if self._is_blocking_tile(ntx, nty):
                        continue
                    choices.append((dx, dy))
                if (e.dirx, e.diry) in choices and random.random() < 0.7:
                    pass
                else:
                    if choices:
                        e.dirx, e.diry = random.choice(choices)

            nx = e.x + e.dirx * spd
            ny = e.y
            if not self._rect_vs_blocking(nx - 6, ny - 6, nx + 6, ny + 6):
                e.x = nx
            nx = e.x
            ny = e.y + e.diry * spd
            if not self._rect_vs_blocking(nx - 6, ny - 6, nx + 6, ny + 6):
                e.y = ny

        # Touch damage
        for e in self.enemies:
            if not e.alive:
                continue
            if self.player.inv_frames == 0:
                px0, py0, px1, py1 = self.player.rect()
                ex0, ey0, ex1, ey1 = e.rect()
                if not (px1 < ex0 or px0 > ex1 or py1 < ey0 or py0 > ey1):
                    self.player.lives -= 1
                    self.player.inv_frames = FPS
                    pyxel.play(0, 3)
                    self.player.x, self.player.y = to_pix(1, 1)
                    # 移動状態リセット
                    self.p_moving = False
                    self.p_dirx = self.p_diry = 0
                    self.p_target_x, self.p_target_y = self.player.x, self.player.y

    # --------------- Draw ---------------
    def draw(self):
        pyxel.cls(COL_BG)
        if self.state == TITLE:
            self.draw_title()
            return

        self.draw_game()

        if self.state == GAMEOVER:
            self._draw_center_label("GAME OVER - R:Retry / Q:Title", COL_ENEMY)
        elif self.state == CLEAR:
            self._draw_center_label("STAGE CLEAR! - Z/R to Continue", COL_PLAYER)
        elif self.pause:
            self._draw_center_label("PAUSED - P:Resume", COL_UI)

    def draw_title(self):
        # checker background (floor colors)
        for x in range(0, W, TILE):
            for y in range(HUD_H, H, TILE):
                c = COL_FLOOR_A if ((x // TILE) + (y // TILE)) % 2 == 0 else COL_FLOOR_B
                pyxel.rect(x, y, TILE, TILE, c)
        s = "BOMBER-PYXEL"
        self._shadow_text((W - len(s) * 4) // 2, 40, s, 7)
        self._shadow_text((W - 11 * 4) // 2, 60, f"STAGE {self.stage}", 6)
        hint = "PRESS Z / SPACE TO START"
        if (self.title_blink // 30) % 2 == 0:
            self._shadow_text((W - len(hint) * 4) // 2, 88, hint, 10)
        self._shadow_text(16, 120, "ARROWS/WASD: MOVE (grid step)", 6)
        self._shadow_text(16, 130, "Z/SPACE: BOMB, P: PAUSE, R: RESTART, Q: TITLE", 6)

    def draw_game(self):
        # HUD
        pyxel.rect(0, 0, W, HUD_H, 1)
        self._shadow_text(4, 4, f"STAGE {self.stage}", COL_UI)
        self._shadow_text(80, 4, f"LIVES {self.player.lives}", 8)
        self._shadow_text(140, 4, f"BOMB {self.player.bombs}", 12)
        self._shadow_text(190, 4, f"FIRE {self.player.power}", 9)

        # Map
        for x in range(GRID_W):
            for y in range(GRID_H):
                px, py = x * TILE, y * TILE + HUD_H
                t = self.map[x][y]
                if t == WALL:
                    c = COL_WALL_2 if (x + y) % 2 == 0 else COL_WALL_1
                    pyxel.rect(px, py, TILE, TILE, c)
                    pyxel.rect(px, py + TILE - 3, TILE, 3, max(0, c - 1))
                elif t == SOFT:
                    pyxel.rect(px + 1, py + 1, TILE - 2, TILE - 2, COL_SOFT)
                    pyxel.rect(px + 1, py + TILE - 4, TILE - 2, 3, COL_SHADOW)
                elif t == PWR_BOMB:
                    pyxel.rect(px + 3, py + 3, TILE - 6, TILE - 6, 2)
                    self._pixel_plus(px + 8, py + 8, 7)
                elif t == PWR_FIRE:
                    pyxel.circ(px + 8, py + 8, 6, 9)
                    pyxel.circb(px + 8, py + 8, 6, 7)
                else:
                    c = COL_FLOOR_A if (x + y) % 2 == 0 else COL_FLOOR_B
                    pyxel.rect(px, py, TILE, TILE, c)

        # Bombs
        for b in self.bombs:
            bx, by = to_pix(b.tx, b.ty)
            pyxel.circ(bx, by, 5, COL_BOMB)
            if (b.fuse // 6) % 2 == 0:
                pyxel.pset(bx + 3, by - 4, 7)

        # Flames
        for f in self.explosions:
            alpha = clamp(int(7 * (f.timer / EXPLOSION_FRAMES)), 2, 7)
            for (tx, ty) in f.tiles:
                cx, cy = to_pix(tx, ty)
                cx, cy = int(cx), int(cy)
                pyxel.rect(cx - 6, cy - 2, 12, 4, COL_FIRE)  # horizontal
                pyxel.rect(cx - 2, cy - 6, 4, 12, COL_FIRE)  # vertical
                pyxel.circb(cx, cy, 7, alpha)

        # Enemies
        for e in self.enemies:
            if not e.alive:
                continue
            pyxel.circ(int(e.x), int(e.y), 6, COL_ENEMY)
            pyxel.pset(int(e.x) - 2, int(e.y) - 2, 0)
            pyxel.pset(int(e.x) + 2, int(e.y) - 2, 0)

        # Player
        if self.player.alive:
            blink = (self.player.inv_frames // 3) % 2 == 1
            if not blink:
                px, py = int(self.player.x), int(self.player.y)
                pyxel.circ(px, py, 6, COL_PLAYER)
                pyxel.pset(px - 2, py - 2, 0)
                pyxel.pset(px + 2, py - 2, 0)
                pyxel.rect(px - 2, py + 2, 4, 1, 0)

    # --------------- Draw helpers ---------------
    def _draw_center_label(self, text, color):
        tw = len(text) * 4
        self._shadow_text((W - tw) // 2, H // 2 - 4, text, color)

    def _shadow_text(self, x, y, s, c):
        pyxel.text(x + 1, y + 1, s, 0)
        pyxel.text(x, y, s, c)

    def _pixel_plus(self, x, y, c):
        pyxel.pset(x, y, c)
        pyxel.pset(x + 1, y, c)
        pyxel.pset(x - 1, y, c)
        pyxel.pset(x, y + 1, c)
        pyxel.pset(x, y - 1, c)


if __name__ == "__main__":
    Game()
