# puni-test

This repository contains a simple Pyxel-based invader game written with the
Pyxel library.  Use the arrow keys to move the player at the bottom of the
screen and press the space bar to shoot upward.  Protect yourself with the
barriers, avoid enemy fire and try to shoot down the occasional UFO for bonus
points.  If all lives are lost or the invaders reach the bottom of the screen
the game ends.  Press the return key to start a new round.

Install the Pyxel library first:

```bash
pip install pyxel
```

Run the game with:

```bash
python invader.py
```

## Packaging for the Web

Pyxel can export games as a static HTML page. Install Pyxel with its web
dependencies and run the packaging command:

```bash
pip install "pyxel[full]"
pyxel package invader.py
```

The command creates a `dist/` directory containing `index.html` and support
files. Open `dist/index.html` locally or upload the directory to any static
hosting service.

### Playing in Pyxel Web Launcher

You can also play the game directly in your browser without hosting it. Visit
the [Pyxel Web Launcher](https://kitao.github.io/pyxel/wasm/launcher/) and
upload `invader.py` or the contents of the `dist/` directory created by the
packaging command.

### Hosting on GitHub Pages

Create a branch such as `gh-pages`, copy the contents of `dist/` to it and
push. Enable GitHub Pages in the repository settings to share the game online.
