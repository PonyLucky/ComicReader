import os
import zipfile
from PyQt5 import QtCore, QtWidgets, QtGui


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
        size_buttons = self._scale(30)

        # Close button
        self.close_button = QtWidgets.QPushButton()
        self.close_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.close_button.setStyleSheet('border-color: #868482;')
        self.close_button.setIcon(QtGui.QIcon('images/close.svg'))
        self.close_button.setIconSize(QtCore.QSize(
            size_buttons, size_buttons
        ))
        self.close_button.clicked.connect(self.close_image_viewer)
        self.top_menu_layout.addWidget(self.close_button)

        # Fullscreen button
        self.fullscreen_button = QtWidgets.QPushButton()
        self.fullscreen_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.fullscreen_button.setStyleSheet('border-color: #868482;')
        self.fullscreen_button.setIcon(QtGui.QIcon('images/fullscreen.svg'))
        self.fullscreen_button.setIconSize(QtCore.QSize(
            size_buttons, size_buttons
        ))
        self.fullscreen_button.clicked.connect(self.toogle_fullscreen)
        self.top_menu_layout.addWidget(self.fullscreen_button)

        # Spacer
        self.top_menu_layout.addStretch()

        # Top button
        self.top_button = QtWidgets.QPushButton()
        self.top_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.top_button.setStyleSheet('border-color: #868482;')
        self.top_button.setIcon(QtGui.QIcon('images/top.svg'))
        self.top_button.setIconSize(QtCore.QSize(
            size_buttons, size_buttons
        ))
        self.top_button.clicked.connect(self.go_to_top)
        self.top_menu_layout.addWidget(self.top_button)

        # Bottom button
        self.bottom_button = QtWidgets.QPushButton()
        self.bottom_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.bottom_button.setStyleSheet('border-color: #868482;')
        self.bottom_button.setIcon(QtGui.QIcon('images/bottom.svg'))
        self.bottom_button.setIconSize(QtCore.QSize(
            size_buttons, size_buttons
        ))
        self.bottom_button.clicked.connect(self.go_to_bottom)
        self.top_menu_layout.addWidget(self.bottom_button)

        # Spacer
        self.top_menu_layout.addStretch()

        # Previous button
        self.previous_button = QtWidgets.QPushButton()
        self.previous_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.previous_button.setStyleSheet('border-color: #868482;')
        self.previous_button.setIcon(QtGui.QIcon('images/previous.svg'))
        self.previous_button.setIconSize(QtCore.QSize(
            size_buttons, size_buttons
        ))
        self.previous_button.clicked.connect(self.previous_chapter)
        self.top_menu_layout.addWidget(self.previous_button)

        # Next button
        self.next_button = QtWidgets.QPushButton()
        self.next_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.next_button.setStyleSheet('border-color: #868482;')
        self.next_button.setIcon(QtGui.QIcon('images/next.svg'))
        self.next_button.setIconSize(QtCore.QSize(
            size_buttons, size_buttons
        ))
        self.next_button.clicked.connect(self.next_chapter)
        self.top_menu_layout.addWidget(self.next_button)

        # Scroll area
        self.scroller = QtWidgets.QScrollArea()
        self.scroller.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff
        )
        self.scroller.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff
        )
        # Bind image_viewer key events to scroller
        self.scroller.keyPressEvent = self.image_viewer_key_press
        # Center image
        self.scroller.setAlignment(QtCore.Qt.AlignCenter)
        # Add scroll area to layout
        self.image_viewer_layout.addWidget(self.scroller)

        # List of images
        self.scroller_images = []

        # Boolean to prevent changing multiple chapters at once
        self.is_changing_chapter = False
        self.changing_chapter_timer = QtCore.QTimer()
        self.changing_chapter_timer.setInterval(1000)
        self.changing_chapter_timer.timeout.connect(
            self.changing_chapter_timeout
        )

        # Set theme
        self.set_theme()

    # ------------------------------------------------------------------------
    # ---------------------------------Events---------------------------------
    # ------------------------------------------------------------------------

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
                if (
                    image.endswith('.png')
                    or image.endswith('.jpg')
                    or image.endswith('.jpeg')
                    or image.endswith('.webp')
                    or image.endswith('.webm')
                ):
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
        width = self._scale(self.settings['viewer']['width'])
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
            self.scroll_update("-")
        # Right, Down -> scroll down
        elif (
            event.key() == QtCore.Qt.Key_Right
            or event.key() == QtCore.Qt.Key_Down
        ):
            self.scroll_update("+")
        # Handle PageUp -> scroll up
        elif event.key() == QtCore.Qt.Key_PageUp:
            self.scroll_update("-", True)
        # Handle PageDown -> scroll down
        elif event.key() == QtCore.Qt.Key_PageDown:
            self.scroll_update("+", True)
        # Handle Shift+Space -> scroll up
        elif (
            event.key() == QtCore.Qt.Key_Space
            and event.modifiers() == QtCore.Qt.ShiftModifier
        ):
            self.scroll_update("-", True)
        # Handle Space -> scroll down
        elif event.key() == QtCore.Qt.Key_Space:
            self.scroll_update("+", True)
        # Handle Tab -> scroll down
        elif event.key() == QtCore.Qt.Key_Tab:
            self.scroll_update("+", True)
        # Handle Shift+Tab -> scroll up
        elif (
            (
                event.key() == QtCore.Qt.Key_Tab
                and event.modifiers() == QtCore.Qt.ShiftModifier
            )
            or event.key() == QtCore.Qt.Key_Backtab
        ):
            self.scroll_update("-", True)
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

    def image_viewer_mouse_press(self, event):
        """Handle mouse press events."""
        # Get position of mouse press depending of settings
        orientation = self.settings['orientation']
        pos = None
        base = None
        if orientation == "vertical":
            pos = event.pos().y()
            base = self.image_viewer.height()
        elif orientation == "horizontal":
            pos = event.pos().x()
            base = self.image_viewer.width()

        # Get step and duration of scroll animation
        step = self._scale(self.settings['click']['step'])
        duration = self.settings['click']['duration']
        # Mouse press on 0% to 40% of image viewer
        if pos < base * 0.4:
            direction = "-"
            # Update current chapter if needed
            has_chapter_changed = self.update_chapter_scroller(direction)
            if has_chapter_changed:
                return
            # Scroll up
            self.scroll_animation(direction, step, duration)
        # Mouse press between 40% and 60% of image viewer
        elif pos < base * 0.6:
            self.toogle_top_menu()
        # Mouse press on 60% and more of image viewer
        else:
            direction = "+"
            # Update current chapter if needed
            has_chapter_changed = self.update_chapter_scroller(direction)
            if has_chapter_changed:
                return
            # Scroll down
            self.scroll_animation(direction, step, duration)
        # Save progression
        self.progression_chapter()

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

    def image_viewer_wheel_event(self, event):
        """Handle mouse wheel events."""
        # Handle mouse wheel -> Save progression
        self.progression_chapter()
        # Scroll
        speed = event.angleDelta().y()
        if speed > 0:
            # Update current chapter if needed
            has_chapter_changed = self.update_chapter_scroller("-")
            if has_chapter_changed:
                return
            self.scroller.verticalScrollBar().setValue(
                self.scroller.verticalScrollBar().value()
                - speed
            )
        elif speed < 0:
            # Update current chapter if needed
            has_chapter_changed = self.update_chapter_scroller("+")
            if has_chapter_changed:
                return
            self.scroller.verticalScrollBar().setValue(
                self.scroller.verticalScrollBar().value()
                - speed
            )

    def previous_chapter(self, event=None):
        """Select previous chapter."""
        # If changing chapter, return
        is_changing_chapter = self.changing_chapter()
        if is_changing_chapter:
            return
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
        # If changing chapter, return
        is_changing_chapter = self.changing_chapter()
        if is_changing_chapter:
            return
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

    def toogle_fullscreen(self, event=None, force: bool = None):
        """Toggle fullscreen."""
        if force is not None:
            if force:
                self._set_fullscreen()
            else:
                self._set_maximized()
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

    def go_to_top(self, event=None):
        """Go to top."""
        self.scroll_animation("top")

    def go_to_bottom(self, event=None):
        """Go to bottom."""
        self.scroll_animation("bottom")

    # ------------------------------------------------------------------------
    # ---------------------------------Timers---------------------------------
    # ------------------------------------------------------------------------

    def changing_chapter_timeout(self, event=None):
        """Handle changing chapter timeout."""
        self.changing_chapter_timer.stop()
        self.is_changing_chapter = False

    # ------------------------------------------------------------------------
    # -------------------------------Functions--------------------------------
    # ------------------------------------------------------------------------

    def set_theme(self):
        """Set theme."""
        # Set dark theme
        theme = "background-color: #2d2d2d;color: #ffffff;"
        self.image_viewer.setStyleSheet("QWidget {" + theme + "}")
        self.top_menu.setStyleSheet("QWidget {" + theme + "}")
        self.scroller.setStyleSheet("QScrollArea {" + theme + "}")

    def set_settings(self, settings: dict):
        """Set settings."""
        self.settings = settings

    def scroll_update(self, direction: str, is_page: bool = False):
        """Update scroll position and current chapter if needed."""
        # Update current chapter if needed
        has_chapter_changed = self.update_chapter_scroller(direction)
        if has_chapter_changed:
            return
        # Update scroll position
        step = None
        duration = None
        if is_page:
            step = self._scale(self.settings['page']['step'])
            duration = self.settings['page']['duration']
        self.scroll_animation(direction, step, duration)

    def changing_chapter(self) -> bool:
        """Handle changing chapter."""
        # Handle changing chapter
        if not self.is_changing_chapter:
            self.is_changing_chapter = True
            # Stopping scrolling
            if (
                "scroller_animation" in self.__dict__
                and self.scroller_animation is not None
            ):
                self.scroller_animation.stop()
            self.changing_chapter_timer.start()
            return False
        return True

    def scroll_animation(
            self,
            direction: str,
            force_step: int = None,
            force_duration: int = None
    ):
        """Scroll content smoothly using a QPropertyAnimation."""
        # Step
        step = self._scale(self.settings['scroll']['step'])
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

    def update_chapter_scroller(self, direction) -> bool:
        """Update current chapter depending on scroll position."""
        scroller = self.scroller.verticalScrollBar()
        # If scroll is at the top, read previous chapter
        if (direction == "-" and scroller.value() == 0):
            self.previous_chapter()
            return True
        # If scroll is at the bottom, read next chapter
        if (direction == "+" and scroller.value() == scroller.maximum()):
            self.next_chapter()
            return True
        return False

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
        self.image_viewer.setWindowState(
            QtCore.Qt.WindowState.WindowNoState
        )
        self.image_viewer.setWindowState(
            QtCore.Qt.WindowState.WindowMaximized
        )
        self.fullscreen_button.setIcon(QtGui.QIcon('images/fullscreen.svg'))

    def _set_fullscreen(self):
        """Set window fullscreen."""
        self.image_viewer.setWindowState(
            QtCore.Qt.WindowState.WindowFullScreen
        )
        self.fullscreen_button.setIcon(QtGui.QIcon(
            'images/fullscreen_exit.svg'
        ))

    def _scale(self, val: int) -> int:
        """Scale value."""
        return int(val * self.settings['viewer']['ui_scale'])
