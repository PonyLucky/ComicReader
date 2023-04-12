import json
import os


class Settings:
    def __init__(self, path):
        self._path = path
        self.settings = {}
        self.load()

    def load(self):
        """Load the settings from the JSON file."""
        # If the settings file doesn't exist, create it with default settings.
        if not os.path.exists(self._path):
            self.settings = {
                'scroll': {
                    'step': 100,
                    'duration': 100
                },
                'click': {
                    'step': 500,
                    'duration': 400
                },
                'page': {
                    'step': 500,
                    'duration': 400
                },
                'mouse': {
                    'step': 10,
                    'duration': 10
                },
                'viewer': {
                    'width': 800,
                },
                'last_read': None,
                'comics_dir': '/home/louis/Documents/Mangas/',
            }
            self.save()
        with open(self._path, 'r') as f:
            self.settings = json.load(f)

    def save(self):
        """Save the settings to the JSON file."""
        with open(self._path, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def get(self, key, default=None) -> object:
        """Get a setting from the settings dictionary.

        ----------
        # Parameters
        key: The key of the setting to get.
        default: The default value to return if the key is not found.

        ----------
        # Returns
        The value of the setting, or the default value if the key is not found.
        """
        return self.settings.get(key, default)

    def set(self, key, value):
        """Set a setting in the settings dictionary.

        ----------
        # Parameters
        key: The key of the setting to set.
        value: The value of the setting to set.
        """
        self.settings[key] = value
        self.save()

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)
