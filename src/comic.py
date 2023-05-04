"""
Comic class.

This class contains utility methods about the comic.
"""


import os
from .metadata import Metadata


class Comic:
    """
    Comic class.

    This class contains utility methods about the comic.
    """
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.metadata = Metadata(os.path.join(path, '.metadata.json'))

    def get_last_chapter(self) -> str:
        """Get the last chapter for a comic."""
        return self.metadata['last_chapter']

    def set_last_chapter(self, chapter: str):
        """Set the last chapter for a comic."""
        self.metadata['last_chapter'] = chapter

    def get_chapter_path(self, chapter: str) -> str:
        """Get the path to a chapter."""
        return os.path.join(self.path, chapter)

    def get_chapter_last_position(self) -> int:
        """Get the last page for a chapter."""
        return self.metadata['last_position']

    def set_chapter_last_position(self, position: int):
        """Set the last page for a chapter."""
        self.metadata['last_position'] = position

    def save(self):
        """Save the metadata to the JSON file."""
        self.metadata.save()

    def refresh(self):
        """Refresh the metadata."""
        self.metadata.load()

    def __getitem__(self, key: object) -> object:
        return self.metadata[key]

    def __setitem__(self, key: object, value: object):
        self.metadata[key] = value
