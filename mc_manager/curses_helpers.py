import curses
from curses.textpad import Textbox, rectangle


class item_base():
    """The base class for menu items
    """
    def init_curses(self):
        """A few curses settings shared across all items
        """
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)

    def display(self, y_pos, key_x, value_x, stdscr, selected, formatting=0):
        """This is meant to be overloaded by a child
        """
        pass


class item_title(item_base):
    """class for a centered menu item
    """
    def __init__(self, title, on_change=None):
        self.title = title
        self.max_len = 0
        self.name = title
    def display(self, y_pos, stdscr, selected, formatting=0):
        self.init_curses()
        cols = stdscr.getmaxyx()[1]
        window = curses.newwin(1,len(self.title)+1,y_pos,int((cols/2)-len(self.title)/2))
        padding = curses.newwin(1,cols,y_pos,0)
        padding.erase()
        padding.addstr(" "*(cols-1))
        padding.refresh()
        window.erase()
        window.addstr(0,0,self.title, formatting)
        window.refresh()
        del window
        del padding
        if selected:
            return self.title
        return None


class item_editor(item_base):
    """class for a menu item with a key and editable value
    """
    def __init__(self, key, value, max_val_len=20):
        """This is a display item which has a key and an editable value

        Args:
            key (str): The key to be displayed
            value (str,int,float,bool): The value to be edited
            max_val_len (int, optional): The maximum length of the value field.
                Defaults to 20.
        """
        self.key=key
        self.value=value
        self.name = key
        if type(value) is str:
            self.validation = self.str_validator
        elif type(value) is int:
            self.validation = self.int_validator
        elif type(value) is float:
            self.validation = self.float_validator
        self.max_val_len = max_val_len
    def display(self, y_pos, key_x, value_x, stdscr, selected, formatting=0):
        """Displays the item

        Args:
            y_pos (int): The y position on stdscr for the item to be displayed
            key_x (int): the x position on stdscr for the key to be displayed
            value_x (int): the x position on stdscr for the value to be displayed
            stdscr (_CursesWindow): a curses windows or pad to use
            selected (bool): Whether or not this item is selected
            formatting (int, optional): a curses format to use. Defaults to 0.

        Returns:
            None, value: returns self.value if an edit was made, otherwise None
        """
        self.init_curses()
        key_window=curses.newwin(1,value_x-key_x,y_pos,key_x)
        value_window=curses.newwin(1,self.max_val_len,y_pos,value_x)
        changed=False
        if selected:
            if type(self.value) is bool:
                self.bool_validator(stdscr,value_window)
            else:
                curses.curs_set(1)
                self.box = Textbox(value_window)
                self.box.edit(self.validation)
                self.box=None
            changed=True
        key_window.erase()
        key_window.addstr(0,0,self.key, formatting)
        value_window.erase()
        value_window.addstr(str(self.value), formatting)
        key_window.refresh()
        value_window.refresh()
        del key_window
        del value_window
        return (self.key,self.value) if changed else None
    
    def str_validator(self, key):
        """This function maps a given keystroke to the desired response when
        the user is editing a value of type str

        Args:
            key (int): The key pressed

        Returns:
            int: the key to returns
        """
        if self.box == None:
            return
        if key == 27:
            return curses.ascii.BEL
        elif key == curses.KEY_BACKSPACE or key == 127:
            return 8
        elif key == curses.KEY_ENTER or key == 10 or key == 13:
            self.value=self.box.gather().strip()
            return curses.ascii.BEL
        else:
            return key
    def float_validator(self, key):
        """This function maps a given keystroke to the desired response when
        the user is editing a value of type float

        Args:
            key (int): The key pressed

        Returns:
            int: the key to returns
        """
        if self.box == None:
            return
        if key == 27:
            return curses.ascii.BEL
        elif key == curses.KEY_BACKSPACE or key == 127:
            return 8
        elif key == curses.KEY_ENTER or key == 10 or key == 13:
            self.value=float(self.box.gather().strip())
            return curses.ascii.BEL
        elif key == 46:
            gather = self.box.gather()
            # If dot hasn't been used and the string isn't empty
            if (not '.' in gather) and (gather.strip()):
                return key
        if key in range(48,58):  # allowed values
            return key
    def int_validator(self, key):
        """This function maps a given keystroke to the desired response when
        the user is editing a value of type int

        Args:
            key (int): The key pressed

        Returns:
            int: the key to returns
        """
        if self.box == None:
            return
        if key == 27:
            return curses.ascii.BEL
        elif key == curses.KEY_BACKSPACE or key == 127:
            return 8
        elif key == curses.KEY_ENTER or key == 10 or key == 13:
            in_val = self.box.gather().strip()
            if in_val != "":
                self.value=int(in_val)
            return curses.ascii.BEL
        if key in range(48,58):  # allowed values
            return key
    def bool_validator(self, stdscr, window):  # This one's special and runs without textbox
        """This function gets a keystroke and toggles self.value, exiting without
        changing on ESC and exiting with changes on ENTER

        Args:
            stdscr (_CursesWindow): The parent screen object
            window (_CursesWindow): The window object text is being written to

        Returns:
            int: the key to returns
        """
        value = self.value
        while True:
            key = stdscr.getch()
            if key == 27:
                return value
            elif key in [curses.KEY_UP, curses.KEY_DOWN, 
               curses.KEY_LEFT, curses.KEY_RIGHT, 32]:  # 32 is space
                value = not value
                window.erase()
                window.addstr(str(value), curses.A_STANDOUT)
                window.refresh()
            elif key == curses.KEY_ENTER or key == 10 or key == 13:
                self.value = value
                return value

class list_base():
    """base class for lists of items
    """
    def __init__(self, items):
        self.items = items
        self.selected = 0
        self.returnVal = None
        
    
    def display(self, stdscr):
        """Displays a list of items

        Args:
            stdscr (_CursesWindow): The window object to display to

        Returns:
            any: returns whatever the child class sets self.returnVal to
        """
        self.rows, self.cols = stdscr.getmaxyx()
        self.middle_col = int(self.cols/2)
        self.start = 0
        stdscr.erase()
        stdscr.refresh()
        self.pre_loop(stdscr)
        while True:
            self.rows, self.cols = stdscr.getmaxyx()
            if not self.loop(stdscr):
                break
            if not self.get_key(stdscr):
                break
        self.post_loop(stdscr)
        return self.returnVal
    
    def pre_loop(self, stdscr):
        """This is run before the main loop, and is available to be overloaded

        Args:
            stdscr (_CursesWindow): The window object to display to
        """
        pass
    
    def loop(self, stdscr):
        """This is the main loop, and is meant to be overloaded

        Args:
            stdscr (_CursesWindow): The window object to display to

        Returns:
            bool: True to continue loop, false otherwise
        """
        return True
    
    def post_loop(self, stdscr):
        """This is run after the loop completes and is available to be overloaded

        Args:
            stdscr (_CursesWindow): The window object to display to
        """
        pass
    
    def get_key(self, stdscr):
        """This function handles commonly used keys, 
        and calls overloadable functions to deal with them

        Args:
            stdscr (_CursesWindow): The window object to display to

        Returns:
            bool: True to continue the main loop, False to stop
        """
        key = stdscr.getch()
        if key == curses.KEY_DOWN:
            return self.key_down()
        elif key == curses.KEY_UP:
            return self.key_up()
        if key in [curses.KEY_ENTER, 10, 13]:
            return self.key_enter()
        elif key == 27:
            return False
        else:
            return True
    
    def key_enter(self):
        """This is a function called when enter is pressed
        it is available to be overloaded

        Returns:
            bool: True to continue the main loop, False to stop
        """
        return True
    
    def key_up(self):
        """This is a function called when the up key is pressed
        it is available to be overloaded, but calls sel_up() by default

        Returns:
            bool: True to continue the main loop, False to stop
        """
        return self.sel_up()

    def key_down(self):
        """This is a function called when the down key is pressed
        it is available to be overloaded, but calls sel_down() by default

        Returns:
            bool: True to continue the main loop, False to stop
        """
        return self.sel_down()
    
    def sel_up(self):
        """This function is called to move the cursor up
        """
        if self.selected == self.start:
            if self.start > 0:
                self.start -= 1
                self.selected -= 1
            else:
                self.selected = len(self.items)-1
                self.start = max(0,len(self.items)-self.rows)
        else:
            self.selected -= 1
        return True

    def sel_down(self):
        """This function is called to move the cursor down
        """
        if self.selected + 1 >= self.rows + self.start or self.selected >= len(self.items) - 1:
            if ((self.start + self.rows < len(self.items)) and (self.selected < len(self.items))):
                self.start += 1
                self.selected += 1
            else:
                self.selected = 0
                self.start = 0
        else:
            self.selected += 1
        return True

class list_editor(list_base):
    """class for a list of item_editor items
    """
    def __init__(self, items):
        """Calls parent init and also finds the
        largest sized string in the list of items given

        Args:
            items (list): a list of items which share the item_base parent
            to be displayed in the list
        """
        super().__init__(items)
        self.keylength = (
            max(
                map(
                    len,
                    (
                        (x.key if type(x) is item_editor else "" for x in self.items)
                    )
                   )
               )
        )
        self.edit = False
        return
    
    def pre_loop(self, stdscr):
        """Sets up the variable returnVal to be used as a list

        Args:
            stdscr (_CursesWindow): The window object to display to
        """
        self.returnVal = []
        return

    def loop(self, stdscr):
        """This is the function called in the loop
        inside the parent's display() function

        Args:
            stdscr (_CursesWindow): The window object to display to

        Returns:
            bool: true to continue the loop, false to stop it
        """
        for i in range(len(self.items)):
            if i >= self.start and i <= self.start + self.rows:
                if type(self.items[i]) is item_editor:
                    setting = self.items[i].display(
                                (i-self.start),
                                (self.middle_col-(self.keylength+2)),
                                (self.middle_col+2),
                                (stdscr),
                                (i==self.selected and self.edit),
                                (curses.A_STANDOUT if i==self.selected else 0))
                elif type(self.items[i]) is item_title:
                    self.items[i].display(
                                (i-self.start),
                                (stdscr),
                                (False),
                                (curses.A_STANDOUT if i==self.selected else 0))
            else:
                setting = None
            if type(setting) is tuple:
                self.returnVal.append(setting) # if changed, append new setting
        self.edit = False
        return True


    def key_enter(self):
        """This is the function called when enter is pressed

        Returns:
            bool: true to continue the loop
        """
        self.edit = True
        return True


# TODO: Replace with new list_h function using items
class select_h():
    def __init__(self, items, title=""):
        self.items = items
        self.title = title
    def display(self, stdscr):
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        selected=0
        while True:
            rows, cols = stdscr.getmaxyx()
            middle_column = int(cols / 2)
            middle_row = int(rows / 2)
            half_length_of_message = int(len(self.title) / 2)
            x_position = middle_column - half_length_of_message
            stdscr.erase()
            stdscr.addstr(0, x_position, self.title+"\n", curses.A_BOLD)
            for i in range(len(self.items)):
                # Get centered position
                half_length_of_message = int(len(" ".join(self.items)) / 2)
                y_position = middle_row
                x_position = middle_column - half_length_of_message
                # Print
                if selected == i:
                    stdscr.addstr(y_position, x_position +
                    (sum(map(len,self.items[0:i])))+i, self.items[i], curses.A_STANDOUT)
                else:
                    stdscr.addstr(y_position, x_position +
                    (sum(map(len,self.items[0:i])))+i, self.items[i])
            stdscr.refresh()
            key = stdscr.getch()
            if key == curses.KEY_RIGHT:
                selected = (selected + 1)%len(self.items)
            elif key == curses.KEY_LEFT:
                selected = (selected - 1)%len(self.items)
            elif key == curses.KEY_ENTER or key == 10 or key == 13:
                        return self.items[selected]
            elif key == 27:  # escape
                return None

# TODO: Replace with new list_menu function using items
class select_v():
    def __init__(self, items, title=""):
        self.items = items
        self.title = title
    def display(self, stdscr):
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        selected=0
        while True:
            rows, cols = stdscr.getmaxyx()
            middle_row = int(rows / 2)
            middle_column = int(cols / 2)
            top_row = int(middle_row-(len(self.items)/2))
            half_length_of_message = int(len(self.title) / 2)
            x_position = middle_column - half_length_of_message
            stdscr.erase()
            stdscr.addstr(0, x_position, self.title+"\n", curses.A_BOLD)
            for i in range(len(self.items)):
                # Get centered position
                half_length_of_message = int(len(self.items[i]) / 2)
                
                y_position = top_row
                x_position = middle_column - half_length_of_message
                # Print
                if selected == i:
                    stdscr.addstr(y_position+i, x_position, self.items[i], curses.A_STANDOUT)
                else:
                    stdscr.addstr(y_position+i, x_position, self.items[i])
            stdscr.refresh()
            key = stdscr.getch()
            if key == curses.KEY_DOWN:
                selected = (selected + 1)%len(self.items)
            elif key == curses.KEY_UP:
                selected = (selected - 1)%len(self.items)
            elif key == curses.KEY_ENTER or key == 10 or key == 13:
                        return self.items[selected]
            elif key == 27:  # escape
                return None

# TODO: Replace with new list_menu function using items
class select_v_scrolling():
    def __init__(self, items, title=""):
        self.items = items
        self.title = title
    def display(self, stdscr):
        rows, cols = stdscr.getmaxyx()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        self._selected = 0
        self._window = [0, min(rows - 2,len(self.items))]
        while True:
            rows, cols = stdscr.getmaxyx()
            middle_column = int(cols / 2)
            half_length_of_message = int(len(self.title) / 2)
            x_position = middle_column - half_length_of_message
            stdscr.erase()
            stdscr.addstr(0, x_position, self.title+"\n", curses.A_BOLD)
            
            for i in range(self._window[0], self._window[1]):
                # Get centered position
                half_length_of_message = int(len(self.items[i]) / 2)
                y_position = stdscr.getyx()[0]
                x_position = middle_column - half_length_of_message
                # Print
                if self._selected == i:
                    stdscr.addstr(y_position, x_position,self.items[i]+"\n", curses.A_STANDOUT)
                else:
                    stdscr.addstr(y_position, x_position,self.items[i]+"\n")
            stdscr.refresh()
            key = stdscr.getch()
            keydict = {
                curses.KEY_DOWN:self.key_down,
                curses.KEY_UP:self.key_up
                }
            if key in keydict:
                keydict[key]()
            elif key in [curses.KEY_ENTER, 10, 13]:
                return self.items[self._selected]
            elif key == 27:  # escape
                return None
    
    def key_up(self):
        if self._window[0] == self._selected:
            if self._window[0] > 1:
                self._window[0] -= 1
                self._window[1] -= 1
                self._selected -= 1
        else:
            self._selected -= 1

    def key_down(self):
        if self._window[1] == self._selected+1:
            if self._window[1] < len(self.items):
                self._window[0] += 1
                self._window[1] += 1
                self._selected += 1
        else:
            self._selected += 1 

if __name__ == "__main__":
    ed = list_editor([item_editor("one",1),
                      item_editor("Two","2"),
                      item_editor("Three",False),
                      item_editor("Two","2"),
                      item_editor("Three",False),
                      item_editor("Two","2"),
                      item_title("TITLE"),
                      item_editor("Three",False),
                      item_editor("Two","2"),
                      item_editor("Three",False),
                      item_editor("Two","2"),
                      item_editor("Three",False),
                      item_editor("Two","2"),
                      item_editor("Three",False),
                      item_editor("Four",True)])
    curses.wrapper(ed.display)