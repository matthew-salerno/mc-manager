import app_constants
import curses_helpers
import curses
import json
import urllib3

const = app_constants.constants()
https = urllib3.PoolManager()

def select(branch="ask",branch_title=""):
    if branch == "ask":
        branches=["Release","Snapshot","All"]
        menu = curses_helpers.select_h(branches, branch_title)
        branch = curses.wrapper(menu.display)
    versions = version_list(branch)
    return curses.wrapper(versions.display)

class version_list():
    def __init__(self, branch="all", title=""):
        branch = branch.lower()  # make case insensitive
        self._version_list=[]
        manifest = json.loads(https.request('GET',const.MANIFEST_URL).data.decode("utf-8"))
        for version in manifest["versions"]:
            if branch == "all":
                self._version_list.append(version["id"])
            elif branch == "snapshot":
                if version["type"] == "snapshot":
                    self._version_list.append(version["id"])
            elif branch == "release":
                if version["type"] == "release":
                    self._version_list.append(version["id"])
    def display(self, stdscr):
        menu = curses_helpers.select_v_scrolling(self._version_list, "Please select a version")
        return menu.display(stdscr)
if __name__ == "__main__":
    print(select("ask","please select a branch"))
    print(select("all"))
    print(select("release"))
    print(select("snapshot"))