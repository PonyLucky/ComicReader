#!/usr/bin/env python
import os
import sys
import re
import subprocess
import shutil
from PySide6 import QtCore, QtWidgets, QtGui
import zipfile

# --- UPDATE THIS ---
WORKING_DIR = '/home/louis/.ComicReader/'
COMIC_DIR = '/home/louis/Documents/Mangas/'
# -------------------
SETTINGS_PATH = os.path.join(WORKING_DIR, 'ComicReader.ini')

# Set working directory
os.chdir(WORKING_DIR)

from settings import Settings
from comic import Comic


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Comic Reader')
        self.setWindowIcon(QtGui.QIcon('ComicReader.png'))
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
        self.image_viewer = QtWidgets.QScrollArea()
        self.image_viewer.setWindowTitle('Image Viewer')
        self.image_viewer.setWindowIcon(QtGui.QIcon('ComicReader.png'))
        self.image_viewer.resize(1000, 600)
        self.image_viewer.keyPressEvent = self.image_viewer_key_press
        self.image_viewer.mousePressEvent = self.image_viewer_mouse_press
        self.image_viewer.keyReleaseEvent = self.image_viewer_key_release
        self.image_viewer.wheelEvent = self.image_viewer_wheel_event
        self.image_viewer.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOn
        )
        self.image_viewer.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff
        )
        # Center image
        self.image_viewer.setAlignment(QtCore.Qt.AlignCenter)

        self.image_viewer_index = 0
        self.image_viewer_images = []

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
                for comic in os.listdir(COMIC_DIR)
                if os.path.isdir(os.path.join(COMIC_DIR, comic))
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
                COMIC_DIR,
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
        """
        Load images for a chapter.
        Load all images next (scroll) to each other.
        As the chapter is a .cbz file, we can use zipfile to
        extract the images to a temporary directory.
        """
        chapter = self.chapter_list.currentItem().text()
        chapter_path = self.current_comic.get_chapter_path(chapter)
        # Refresh metadata
        self.current_comic.refresh()
        # Save last chapter
        self.current_comic.set_last_chapter(chapter)
        # Create temporary directory
        manga_name = self.current_comic.name
        tmp_dir = os.path.join(WORKING_DIR, 'tmp', manga_name, chapter)
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        # Clear image viewer
        self.image_viewer_images = []
        # Extract images to a temporary directory
        with zipfile.ZipFile(chapter_path, 'r') as zip_file:
            for image in zip_file.namelist():
                if image.endswith('.png') or image.endswith('.jpg'):
                    zip_file.extract(
                        image,
                        tmp_dir
                    )
                    self.image_viewer_images.append(
                        os.path.join(tmp_dir, image)
                    )
        self.image_viewer_index = 0
        # Load all images vertically
        image_widget = QtWidgets.QWidget()
        image_layout = QtWidgets.QVBoxLayout()

        # Add "Previous" button
        height_button = 50
        previous_button = QtWidgets.QPushButton('Previous')
        previous_button.setFixedHeight(height_button)
        previous_button.setFocusPolicy(QtCore.Qt.NoFocus)
        previous_button.clicked.connect(self.previous_chapter)
        image_layout.addWidget(previous_button)

        width = self.settings['viewer']['width']
        for image in self.image_viewer_images:
            image_pixmap = QtGui.QPixmap(image)
            # Fit image to width
            image_pixmap = image_pixmap.scaledToWidth(width)
            # Create label
            image_label = QtWidgets.QLabel()
            image_label.setPixmap(image_pixmap)
            image_layout.addWidget(image_label)

        # Add "Next" button
        next_button = QtWidgets.QPushButton('Next')
        next_button.setFixedHeight(height_button)
        next_button.setFocusPolicy(QtCore.Qt.NoFocus)
        next_button.clicked.connect(self.next_chapter)
        image_layout.addWidget(next_button)
        # Set layout
        image_widget.setLayout(image_layout)
        self.image_viewer.setWidget(image_widget)
        # Change window title
        min_title = chapter[:-4].split(' ', 3)
        min_title = min_title[0] + ' ' + min_title[1]
        self.image_viewer.setWindowTitle(
            '{} - {}'.format(self.current_comic.name, min_title)
        )
        # Set focus on image viewer
        self.image_viewer.setFocus()
        # Get last_position if any
        last_position = self.current_comic.get_chapter_last_position()
        if last_position is not None:
            self.image_viewer.verticalScrollBar().setValue(last_position)
        # Maximize image viewer
        self.image_viewer.showMaximized()

        # Update chapter list
        is_last_chapter = False
        for index in range(self.chapter_list.count()):
            # If chapter is last chapter
            if self.chapter_list.item(index).text() == chapter:
                is_last_chapter = True
                self.chapter_list.item(index).setForeground(
                    QtGui.QColor(255, 255, 255)
                )
            else:
                # If is_last_chapter is False, set read chapters to gray
                if not is_last_chapter:
                    self.chapter_list.item(index).setForeground(
                        QtGui.QColor(128, 128, 128)
                    )
                # If is_last_chapter is True, set unread chapters to white
                else:
                    self.chapter_list.item(index).setForeground(
                        QtGui.QColor(255, 255, 255)
                    )
        print("[DEBUG] Load images")
        print("- chapter: {}".format(chapter_path))
        print("- nb images: {}".format(len(self.image_viewer_images)))

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
        # Handle Ctrl+Q, Ctrl+W -> quit
        if (
            (
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
    def image_viewer_key_press(self, event):
        """Handle key press events."""
        # Handle Esc, Ctrl+W, Ctrl+Q -> close image viewer
        if (
            event.key() == QtCore.Qt.Key_Escape
            or (
                event.key() == QtCore.Qt.Key_W
                and event.modifiers() == QtCore.Qt.ControlModifier
            )
            or (
                event.key() == QtCore.Qt.Key_Q
                and event.modifiers() == QtCore.Qt.ControlModifier
            )
        ):
            self.image_viewer.hide()
        # Handle arrow keys -> scroll content
        # Left, Up -> scroll up
        elif (
            event.key() == QtCore.Qt.Key_Left
            or event.key() == QtCore.Qt.Key_Up
        ):
            self.scroll_animation("-")
        # Right, Down -> scroll down
        elif (
            event.key() == QtCore.Qt.Key_Right
            or event.key() == QtCore.Qt.Key_Down
        ):
            self.scroll_animation("+")
        # Handle PageUp -> scroll up
        elif event.key() == QtCore.Qt.Key_PageUp:
            step = self.settings['page']['step']
            duration = self.settings['page']['duration']
            self.scroll_animation("-", step, duration)
        # Handle PageDown -> scroll down
        elif event.key() == QtCore.Qt.Key_PageDown:
            step = self.settings['page']['step']
            duration = self.settings['page']['duration']
            self.scroll_animation("+", step, duration)
        # Handle Home -> scroll to top
        elif event.key() == QtCore.Qt.Key_Home:
            self.scroll_animation("top")
        # Handle End -> scroll to bottom
        elif event.key() == QtCore.Qt.Key_End:
            self.scroll_animation("bottom")
        # Handle P -> read previous chapter
        elif event.key() == QtCore.Qt.Key_P:
            self.previous_chapter()
        # Handle N -> read next chapter
        elif event.key() == QtCore.Qt.Key_N:
            self.next_chapter()
        # Handle F, F11 -> toggle fullscreen
        elif (
            event.key() == QtCore.Qt.Key_F
            or event.key() == QtCore.Qt.Key_F11
        ):
            state = self.image_viewer.windowState()
            if state == QtCore.Qt.WindowFullScreen:
                self.image_viewer.setWindowState(QtCore.Qt.WindowMaximized)
            else:
                self.image_viewer.setWindowState(QtCore.Qt.WindowFullScreen)

    @QtCore.Slot()
    def image_viewer_mouse_press(self, event):
        """Handle mouse press events."""
        # Get x position of mouse press
        x = event.pos().x()
        step = self.settings['click']['step']
        duration = self.settings['click']['duration']
        # Is mouse press on left side of image viewer?
        if x < self.image_viewer.width() / 2:
            # Scroll up
            self.scroll_animation("-", step, duration)
        # Is mouse press on right side of image viewer?
        elif x > self.image_viewer.width() / 2:
            # Scroll down
            self.scroll_animation("+", step, duration)
        # Save progression
        self.progression_chapter()

    def scroll_animation(
            self,
            direction: str,
            force_step: int = None,
            force_duration: int = None
    ):
        """Scroll content smoothly using a QPropertyAnimation."""
        # Step
        step = self.settings['scroll']['step']
        if force_step is not None:
            step = abs(force_step)
        # Duration
        duration = self.settings['scroll']['duration']
        if force_duration is not None:
            duration = force_duration
        # Get current scroll position
        current_scroll_position = self.image_viewer.verticalScrollBar().value()
        # Get new scroll position
        if direction == "+":
            new_scroll_position = current_scroll_position + step
        elif direction == "-":
            new_scroll_position = current_scroll_position - step
        elif direction == "top":
            new_scroll_position = 0
        elif direction == "bottom":
            new_scroll_position = (
                self.image_viewer.verticalScrollBar().maximum()
            )
        # Create animation
        self.image_viewer_animation = QtCore.QPropertyAnimation(
            self.image_viewer.verticalScrollBar(),
            b"value"
        )
        self.image_viewer_animation.setDuration(duration)
        self.image_viewer_animation.setStartValue(current_scroll_position)
        self.image_viewer_animation.setEndValue(new_scroll_position)
        self.image_viewer_animation.start()

    def previous_chapter(self):
        """Select previous chapter."""
        # Get current fullscreen state
        state = self.image_viewer.windowState()
        # If not first chapter, select previous chapter
        if self.chapter_list.currentRow() > 0:
            self.chapter_list.setCurrentRow(
                self.chapter_list.currentRow() - 1
            )
            self.chapter_clicked()
        # Reset scroll position
        self.image_viewer.verticalScrollBar().setValue(0)
        # Set back to fullscreen if needed
        if state == QtCore.Qt.WindowFullScreen:
            self.image_viewer.setWindowState(QtCore.Qt.WindowFullScreen)

    def next_chapter(self):
        """Select next chapter."""
        # Get current fullscreen state
        state = self.image_viewer.windowState()
        # If not last chapter, select next chapter
        if self.chapter_list.currentRow() < self.chapter_list.count() - 1:
            self.chapter_list.setCurrentRow(
                self.chapter_list.currentRow() + 1
            )
            self.chapter_clicked()
        # Reset scroll position
        self.image_viewer.verticalScrollBar().setValue(0)
        # Set back to fullscreen if needed
        if state == QtCore.Qt.WindowFullScreen:
            self.image_viewer.setWindowState(QtCore.Qt.WindowFullScreen)

    @QtCore.Slot()
    def image_viewer_key_release(self, event):
        """Handle key release events."""
        # Handle Down, Up, Left, Right, PageUp, PageDown, Home, End
        # -> Save progression
        if (
            event.key() == QtCore.Qt.Key_Down
            or event.key() == QtCore.Qt.Key_Up
            or event.key() == QtCore.Qt.Key_Left
            or event.key() == QtCore.Qt.Key_Right
            or event.key() == QtCore.Qt.Key_PageUp
            or event.key() == QtCore.Qt.Key_PageDown
            or event.key() == QtCore.Qt.Key_Home
            or event.key() == QtCore.Qt.Key_End
        ):
            self.progression_chapter()

    @QtCore.Slot()
    def image_viewer_wheel_event(self, event):
        """Handle mouse wheel events."""
        # Handle mouse wheel -> Save progression
        self.progression_chapter()
        # Scroll
        speed = event.angleDelta().y()
        if speed > 0:
            self.image_viewer.verticalScrollBar().setValue(
                self.image_viewer.verticalScrollBar().value()
                - speed
            )
        elif speed < 0:
            self.image_viewer.verticalScrollBar().setValue(
                self.image_viewer.verticalScrollBar().value()
                - speed
            )

    def progression_chapter(self):
        """Keep track of progression."""
        # Get current position
        current_position = self.image_viewer.verticalScrollBar().value()
        # Update progression
        self.current_comic.set_chapter_last_position(current_position)
        # Save
        self.current_comic.save()
        print("[DEBUG] Progression")
        print("- Current position: {}".format(current_position))

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
