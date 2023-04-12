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
        self.image_viewer = QtWidgets.QWidget()
        self.image_viewer.setWindowTitle('Image Viewer')
        self.image_viewer.setWindowIcon(QtGui.QIcon('images/ComicReader.png'))
        self.image_viewer.resize(1000, 600)
        # Image viewer events
        self.image_viewer.keyPressEvent = self.image_viewer_key_press
        self.image_viewer.mousePressEvent = self.image_viewer_mouse_press
        self.image_viewer.keyReleaseEvent = self.image_viewer_key_release
        self.image_viewer.wheelEvent = self.image_viewer_wheel_event

        # Image viewer layout
        self.image_viewer_layout = QtWidgets.QVBoxLayout()
        self.image_viewer.setLayout(self.image_viewer_layout)
        self.image_viewer_layout.setContentsMargins(0, 0, 0, 0)
        self.image_viewer_layout.setSpacing(0)

        # Top menu
        self.top_menu = QtWidgets.QWidget()
        self.top_menu_layout = QtWidgets.QHBoxLayout()
        self.top_menu.setLayout(self.top_menu_layout)
        self.top_menu_layout.setContentsMargins(2, 2, 2, 2)
        self.top_menu.setStyleSheet('background-color: #1e1b18;')
        self.image_viewer_layout.addWidget(self.top_menu)
        # Hide top menu
        self.top_menu.hide()

        # Size buttons in top menu
        size_buttons = (30, 30)

        # Close button
        self.close_button = QtWidgets.QPushButton()
        self.close_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.close_button.setStyleSheet('border-color: #868482;')
        self.close_button.setIcon(QtGui.QIcon('images/close.svg'))
        self.close_button.setIconSize(QtCore.QSize(*size_buttons))
        self.close_button.clicked.connect(self.close_image_viewer)
        self.top_menu_layout.addWidget(self.close_button)

        # Fullscreen button
        self.fullscreen_button = QtWidgets.QPushButton()
        self.fullscreen_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.fullscreen_button.setStyleSheet('border-color: #868482;')
        self.fullscreen_button.setIcon(QtGui.QIcon('images/fullscreen.svg'))
        self.fullscreen_button.setIconSize(QtCore.QSize(*size_buttons))
        self.fullscreen_button.clicked.connect(self.toogle_fullscreen)
        self.top_menu_layout.addWidget(self.fullscreen_button)

        # Spacer
        self.top_menu_layout.addStretch()

        # Previous button
        self.previous_button = QtWidgets.QPushButton()
        self.previous_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.previous_button.setStyleSheet('border-color: #868482;')
        self.previous_button.setIcon(QtGui.QIcon('images/previous.svg'))
        self.previous_button.setIconSize(QtCore.QSize(*size_buttons))
        self.previous_button.clicked.connect(self.previous_chapter)
        self.top_menu_layout.addWidget(self.previous_button)

        # Next button
        self.next_button = QtWidgets.QPushButton()
        self.next_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.next_button.setStyleSheet('border-color: #868482;')
        self.next_button.setIcon(QtGui.QIcon('images/next.svg'))
        self.next_button.setIconSize(QtCore.QSize(*size_buttons))
        self.next_button.clicked.connect(self.next_chapter)
        self.top_menu_layout.addWidget(self.next_button)

        # Scroll area
        self.scroller = QtWidgets.QScrollArea()
        self.scroller.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOn
        )
        self.scroller.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff
        )
        # Center image
        self.scroller.setAlignment(QtCore.Qt.AlignCenter)
        # Add scroll area to layout
        self.image_viewer_layout.addWidget(self.scroller)

        # List of images
        self.scroller_images = []

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
        self.scroller_images = []
        # Extract images to a temporary directory
        with zipfile.ZipFile(chapter_path, 'r') as zip_file:
            for image in zip_file.namelist():
                if image.endswith('.png') or image.endswith('.jpg'):
                    zip_file.extract(
                        image,
                        tmp_dir
                    )
                    self.scroller_images.append(
                        os.path.join(tmp_dir, image)
                    )

        # Load all images vertically
        image_widget = QtWidgets.QWidget()
        image_layout = QtWidgets.QVBoxLayout()
        width = self.settings['viewer']['width']
        for image in self.scroller_images:
            image_pixmap = QtGui.QPixmap(image)
            # Fit image to width
            image_pixmap = image_pixmap.scaledToWidth(width)
            # Create label
            image_label = QtWidgets.QLabel()
            image_label.setPixmap(image_pixmap)
            image_layout.addWidget(image_label)

        # Set layout
        image_widget.setLayout(image_layout)
        self.scroller.setWidget(image_widget)
        # Change window title
        min_title = chapter[:-4].split(' ', 3)
        min_title = min_title[0] + ' ' + min_title[1]
        self.scroller.setWindowTitle(
            '{} - {}'.format(self.current_comic.name, min_title)
        )
        # Set focus on image viewer
        self.scroller.setFocus()
        # Get last_position if any
        last_position = self.current_comic.get_chapter_last_position()
        if last_position is not None:
            self.scroller.verticalScrollBar().setValue(last_position)
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
        print("- nb images: {}".format(len(self.scroller_images)))

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
            self.close_image_viewer()
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
            self.toogle_fullscreen()
        # Handle M -> toggle top menu
        elif event.key() == QtCore.Qt.Key_M:
            self.toogle_top_menu()

    @QtCore.Slot()
    def image_viewer_mouse_press(self, event):
        """Handle mouse press events."""
        # Get y position of mouse press
        y = event.pos().y()
        step = self.settings['click']['step']
        duration = self.settings['click']['duration']
        # Mouse press on top 40% of image viewer
        if y < self.image_viewer.height() * 0.4:
            # Scroll up
            self.scroll_animation("-", step, duration)
        # Mouse press between 40% and 60% of image viewer
        elif y < self.image_viewer.height() * 0.6:
            self.toogle_top_menu()
        # Mouse press on bottom 40% of image viewer
        else:
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
            self.scroller.verticalScrollBar().setValue(
                self.scroller.verticalScrollBar().value()
                - speed
            )
        elif speed < 0:
            self.scroller.verticalScrollBar().setValue(
                self.scroller.verticalScrollBar().value()
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
        current_scroll_position = self.scroller.verticalScrollBar().value()
        # Get new scroll position
        if direction == "+":
            new_scroll_position = current_scroll_position + step
        elif direction == "-":
            new_scroll_position = current_scroll_position - step
        elif direction == "top":
            new_scroll_position = 0
        elif direction == "bottom":
            new_scroll_position = (
                self.scroller.verticalScrollBar().maximum()
            )
        # Create animation
        self.scroller_animation = QtCore.QPropertyAnimation(
            self.scroller.verticalScrollBar(),
            b"value"
        )
        self.scroller_animation.setDuration(duration)
        self.scroller_animation.setStartValue(current_scroll_position)
        self.scroller_animation.setEndValue(new_scroll_position)
        self.scroller_animation.start()

    def previous_chapter(self, event=None):
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
        self.scroller.verticalScrollBar().setValue(0)
        # Set back to fullscreen if needed
        if state == QtCore.Qt.WindowFullScreen:
            self.toogle_fullscreen(force=True)

    def next_chapter(self, event=None):
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
        self.scroller.verticalScrollBar().setValue(0)
        # Set back to fullscreen if needed
        if state == QtCore.Qt.WindowFullScreen:
            self.toogle_fullscreen(force=True)

    def progression_chapter(self):
        """Keep track of progression."""
        # Get current position
        current_position = self.scroller.verticalScrollBar().value()
        # Update progression
        self.current_comic.set_chapter_last_position(current_position)
        # Save
        self.current_comic.save()
        print("[DEBUG] Progression")
        print("- Current position: {}".format(current_position))

    def _set_maximized(self):
        """Set window maximized."""
        self.image_viewer.setWindowState(QtCore.Qt.WindowMaximized)
        self.fullscreen_button.setIcon(QtGui.QIcon('images/fullscreen.svg'))

    def _set_fullscreen(self):
        """Set window fullscreen."""
        self.image_viewer.setWindowState(QtCore.Qt.WindowFullScreen)
        self.fullscreen_button.setIcon(QtGui.QIcon(
            'images/fullscreen_exit.svg'
        ))

    def toogle_fullscreen(self, event=None, force: bool = None):
        """Toggle fullscreen."""
        if force is not None:
            if force:
                self._set_maximized()
            else:
                self._set_fullscreen()
        else:
            state = self.image_viewer.windowState()
            if state == QtCore.Qt.WindowFullScreen:
                self._set_maximized()
            else:
                self._set_fullscreen()

    def toogle_top_menu(self, event=None):
        """Toggle top menu."""
        if self.top_menu.isHidden():
            self.top_menu.show()
        else:
            self.top_menu.hide()

    def close_image_viewer(self, event=None):
        """Close image viewer."""
        # Save progression
        self.progression_chapter()
        # Close image viewer
        self.image_viewer.hide()