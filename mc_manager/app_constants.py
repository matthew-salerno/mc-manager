from os import environ
from pathlib import Path
import sys

class constants():
    """These are all property functions which return values that should not be changed and
    are used by the mc-manager app
    """
    @property
    def SNAP(self):
        if "SNAP" in environ:
            return True
        else:
            return False

    @property
    def INTERFACE(self):
        return "com.salernosection.mc_as_a_service"

    @property
    def VERSION(self):
        if self.SNAP:
            return environ["SNAP_VERSION"]
        else:
            return "unknown"

    @property
    def NAME(self):
        if self.SNAP:
            return environ["SNAP_NAME"]
        else:
            return "mc_manager"

    @property
    def RESOURCES_DIR(self):
        if self.SNAP:
            return Path(environ["SNAP"])/"mc_manager"/"resources"
        else:
            return Path(__file__,'..').resolve()/"resources"

    @property
    def HELP_PATH(self):
        return self.RESOURCES_DIR/"help.txt"

    @property
    def MANIFEST_URL(self):
        return "https://launchermeta.mojang.com/mc/game/version_manifest.json"

    @property
    def EULA_URL(self):
        return "https://account.mojang.com/documents/minecraft_eula"
