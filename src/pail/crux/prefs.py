from PySide2 import QtCore
import json
from .constants import Organization

class QtSettings(object):

    def __init__(self, application):
        self._qt_settings = QtCore.QSettings(Organization, application)

    @staticmethod
    def join_key(key, layers=()):
        return "/".join(list(layers) + [key])

    def get(self, key, layers=(), default=None):
        joined_key = self.join_key(key, layers)
        if self._qt_settings.contains(joined_key):
            return self._qt_settings.value(joined_key)
        else:
            self.set(key, default, layers)
            return default

    def set(self, key, value, layers=None):
        joined_key = self.join_key(key, layers)
        self._qt_settings.setValue(joined_key, value)

    def dump(self, file_path):
        settings_dict = {
            key: self._qt_settings.value(key)
            for key in self._qt_settings.allKeys()
        }

        with open(file_path, "w") as file:
            json.dump(settings_dict, file, indent=4)
