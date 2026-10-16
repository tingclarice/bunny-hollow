# Bunny Hollow

A Pygame Quoridor prototype. The first milestone is a local two-player game;
the AI and search algorithms are planned but not implemented yet.

## Bootstrap

Run the folder setup script from the project root:

```bash
bash setup_project.sh
```

Install the listed dependencies with:

```bash
python -m pip install -r requirements.txt
```

Run the application with:

```bash
python main.py
```

## Play the prototype

```bash
python main.py
```

The board and rabbit pawns are drawn with Pygame shapes, so no external art
assets are required for this prototype. Click a highlighted square to move.
Press **W** to enter wall placement, **R** to rotate the wall, and click the
board to place it. **Backspace** undoes the last move, **N** starts a new game,
**F11** toggles fullscreen, and **Esc** quits.

This milestone supports two local players and the core pawn/wall rules. It
does not yet include a computer opponent, menus, sound, or the planned
Minimax/A*/BFS modules.

Run the board-rule tests with:

```bash
pytest
```
