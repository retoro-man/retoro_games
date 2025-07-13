import pyxel

class VirtualController:
    """Simple on-screen controller for touch devices."""

    def __init__(self, game_w: int, game_h: int):
        self.game_w = game_w
        self.game_h = game_h
        self._prev = {'a': False, 'b': False, 'x': False, 'y': False}
        self.reset()

    def reset(self) -> None:
        self.left = self.right = self.up = self.down = False
        self.a = self.b = self.x = self.y = False
        self.a_p = self.b_p = self.x_p = self.y_p = False

    def orientation(self) -> str:
        return 'portrait' if pyxel.height > pyxel.width else 'landscape'

    def _in_rect(self, x: int, y: int, r: tuple[int, int, int, int]) -> bool:
        x1, y1, x2, y2 = r
        return x1 <= x <= x2 and y1 <= y <= y2

    def _in_circle(self, x: int, y: int, cx: int, cy: int, rad: int) -> bool:
        return (x - cx) ** 2 + (y - cy) ** 2 <= rad * rad

    def update(self, off_x: int = 0, off_y: int = 0) -> None:
        self.reset()
        mx, my = pyxel.mouse_x, pyxel.mouse_y
        pressed = pyxel.btn(pyxel.MOUSE_LEFT)
        orient = self.orientation()

        if orient == 'portrait':
            ctrl_top = off_y + self.game_h
            h = pyxel.height - ctrl_top
            d_cx = off_x + 30
            d_cy = ctrl_top + h // 2
            b_cx = off_x + self.game_w - 30
            b_cy = d_cy
        else:
            left_w = off_x
            d_cx = left_w // 2
            d_cy = off_y + self.game_h // 2
            b_cx = off_x + self.game_w + left_w + left_w // 2
            b_cy = d_cy

        size = 8
        if pressed:
            if self._in_rect(mx, my, (d_cx - size, d_cy - 3*size, d_cx + size, d_cy - size)):
                self.up = True
            if self._in_rect(mx, my, (d_cx - size, d_cy + size, d_cx + size, d_cy + 3*size)):
                self.down = True
            if self._in_rect(mx, my, (d_cx - 3*size, d_cy - size, d_cx - size, d_cy + size)):
                self.left = True
            if self._in_rect(mx, my, (d_cx + size, d_cy - size, d_cx + 3*size, d_cy + size)):
                self.right = True
            r = 8
            if self._in_circle(mx, my, b_cx + 2*r, b_cy, r):
                self.a = True
            if self._in_circle(mx, my, b_cx, b_cy + 2*r, r):
                self.b = True
            if self._in_circle(mx, my, b_cx - 2*r, b_cy, r):
                self.x = True
            if self._in_circle(mx, my, b_cx, b_cy - 2*r, r):
                self.y = True

        for n in ['a', 'b', 'x', 'y']:
            cur = getattr(self, n)
            setattr(self, f'{n}_p', cur and not self._prev[n])
            self._prev[n] = cur

    def draw(self, off_x: int = 0, off_y: int = 0) -> None:
        orient = self.orientation()
        if orient == 'portrait':
            ctrl_top = off_y + self.game_h
            h = pyxel.height - ctrl_top
            d_cx = off_x + 30
            d_cy = ctrl_top + h // 2
            b_cx = off_x + self.game_w - 30
            b_cy = d_cy
        else:
            left_w = off_x
            d_cx = left_w // 2
            d_cy = off_y + self.game_h // 2
            b_cx = off_x + self.game_w + left_w + left_w // 2
            b_cy = d_cy
        size = 8
        pyxel.rect(d_cx - size, d_cy - 3*size, 2*size, 2*size, 13)
        pyxel.rect(d_cx - size, d_cy + size, 2*size, 2*size, 13)
        pyxel.rect(d_cx - 3*size, d_cy - size, 2*size, 2*size, 13)
        pyxel.rect(d_cx + size, d_cy - size, 2*size, 2*size, 13)
        pyxel.rect(d_cx - size, d_cy - size, 2*size, 2*size, 5)
        r = 8
        pyxel.circ(b_cx + 2*r, b_cy, r, 8)
        pyxel.circ(b_cx, b_cy + 2*r, r, 8)
        pyxel.circ(b_cx - 2*r, b_cy, r, 8)
        pyxel.circ(b_cx, b_cy - 2*r, r, 8)
