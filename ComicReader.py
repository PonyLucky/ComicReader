#!/usr/bin/env python
import os
import sys
import re
import subprocess
import shutil
from PySide6 import QtCore, QtWidgets, QtGui

# --- UPDATE THIS ---
WORKING_DIR = '/home/louis/.ComicReader/'
# -------------------
SETTINGS_PATH = os.path.join(WORKING_DIR, 'ComicReader.ini')

# Set working directory
os.chdir(WORKING_DIR)

from src.settings import Settings
from src.comic import Comic
from src.viewer import Viewer


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Comic Reader')
        self.setWindowIcon(QtGui.QIcon('images/ComicReader.png'))
        self.resize(1000, 600)
        self.keyPressEvent = self.key_press
        self.settings = Settings(SETTINGS_PATH)

        self.comic_list = QtWidgets.QListWidget()
        self.comic_list.itemClicked.connect(self.comic_clicked)
        self.comic_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.comic_list.customContextMenuRequested.connect(
            self.comic_context_menu
        )
        self.comic_list.setSortingEnabled(True)
        self.comic_list.keyPressEvent = self.comic_list_key_press
        self.comic_list.setFont(QtGui.QFont('Noto Sans', 12))

        self.chapter_list = QtWidgets.QListWidget()
        self.chapter_list.itemClicked.connect(self.chapter_clicked)
        self.chapter_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.chapter_list.customContextMenuRequested.connect(
            self.chapter_context_menu
        )
        self.chapter_list.keyPressEvent = self.chapter_list_key_press
        self.chapter_list.setFont(QtGui.QFont('Noto Sans', 12))

        # Image viewer will be in a new window
        self.viewer = Viewer(
            WORKING_DIR=WORKING_DIR,
            settings=self.settings
        )

        self.splitter = QtWidgets.QSplitter()
        self.splitter.addWidget(self.comic_list)
        self.splitter.addWidget(self.chapter_list)
        self.setCentralWidget(self.splitter)

        self.load_comics()
        self.current_comic = None

        # Load last read if any
        if self.settings['last_read']:
            for i in range(self.comic_list.count()):
                text = self.comic_list.item(i).text()
                if text == self.settings['last_read']:
                    self.comic_list.setCurrentRow(i)
                    self.comic_clicked()
                    break
            self.comic_clicked()

        # Show main window
        self.showMaximized()

        # Show image viewer if there is a last chapter
        if self.settings['last_read']:
            # Load last chapter if any
            last_chapter = self.current_comic.get_last_chapter()
            if last_chapter:
                self.chapter_clicked()

    def load_comics(self):
        """Load comics from the comic directory."""
        self.comic_list.clear()
        self.chapter_list.clear()
        # List directories only
        self.comic_list.addItems(
            [
                comic
                for comic in os.listdir(self.settings['comics_dir'])
                if os.path.isdir(os.path.join(
                    self.settings['comics_dir'],
                    comic
                ))
            ]
        )
        # Sort comics
        self.comic_list.sortItems()
        print("[DEBUG] Load comics")
        print("- nb comics: {}".format(self.comic_list.count()))

    @QtCore.Slot()
    def comic_clicked(self):
        """Load chapters for a comic."""
        self.chapter_list.clear()
        self.current_comic = Comic(
            os.path.join(
                self.settings['comics_dir'],
                self.comic_list.currentItem().text()
            )
        )
        # List .cbz files
        chapter_list = [
            chapter
            for chapter in os.listdir(self.current_comic.path)
            if chapter.endswith('.cbz')
        ]
        # Sort chapters
        chapter_list.sort(key=lambda x: int(re.findall(r'\d+', x)[0]))
        # Check if there are chapters in ".5", if so, move them to the
        # next position
        is_half = False
        for index, chapter in enumerate(chapter_list):
            if chapter.endswith('.5.cbz'):
                if not is_half:
                    number = int(re.findall(r'\d+', chapter)[0])
                    next_number = int(
                        re.findall(r'\d+', chapter_list[index + 1])[0]
                    )
                    # Move if next chapter has same number
                    if number == next_number:
                        chapter_list.insert(index + 2, chapter)
                        chapter_list.remove(chapter)
                        is_half = True
                else:
                    is_half = False
        self.chapter_list.addItems(chapter_list)
        # Select last chapter
        last_chapter = self.current_comic.get_last_chapter()
        if last_chapter:
            for index in range(self.chapter_list.count()):
                if self.chapter_list.item(index).text() == last_chapter:
                    self.chapter_list.setCurrentRow(index)
                    break
                else:
                    # Set read chapters to gray
                    self.chapter_list.item(index).setForeground(
                        QtGui.QColor(128, 128, 128)
                    )
        # Set focus on chapter list
        self.chapter_list.setFocus()
        # Save settings
        self.settings['last_read'] = self.comic_list.currentItem().text()
        self.settings.save()
        print("[DEBUG] Load chapters")
        print("- comic: {}".format(self.current_comic.path))
        print("- nb chapters: {}".format(self.chapter_list.count()))
        print("- last chapter: {}".format(last_chapter))

    @QtCore.Slot()
    def chapter_clicked(self):
        """Open a chapter in the viewer."""
        self.viewer.set_settings(self.settings)
        self.viewer.chapter_clicked(
            self.current_comic,
            self.chapter_list
        )

    @QtCore.Slot()
    def comic_context_menu(self, position):
        """Context menu for comics."""
        menu = QtWidgets.QMenu()
        # Add "Open in file manager" action
        open_in_file_manager_action = QtGui.QAction(
            'Open in file manager',
            self
        )
        open_in_file_manager_action.triggered.connect(
            self.open_in_file_manager
        )
        menu.addAction(open_in_file_manager_action)

        menu.exec(self.comic_list.mapToGlobal(position))

    @QtCore.Slot()
    def chapter_context_menu(self, position):
        """Context menu for chapters."""
        menu = QtWidgets.QMenu()
        # Add "Open in file manager" action
        open_in_file_manager_action = QtGui.QAction(
            'Open in file manager',
            self
        )
        open_in_file_manager_action.triggered.connect(
            self.open_in_file_manager
        )
        menu.addAction(open_in_file_manager_action)

        menu.exec(self.chapter_list.mapToGlobal(position))

    @QtCore.Slot()
    def open_in_file_manager(self):
        """Open the current comic in the file manager."""
        if self.current_comic is not None:
            subprocess.Popen(
                ['xdg-open', self.current_comic.path]
            )

    @QtCore.Slot()
    def key_press(self, event):
        """Handle key press events."""
        # Handle Esc, Ctrl+Q, Ctrl+W -> quit
        if (
            event.key() == QtCore.Qt.Key_Escape
            or (
                event.key() == QtCore.Qt.Key_Q
                and event.modifiers() == QtCore.Qt.ControlModifier
            )
            or (
                event.key() == QtCore.Qt.Key_W
                and event.modifiers() == QtCore.Qt.ControlModifier
            )
        ):
            self.close()

    @QtCore.Slot()
    def comic_list_key_press(self, event):
        """Handle key press events."""
        # Handle Enter, Space -> trigger comic_clicked
        if (
            event.key() == QtCore.Qt.Key_Enter
            or event.key() == QtCore.Qt.Key_Return
            or event.key() == QtCore.Qt.Key_Space
        ):
            self.comic_clicked()
        # Handle arrow keys -> select next/previous comic
        # Left, Up -> select previous comic
        elif (
            event.key() == QtCore.Qt.Key_Left
            or event.key() == QtCore.Qt.Key_Up
        ):
            # If not first comic, select previous comic
            if self.comic_list.currentRow() > 0:
                self.comic_list.setCurrentRow(
                    self.comic_list.currentRow() - 1
                )
        # Right, Down -> select next comic
        elif (
            event.key() == QtCore.Qt.Key_Right
            or event.key() == QtCore.Qt.Key_Down
        ):
            # If not last comic, select next comic
            if self.comic_list.currentRow() < self.comic_list.count() - 1:
                self.comic_list.setCurrentRow(
                    self.comic_list.currentRow() + 1
                )
        # Deserve normal key_press event
        else:
            self.key_press(event)

    @QtCore.Slot()
    def chapter_list_key_press(self, event):
        """Handle key press events."""
        # Handle Enter, Space -> trigger chapter_clicked
        if (
            event.key() == QtCore.Qt.Key_Enter
            or event.key() == QtCore.Qt.Key_Return
            or event.key() == QtCore.Qt.Key_Space
        ):
            self.chapter_clicked()
        # Handle arrow keys -> select next/previous chapter
        # Left, Up -> select previous chapter
        elif (
            event.key() == QtCore.Qt.Key_Left
            or event.key() == QtCore.Qt.Key_Up
        ):
            # If not first chapter, select previous chapter
            if self.chapter_list.currentRow() > 0:
                self.chapter_list.setCurrentRow(
                    self.chapter_list.currentRow() - 1
                )
        # Right, Down -> select next chapter
        elif (
            event.key() == QtCore.Qt.Key_Right
            or event.key() == QtCore.Qt.Key_Down
        ):
            # If not last chapter, select next chapter
            if self.chapter_list.currentRow() < self.chapter_list.count() - 1:
                self.chapter_list.setCurrentRow(
                    self.chapter_list.currentRow() + 1
                )
        # Handle R to read current chapter
        elif event.key() == QtCore.Qt.Key_R:
            self.chapter_clicked()
        # Handle N to read next chapter
        elif event.key() == QtCore.Qt.Key_N:
            # If not last chapter, select next chapter
            if self.chapter_list.currentRow() < self.chapter_list.count() - 1:
                self.chapter_list.setCurrentRow(
                    self.chapter_list.currentRow() + 1
                )
                self.chapter_clicked()
        # Deserve normal key_press event
        else:
            self.key_press(event)

    @QtCore.Slot()
    def close(self) -> bool:
        # Clear temporary directory
        if os.path.exists(os.path.join(WORKING_DIR, 'tmp')):
            shutil.rmtree(os.path.join(WORKING_DIR, 'tmp'))
            print('[INFO] Temporary directory cleared.')
        # Close window
        return super().close()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
