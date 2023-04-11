import os
from PySide6 import QtCore, QtWidgets, QtGui
import zipfile


class Viewer:
    def __init__(self, WORKING_DIR, settings):
        self.WORKING_DIR = WORKING_DIR
        self.settings = settings
        self.current_comic = None
        self.chapter_list = None
        # Image viewer
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
        # List of images
        self.image_viewer_images = []

    def set_settings(self, settings: dict):
        """Set settings."""
        self.settings = settings

    def chapter_clicked(self, current_comic=None, chapter_list=None):
        """
        Load images for a chapter.
        Load all images next (scroll) to each other.
        As the chapter is a .cbz file, we can use zipfile to
        extract the images to a temporary directory.
        """
        if current_comic is not None:
            self.current_comic = current_comic
        if chapter_list is not None:
            self.chapter_list = chapter_list
        chapter = self.chapter_list.currentItem().text()
        chapter_path = self.current_comic.get_chapter_path(chapter)
        # Refresh metadata
        self.current_comic.refresh()
        # Save last chapter
        self.current_comic.set_last_chapter(chapter)
        # Create temporary directory
        manga_name = self.current_comic.name
        tmp_dir = os.path.join(self.WORKING_DIR, 'tmp', manga_name, chapter)
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
            # Save progression
            self.progression_chapter()
            # Close image viewer
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
