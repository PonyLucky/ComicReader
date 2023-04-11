import os
import json
from datetime import datetime


class Metadata:
    def __init__(self, path):
        self._path = path
        self.metadata = {}
        self.load()

    def load(self):
        """Load the metadata from the JSON file."""
        if not os.path.exists(self._path):
            self.metadata = {
                'last_chapter': None,
                'last_position': None,
                'last_updated': datetime.now().isoformat()
            }
            self.save()
        with open(self._path, 'r') as f:
            self.metadata = json.load(f)

    def save(self):
        """Save the metadata to the JSON file."""
        # Update the last updated time
        self.metadata['last_updated'] = datetime.now().isoformat()
        with open(self._path, 'w') as f:
            json.dump(self.metadata, f, indent=4)

    def get(self, key, default=None) -> object:
        """Get a metadata from the metadata dictionary.

        ----------
        # Parameters
        key: The key of the metadata to get.
        default: The default value to return if the key is not found.

        ----------
        # Returns
        The value of the metadata, or the default value if the key is not
        found.
        """
        return self.metadata.get(key, default)

    def set(self, key, value):
        """Set a metadata in the metadata dictionary.

        ----------
        # Parameters
        key: The key of the metadata to set.
        value: The value of the metadata to set.
        """
        self.metadata[key] = value
        self.save()

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __repr__(self):
        return str(self.metadata)

    def __str__(self):
        return str(self.metadata)
