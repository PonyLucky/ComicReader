"""
Viewer class

This class is responsible for displaying the images of the comic.

The viewer is a QWidget that is displayed in a separate window.
"""

import os
import zipfile
from PyQt5 import QtCore, QtWidgets, QtGui
from .comic import Comic


class Viewer:
    """
    Viewer class

    This class is responsible for displaying the images of the comic.

    The viewer is a QWidget that is displayed in a separate window.
    """
    def __init__(self, working_dir: str, settings: dict):
        self.working_dir = working_dir
        self.settings = settings
        self.current_comic = None
        self.chapter_list = None
        self.scroller_animation = None

        # Image viewer
        self.image_viewer = QtWidgets.QWidget()
        self.image_viewer.setWindowTitle('Image Viewer')
        self.image_viewer.setWindowIcon(QtGui.QIcon('images/comic_reader.png'))
        self.image_viewer.resize(1000, 600)
        # Image viewer events
        self.image_viewer.keyPressEvent = self._image_viewer_key_press
        self.image_viewer.mousePressEvent = self._image_viewer_mouse_press
        self.image_viewer.keyReleaseEvent = self._image_viewer_key_release
        self.image_viewer.wheelEvent = self._image_viewer_wheel_event

        # Hover events
        self.image_viewer.setMouseTracking(True)
        self.image_viewer.installEventFilter(self.image_viewer)
        self.image_viewer.enterEvent = self._image_viewer_mouse_move

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
        self.fullscreen_button.clicked.connect(self._toggle_fullscreen)
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
        self.previous_button.clicked.connect(self._previous_chapter)
        self.top_menu_layout.addWidget(self.previous_button)

        # Next button
        self.next_button = QtWidgets.QPushButton()
        self.next_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.next_button.setStyleSheet('border-color: #868482;')
        self.next_button.setIcon(QtGui.QIcon('images/next.svg'))
        self.next_button.setIconSize(QtCore.QSize(
            size_buttons, size_buttons
        ))
        self.next_button.clicked.connect(self._next_chapter)
        self.top_menu_layout.addWidget(self.next_button)

        # Scroll area
        self.scroller = QtWidgets.QScrollArea()
        self.scroller.verticalScrollBar().hide()
        self.scroller.horizontalScrollBar().hide()
        # Bind image_viewer key events to scroller
        self.scroller.keyPressEvent = self._image_viewer_key_press
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
        self._set_theme()

    # ------------------------------------------------------------------------
    # ---------------------------------Events---------------------------------
    # ------------------------------------------------------------------------

    def chapter_clicked(
            self,
            current_comic: Comic = None,
            chapter_list: QtWidgets.QListWidget = None):
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
        tmp_dir = os.path.join(self.working_dir, 'tmp', manga_name, chapter)
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
        self.image_viewer.setWindowTitle(
            f'{self.current_comic.name} - {min_title}'
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
        print(f"- chapter: {chapter_path}")
        print(f"- nb images: {len(self.scroller_images)}")

    def _image_viewer_key_press(self, event):
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
            self._scroll_update("-")
        # Right, Down -> scroll down
        elif (
            event.key() == QtCore.Qt.Key_Right
            or event.key() == QtCore.Qt.Key_Down
        ):
            self._scroll_update("+")
        # Handle PageUp -> scroll up
        elif event.key() == QtCore.Qt.Key_PageUp:
            self._scroll_update("-", True)
        # Handle PageDown -> scroll down
        elif event.key() == QtCore.Qt.Key_PageDown:
            self._scroll_update("+", True)
        # Handle Shift+Space -> scroll up
        elif (
            event.key() == QtCore.Qt.Key_Space
            and event.modifiers() == QtCore.Qt.ShiftModifier
        ):
            self._scroll_update("-", True)
        # Handle Space -> scroll down
        elif event.key() == QtCore.Qt.Key_Space:
            self._scroll_update("+", True)
        # Handle Tab -> scroll down
        elif event.key() == QtCore.Qt.Key_Tab:
            self._scroll_update("+", True)
        # Handle Shift+Tab -> scroll up
        elif (
            (
                event.key() == QtCore.Qt.Key_Tab
                and event.modifiers() == QtCore.Qt.ShiftModifier
            )
            or event.key() == QtCore.Qt.Key_Backtab
        ):
            self._scroll_update("-", True)
        # Handle Home -> scroll to top
        elif event.key() == QtCore.Qt.Key_Home:
            self._scroll_animation("top")
        # Handle End -> scroll to bottom
        elif event.key() == QtCore.Qt.Key_End:
            self._scroll_animation("bottom")
        # Handle P -> read previous chapter
        elif event.key() == QtCore.Qt.Key_P:
            self._previous_chapter()
        # Handle N -> read next chapter
        elif event.key() == QtCore.Qt.Key_N:
            self._next_chapter()
        # Handle F, F11 -> toggle fullscreen
        elif (
            event.key() == QtCore.Qt.Key_F
            or event.key() == QtCore.Qt.Key_F11
        ):
            self._toggle_fullscreen()
        # Handle M -> toggle top menu
        elif event.key() == QtCore.Qt.Key_M:
            self._toggle_top_menu()
        # Handle C -> toggle mouse cursor
        elif event.key() == QtCore.Qt.Key_C:
            self._toggle_mouse_cursor()
        # Handle S -> toggle scrollbar
        elif event.key() == QtCore.Qt.Key_S:
            self._toggle_scrollbar()

    def _image_viewer_mouse_press(self, event):
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
            has_chapter_changed = self._update_chapter_scroller(direction)
            if has_chapter_changed:
                return
            # Scroll up
            self._scroll_animation(direction, step, duration)
        # Mouse press between 40% and 60% of image viewer
        elif pos < base * 0.6:
            self._toggle_top_menu()
        # Mouse press on 60% and more of image viewer
        else:
            direction = "+"
            # Update current chapter if needed
            has_chapter_changed = self._update_chapter_scroller(direction)
            if has_chapter_changed:
                return
            # Scroll down
            self._scroll_animation(direction, step, duration)
        # Save progression
        self._progression_chapter()

    def _image_viewer_key_release(self, event):
        """Handle key release events."""
        # Handle Down, Up, Left, Right, PageUp, PageDown, Home, End
        # -> Save progression
        if (
            event.key() == QtCore.Qt.Key_Down
            or event.key() == QtCore.Qt.Key_Up
            or event.key() == QtCore.Qt.Key_Left
            or event.key() == QtCore.Qt.Key_Right
        ):
            self._progression_chapter()
        elif (
            event.key() == QtCore.Qt.Key_PageUp
            or event.key() == QtCore.Qt.Key_PageDown
            or event.key() == QtCore.Qt.Key_Home
            or event.key() == QtCore.Qt.Key_End
        ):
            self._progression_chapter()

    def _image_viewer_wheel_event(self, event):
        """Handle mouse wheel events."""
        # Handle mouse wheel -> Save progression
        self._progression_chapter()
        # Scroll
        speed = event.angleDelta().y()
        if speed > 0:
            # Update current chapter if needed
            has_chapter_changed = self._update_chapter_scroller("-")
            if has_chapter_changed:
                return
            self.scroller.verticalScrollBar().setValue(
                self.scroller.verticalScrollBar().value()
                - speed
            )
        elif speed < 0:
            # Update current chapter if needed
            has_chapter_changed = self._update_chapter_scroller("+")
            if has_chapter_changed:
                return
            self.scroller.verticalScrollBar().setValue(
                self.scroller.verticalScrollBar().value()
                - speed
            )

    def eventFilter(self, obj, event):
        if (
            event.type() == QtCore.QEvent.MouseMove
        ):
            self._image_viewer_mouse_move(event)
        return super().eventFilter(obj, event)

    def _image_viewer_mouse_move(self, event):
        """Handle mouse mouse events."""
        # Show mouse cursor
        self._toggle_mouse_cursor(force=True)

    def _previous_chapter(self, event=None):
        """Select previous chapter."""
        # DEBUG
        if event:
            print("[DEBUG] previous_chapter |", event.key())
        # If changing chapter, return
        is_changing_chapter = self._changing_chapter()
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
        else:
            # Close window if first chapter
            self.close_image_viewer()
        # Reset scroll position
        self.scroller.verticalScrollBar().setValue(0)
        # Set back to fullscreen if needed
        if state == QtCore.Qt.WindowFullScreen:
            self._toggle_fullscreen(force=True)

    def _next_chapter(self, event=None):
        """Select next chapter."""
        # DEBUG
        if event:
            print("[DEBUG] next_chapter |", event.key())
        # If changing chapter, return
        is_changing_chapter = self._changing_chapter()
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
        else:
            # Close window if last chapter
            self.close_image_viewer()
        # Reset scroll position
        self.scroller.verticalScrollBar().setValue(0)
        # Set back to fullscreen if needed
        if state == QtCore.Qt.WindowFullScreen:
            self._toggle_fullscreen(force=True)

    def _toggle_fullscreen(self, event=None, force: bool = None):
        """Toggle fullscreen."""
        # DEBUG
        if event:
            print("[DEBUG] toggle_fullscreen |", event.key())
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

    def _toggle_top_menu(self, event=None):
        """Toggle top menu."""
        # DEBUG
        if event:
            print("[DEBUG] toggle_top_menu |", event.key())
        if self.top_menu.isHidden():
            self.top_menu.show()
        else:
            self.top_menu.hide()

    def close_image_viewer(self, event=None):
        """Close image viewer."""
        # DEBUG
        if event:
            print("[DEBUG] close_image_viewer |", event.key())
        # Save progression
        self._progression_chapter()
        # Close image viewer
        self.image_viewer.hide()

    def go_to_top(self, event=None):
        """Go to top."""
        # DEBUG
        if event:
            print("[DEBUG] go_to_top |", event.key())
        self._scroll_animation("top")

    def go_to_bottom(self, event=None):
        """Go to bottom."""
        # DEBUG
        if event:
            print("[DEBUG] got_to_bottom |", event.key())
        self._scroll_animation("bottom")

    # ------------------------------------------------------------------------
    # ---------------------------------Timers---------------------------------
    # ------------------------------------------------------------------------

    def changing_chapter_timeout(self, event=None):
        """Handle changing chapter timeout."""
        # DEBUG
        if event:
            print("[DEBUG] changing_chapter_timeout |", event.key())
        self.changing_chapter_timer.stop()
        self.is_changing_chapter = False

    # ------------------------------------------------------------------------
    # -------------------------------Functions--------------------------------
    # ------------------------------------------------------------------------

    def set_settings(self, settings: dict):
        """Set settings."""
        self.settings = settings

    def _set_theme(self):
        """Set theme."""
        # Set dark theme
        theme = "background-color: #2d2d2d;color: #ffffff;"
        self.image_viewer.setStyleSheet("QWidget {" + theme + "}")
        self.top_menu.setStyleSheet("QWidget {" + theme + "}")
        self.scroller.setStyleSheet("QScrollArea {" + theme + "}")

    def _scroll_update(self, direction: str, is_page: bool = False):
        """Update scroll position and current chapter if needed."""
        # Update current chapter if needed
        has_chapter_changed = self._update_chapter_scroller(direction)
        if has_chapter_changed:
            return
        # Update scroll position
        step = None
        duration = None
        # If page scrolling
        if is_page:
            step = self._scale(self.settings['page']['step'])
            duration = self.settings['page']['duration']
        self._scroll_animation(direction, step, duration)

    def _changing_chapter(self) -> bool:
        """Handle changing chapter."""
        # Handle changing chapter
        if not self.is_changing_chapter:
            self.is_changing_chapter = True
            # Stopping scrolling
            if self.scroller_animation is not None:
                self.scroller_animation.stop()
            self.changing_chapter_timer.start()
            return False
        return True

    def _scroll_animation(
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
            self._toggle_mouse_cursor(force=False)
        elif direction == "-":
            new_scroll_position = current_scroll_position - step
            self._toggle_mouse_cursor(force=False)
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

    def _update_chapter_scroller(self, direction) -> bool:
        """Update current chapter depending on scroll position."""
        scroller = self.scroller.verticalScrollBar()
        # If scroll is at the top, read previous chapter
        if (direction == "-" and scroller.value() == 0):
            self._previous_chapter()
            return True
        # If scroll is at the bottom, read next chapter
        if (direction == "+" and scroller.value() == scroller.maximum()):
            self._next_chapter()
            return True
        return False

    def _progression_chapter(self):
        """Keep track of progression."""
        # Get current position
        current_position = self.scroller.verticalScrollBar().value()
        # Update progression
        self.current_comic.set_chapter_last_position(current_position)
        # Save
        self.current_comic.save()
        print("[DEBUG] Progression")
        print(f"- Current position: {current_position}")

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

    def _toggle_mouse_cursor(self, force: bool = None):
        """Toggle mouse cursor."""
        # Get current cursor
        val = self.image_viewer.cursor().shape() != QtCore.Qt.BlankCursor
        print("[DEBUG] _toggle_mouse_cursor |\n- Blank: ", val)
        print("- force: ", force)
        # If cursor is already in the right state, do nothing
        if val == force:
            return
        # Force cursor state if needed
        if force is not None:
            val = force
        print("- val: ", val)
        # Set cursor
        if val:
            self.image_viewer.setCursor(QtCore.Qt.ArrowCursor)
        else:
            self.image_viewer.setCursor(QtCore.Qt.BlankCursor)

    def _toggle_scrollbar(self, force: bool = False):
        """Toggle scrollbar."""
        if self.scroller.verticalScrollBar().isVisible():
            self.scroller.verticalScrollBar().hide()
        else:
            self.scroller.verticalScrollBar().show()
