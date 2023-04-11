# .ComicReader

ComicReader is a comic manager + viewer. This app is multiplatform, and is written in Python 3.11. It uses PyQt6 for the GUI.

## Installation

### 1) Download the project

```bash
git clone
```

### 2) Install the dependencies

```bash
pip install -r requirements.txt
# or
pip3 install -r requirements.txt
```

### 3) Customize the app

You need to update some paths in ComicReader.py. You can find them by searching for "UPDATE THIS". They are :

- `WORKING_DIR` : The directory of the project, so it can find itself and its dependencies. Needed for the `import` statements if you run the app outside of the project directory, like using the `.desktop` file on Linux.
- `COMIC_DIR` : The directory where your comics are stored. This is where the app will look for comics to display.

## Example `COMIC_DIR` structure

```bash
COMIC_DIR/
├── Comic 1/
│   ├── Chapter 1.cbz
│   ├── Chapter 2.cbz
│   └── Chapter 3.cbz
├── Comic 2/
│   ├── Chapter 1.cbz
│   ├── Chapter 2.cbz
│   └── Chapter 3.cbz
└── Comic 3/
    ├── Chapter 1.cbz
    ├── Chapter 2.cbz
    └── Chapter 3.cbz
```

The app wil display the comics alphabetically (a, b, c, ...), and the chapters in natural order (1, 2, 3, ..., 10, 11, 12, ...).

## Shortcuts

### Main window

- `Arrow keys` : Navigate between comics / chapters.
- `Enter | Space` : Open the selected comic / chapter.
- `Ctrl + Q | Ctrl + W` : Close the app.
- `R` : Read the selected Chapter.
- `N` : Read the next Chapter.

### Viewer

- `Esc | Ctrl + Q | Ctrl + W` : Close the viewer.
- `Left | Up | Page Up` : Scroll up.
- `Right | Down | Page Down` : Scroll down.
- `Home` : Scroll to the top.
- `End` : Scroll to the bottom.
- `P` : Go to the previous chapter.
- `N` : Go to the next chapter.
- `F | F11` : Toggle fullscreen.
- `Mouse wheel` : Scroll up / down.
- `Mouse click` : Scroll up / down, depending on the position of the click. If the click is on the left half of the screen, it will scroll up. If it's on the right half, it will scroll down.