import app_constants, eula, version_selector, curses_helpers
import curses

import subprocess
from copy import deepcopy
from gi.repository import GLib
const = app_constants.constants()

if const.SNAP:
    from pydbus import SystemBus as UsedBus
else:
    from pydbus import SessionBus as UsedBus
bus = UsedBus()
try:
    manager = bus.get(const.INTERFACE)
except GLib.Error:
    print("error connecting to service")
    exit(1)
def str2bool(string):
    """Quick function that converts a string to bool

    Args:
        string (str): The string to be converted to a bool

    Raises:
        TypeError: Raises an error if string is not of type bool or str

    Returns:
        bool: the converted string
    """
    if isinstance(string,str):
        if string.lower() in ["true", "on", "yes", "1", "t"]:
            return True
        elif string.lower() in ["false", "off", "no", "0", "f"]:
            return False
    elif isinstance(string,bool):
        return string
    else:
        raise TypeError

def blank(*args, **kwargs):
    """Does nothing, takes any arguments
    Used for specifying a printer function
    TODO: Replace this with something a little more
    appropriate, like maybe null object to be used with a
    print object and a the logger module.
    """
    pass

def set_eula(args=[], printer=print):
    """
    Returns:
        bool: returns whether or not the user has agreed to the eula
    """
    if curses.wrapper(tui_set_eula):
        printer("Signed EULA")
        agree = True
    else:
        printer("Unsigned EULA")
        agree = False
    manager.eula = agree
    return agree

def tui_set_eula(stdscr):
    """sets eula without creating a wrapper
    """
    return eula.eula_check(stdscr)

def mc_version(args=[], printer=print):
    """Returns the minecraft game version

    Args:
        printer (function, optional): The function to
            display text. Defaults to print.

    Returns:
        str: the minecraft version
    """
    mc_version = manager.mc_version
    printer(mc_version)
    return mc_version



def start(args=[], printer=print):
    """Tells the minecraft server to start

    Args:
        printer (function, optional): The function to
            display text. Defaults to print.

    Returns:
        bool: whether the start was successful
    """
    if not len(args):
        started = manager.start(120)
    else:
        if type(args[0]) is int:
            started = manager.start(args[0])
        else:
            printer("Please use an integer as the argument")
            started = False
    
    if started:
        printer("Started server")
    else:
        printer("Could not start server!")
    return started



def stop(args=[], printer=print):
    """Tells the minecraft server to stop

    Args:
        printer (function, optional): The function to
            display text. Defaults to print.

    Returns:
        bool: whether the server successfully stopped
    """
    if not len(args):
        stopped = manager.stop(120)
    else:
        if type(args[0]) is int:
            stopped = manager.stop(args[0])
        else:
            printer("Please use an integer as the argument")
            stopped = False
    if stopped:
        printer("Stopped server")
    else:
        printer("Could not stop server!")
    return stopped



def ramdisk(args=[], printer=print):
    """Changes the ramdisk option in the server config
    NOTE: This does not create a ramdisk, it simply
    assumes you have mounted a ramdisk to the ramdisk
    folder

    Args:
        *args[0] (bool, optional): if this is set it
            sets the ramdisk config to this value.
            If this is not set it makes no changes.
        
        printer (function, optional): The function to
            display text. Defaults to print.

    Returns:
        bool: the state of the ramdisk after any changes
    """
    if args:
        enabled = str2bool(args[0])
        manager.ramdisk = enabled
    else:
        printer("ramdisk is "+("on" if manager.ramdisk else "off"))
    return manager.ramdisk



def set_property(args, printer=print):
    """sets a property in server.properties

    Args:
        key (str): the property to set
            value (str, optional): The value to set the property to
            deletes the property if None. Defaults to None.
        
        printer (function, optional): The function to
            display text. Defaults to print.

    Raises:
        TypeError: Type error if the value is of the wrong type
    """
    if not len(args):
        return curses.wrapper(tui_server_options)
    properties = manager.server_properties
    key = args[0]
    if len(args) > 1:
        value = args[1]
        if type(value) is str:
            properties[key] = value
            printer(f"Property \"{key}\" is now \"{value}\"")
        else:
            raise TypeError("Value must be str or empty")
    else:
        if key in properties:
            del properties[key]
            printer(f"Deleted property \"{key}\"")
    manager.server_properties = properties



def get_eula(args=[], printer=print):
    """Returns whether or not the eula has been
    agreed to

    Args:
        printer (function, optional): The function to
            display text. Defaults to print.

    Returns:
        bool: True if eula=true, false otherwise
    """
    if manager.eula:
        printer("EULA is signed")
        return True
    else:
        printer("EULA is not signed")
        return False



def send(args=[], printer=print):
    """Sends a command to the minecraft server

    Args:
        *args (str): the command to send, can be a string or list of strings
        printer (function, optional): The function to
            display text. Defaults to print.

    Returns:
        bool: returns True if the message was sent, False otherwise.
            Note this does not mean the server recieved or understood the message
            it simply means the service got the message and sent a reply
    """
    seperator = " "
    argString = seperator.join(args)
    printer(f"Sent command \"{' '.join(args)}\" to the server")
    return manager.send(argString)



def status(args=[], printer=print):
    """Returns the status of the Minecraft server

    Args:
        printer (function, optional): The function to
            display text. Defaults to print.

    Returns:
        bool: True if the server is running, false if it is not
    """
    if manager.status():
        printer("Server is running")
        return True
    else:
        printer("Server is off")
        return False

def stop_service(args=[],printer=print):
    """stops the mc-as-a-service service
    """
    printer("stopping service")
    manager.stop_service()
    printer("service stopped")

def install(args=[], printer=print):
    """Tells the service to install a minecraft server

    Args:
        *args[0] (str, optional): The version to install,
            opens up the TUI installer if not specified
        printer (function, optional): The function to
            display text. Defaults to print.

    Returns:
        bool: True if the install was successful, False otherwise 

    Raises:
        TypeError: When argument is not a string
    """
    if not args:
        version = version_selector.select()
    elif type(args[0]) is str:
        version = args[0]
    else:
        raise TypeError("Expected string as argument") 
    if manager.install(version):
        printer(f"Installed server of version {version}")
        return True
    else:
        printer("Could not install server")
        return False



def set_path(args=[], printer=print):
    """sets the path to the server launcher, relative to the server folder

    Args:
        *args[1] (str, optional): The path to the launcher to use, if None
            does not make any changes
        printer (function, optional): The function to
            display text. Defaults to print.

    Returns:
        str: returns the server path after any changes were made
    
    Raises:
        TypeError: Type error if the path is not a string
    """
    if len(args) == 0:
        path = manager.launch_path
        printer(f"Server launches from {path}")
        return path
    elif type(args[0]) is not str:
        raise TypeError
    path = args[0]
    manager.launch_path = path
    printer(f"Server now launches from {path}")
    return path


def launch_options(args=[], printer=print):
    """sets the path to the server launcher, relative to the server folder

    Args:
        *args (str, optional): The options to add
        printer (function, optional): The function to
            display text. Defaults to print.

    Returns:
        str: returns the launch options after any changes were made
    
    Raises:
        TypeError: Type error if the options is not a list of strings
    """
    if not len(args):
        options = manager.launch_options
        if manager.launch_options == []:
            printer("Server uses no launch options")
        else:
            printer(f"launch options are {'-'+' -'.join(options)}")
        return options
    if type(args[0]) is not list:
        if not all(isinstance(arg, str) for arg in args):
            raise TypeError
        if args[0].strip() == "":
            manager.launch_options = []
        else:
            manager.launch_options = args
    else:
        manager.launch_options = args[0]
        printer(f"launch options changed to {'-'+' -'.join(args[0])}")
    
    return args

def tui_launch_options(stdscr):
    """This is the TUI for selecting launch options
    """
    items = [curses_helpers.item_editor("Launch Path", set_path(printer=blank)),
             curses_helpers.item_editor("Launch Options"," ".join(launch_options(printer=blank))),
             curses_helpers.item_editor("Ramdisk",ramdisk(printer=blank))]
    menu = curses_helpers.list_editor(items)
    changes = menu.display(stdscr)
    for change in changes:
        if change[0] == "Launch Path":
            set_path(change[1], printer=blank)
        elif change[0] == "Launch Options":
            launch_options(change[1].split(), printer=blank)
        elif change[0] == "Ramdisk":
            ramdisk(change[1], printer=blank)

def tui_server_options(stdscr):
    """This is the TUI for changing server.properties settings
    """
    options = manager.server_properties
    new_options = deepcopy(options)
    default_options = manager.server_default_properties
    opt_list = []
    for option in default_options:
        if not option in options:
            opt_list.append(curses_helpers.item_editor(option, default_options[option]))
    for option in options: 
        opt_list.append(curses_helpers.item_editor(option, options[option]))
    sorter = lambda x: x.name
    opt_list.sort(key=sorter)
    items = curses_helpers.list_editor(opt_list)
    changed_list = items.display(stdscr)
    for item in changed_list:
        new_options[item[0]] = item[1]
    manager.server_properties = new_options
