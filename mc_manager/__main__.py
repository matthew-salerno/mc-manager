import app_constants, commands, curses_helpers
from getopt import getopt, GetoptError
import pkg_resources
import curses
import sys

const = app_constants.constants()

def process_command(arguments):
    """Processes the arguments and options issued by the command

    Args:
        arguments (list): should be a sys.argv[1:] argument vector
    """
    
    try:
        opts, args = getopt(arguments, "hvq", ["mc-version", "help", "quiet",
                                               "version"])
    except GetoptError:
        print(f"Wrong arguments, type {const.NAME} -h for help")
    option_dict = {
                  "-h": cmd_help,
                  "-v": version,
                  "--mc-version": commands.mc_version,
                  "--help": cmd_help, 
                  "--version": version
                  }
    args_dict = {
                "start": commands.start,
                "stop": commands.stop,
                "ramdisk": commands.ramdisk,
                "set-property": commands.set_property,
                "launch-path": commands.set_path,
                "eula": commands.set_eula,
                "get-eula": commands.get_eula,
                "send": commands.send,
                "status": commands.status,
                "install": commands.install,
                "launch-options": commands.launch_options,
                "stop-service": commands.stop_service
                }
    quiet = False
    if opts:  # if not empty
        # for this particular application we don't need a case where
        # there are multiple options or option values
        if "--quiet" in (x[0] for x in opts) or "-q" in (x[0] for x in opts):
            quiet=True
        option_dict[opts[0][0]](args)
    else:
        if len(args):
            if args[0] in args_dict:
                args_dict[args[0]](args[1:], printer=(commands.blank if quiet else print))
            else:
                print("No command found!")
        else:
            curses.wrapper(tui)


def version(args):
    """Returns the version of mc-as-a-service

    Args:
        args (any): doesn't except arguments,
        but could be called with arguments
    """
    print(const.VERSION)

def cmd_help(args):
    """Prints the file help.txt to the console

    Args:
        args (any): doesn't except arguments,
        but could be called with arguments
    """
    with const.HELP_PATH.open() as help_file:
        helpstring = help_file.read()
        help_file.close()
    print(f"{const.NAME}: Version {const.VERSION}")
    print(helpstring)


def tui(stdscr):
    """This is the top level TUI interface,
    or main menu
    """
    while True:
        menu_items = {
                    "Start":commands.start,
                    "Stop":commands.stop,
                    "Install":commands.install,
                    "Eula":commands.set_eula
                    }
        tui_items = {
                    "Launch Options":commands.tui_launch_options,
                    "Server Options":commands.tui_server_options
                    }
        selector = curses_helpers.select_v(list(menu_items)+list(tui_items))
        selected = selector.display(stdscr)
        if selected == None:
            break
        if selected in menu_items:
            menu_items[selected](printer=commands.blank)
        elif selected in tui_items:
            tui_items[selected](stdscr)

if __name__ == "__main__":
    process_command(sys.argv[1:])