import pyxel

class App:
    def __init__(self):
        # In newer versions of Pyxel the caption argument was renamed to
        # "title". Using the incorrect argument raises a TypeError, so use
        # the modern "title" keyword instead for compatibility.
        pyxel.init(160, 120, title="Pyxel Invader")
        self.player_x = pyxel.width // 2
        self.bullets = []
        self.enemy_dir = 1
        self.enemies = []
        for y in range(3):
            for x in range(8):
                self.enemies.append([x * 16 + 16, y * 12 + 16])
        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btn(pyxel.KEY_LEFT):
            self.player_x = max(self.player_x - 2, 0)
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.player_x = min(self.player_x + 2, pyxel.width - 8)
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.bullets.append([self.player_x + 4, pyxel.height - 10])

        for bullet in self.bullets:
            bullet[1] -= 4
        self.bullets = [b for b in self.bullets if b[1] > 0]

        edge = False
        for enemy in self.enemies:
            enemy[0] += self.enemy_dir
            if enemy[0] <= 0 or enemy[0] >= pyxel.width - 8:
                edge = True
        if edge:
            self.enemy_dir *= -1
            for enemy in self.enemies:
                enemy[1] += 8

        for bullet in self.bullets:
            for enemy in self.enemies:
                if (enemy[0] < bullet[0] < enemy[0] + 8 and
                        enemy[1] < bullet[1] < enemy[1] + 8):
                    self.enemies.remove(enemy)
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    break

    def draw(self):
        pyxel.cls(0)
        pyxel.rect(self.player_x, pyxel.height - 8, 8, 8, 9)
        for bullet in self.bullets:
            pyxel.rect(bullet[0], bullet[1], 1, 4, 7)
        for enemy in self.enemies:
            pyxel.rect(enemy[0], enemy[1], 8, 8, 8)

if __name__ == "__main__":
    App()
