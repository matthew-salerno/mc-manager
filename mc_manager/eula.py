import app_constants
import curses
import urllib3
import json
import re
import textwrap
from time import sleep
from html.parser import HTMLParser

https = urllib3.PoolManager()
const = app_constants.constants()

# NOTE TODO: This file is a huge mess cobbled together quickly and without much thought.
# I plan on eventually rewriting and documenting it but for now it is fairly low
# priority. On a high level all it does is read the eula to the user and return
# true or false depending on what they answer.
# In short:
# I know my O values are terible
# I know this needs more comments
# I know this is not readable
# I will get around to it *eventually* 

class eula():
    def __init__(self):
        self.strings=[]
    def addstr(self, string):
        if self.strings:
            string = self.strings[-1] + string  # Combine with newest
            self.strings.pop()  # remove newest
        for substring in re.split('(<[^>]*>)',string):
            substring=re.sub('\n','',substring)
            substring=re.sub(' +',' ',substring)
            # so long as it's not empty
            if substring and not re.match('^ *$',substring):
                self.strings.append(substring)  # add it back in

    def curse_all(self, pad, stdscr, pos=0):
        pad.erase()
        format_dict = {"<h1>":False, "<h2>":False, "<ul>":False, "<strong>":False, "<sup>":False}
        pad_cols = pad.getmaxyx()[1]

        for string in self.strings:
            # Find begin format
            y_position, x_position = pad.getyx()
            if string[0] == '<':
                if string in format_dict:
                    format_dict[string]=True
                elif string == "<p>":
                    pad.addstr("    ")
                #find end format
                elif string[1]=='/' and len(string) < 10:
                    string = re.sub('/','',string)
                    if string in format_dict:
                        format_dict[string]=False
                    elif string == "<p>":
                        y_position += 1
                        pad.move(y_position,0)
                continue
            
            # apply formatting
            string_format = 0
            
            if not format_dict["<sup>"]:
                if format_dict["<ul>"]:  # Underline
                    string_format = string_format | curses.A_UNDERLINE
                if format_dict["<strong>"]:  # Bold
                    string_format = string_format | curses.A_BOLD
                if format_dict["<h1>"] or format_dict["<h2>"]:  # Headers
                    string_format = string_format | curses.A_BOLD | curses.A_UNDERLINE
                    middle_column = int(pad_cols / 2)
                    string_list = textwrap.wrap(string, pad_cols-2)
                    string = ""
                    y_position += 1
                    for line in string_list:
                        half_length_of_message = int(len(line) / 2)
                        x_position = middle_column - half_length_of_message
                        pad.addstr(y_position, x_position, line, string_format)
                        y_position += 1
                        pad.move(y_position,0)
                        
                else:
                    string = textwrap.fill(string, pad_cols-2, initial_indent=' '*x_position, drop_whitespace=True)
                    string = re.sub('\n ', '\n', string)
                    string = string[x_position:]
                    pad.addstr(y_position, x_position, string, string_format)
                lines, cols = stdscr.getmaxyx()
                pad.refresh(pos,0,1,2,lines - 2, cols-2)
            
    def get_lines(self, cols):
        numLines = 0
        paragraph = ""

        #Logic:
        # If end of paragraph, see how much text was seen since previous text and run textwrap to 
        #  determine how many lines it was
        # If end of header, same as paragraph but add 1
        # If this was any other tag, ignore.
        # If just plain text, add to the paragraph variable to keep track of previous text

        for string in self.strings:
            if string == "</p>":
               parsed = textwrap.wrap("    " + paragraph, width=cols)
               numLines += len(parsed)
               paragraph = ""
            elif re.match("^</h[1-8]>$", string):
               parsed = textwrap.wrap(paragraph, width=cols)
               numLines += 1 + len(parsed) #+1 for the newline above
               paragraph = ""
            elif string[0] == "<":
               continue
            else:
               paragraph += string
        return numLines

class EULA_HTML_Parser(HTMLParser):
    def __init__(self, print_func=print):
        super().__init__()
        self.display=print_func
        self._on = False
        self._on_tag = 'div'
        self._on_attr = ('id', 'terms-text')
        self._off_tag = 'div'
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == self._on_tag:
            if self._on_attr in attrs:
                self._on = True
                return
        if not self._on:
            return
        # get links
        if tag == "a":
            for attr in attrs:
                if attr[0] == "href":
                    self.links.append(attr[1])

        self.tagger(tag, True)

    def handle_endtag(self, tag):
        if not self._on:
            return
        if tag == self._off_tag:
            self._on = False
            # Add links to the end
            for i in range(len(self.links)):  # add links at the end
                self.links[i] = f"<p>[{i+1}]{self.links[i]}</p>"
                self.display(self.links[i])
            return
        self.tagger(tag, False)

    def handle_data(self, data):
        if self._on:
            self.display(data)
    def tagger(self, tag, start):
        if not self._on:
            return
        start_dict={
            "li":"<p><sup>* </sup>", # sup is my own tag, for suppress, it temporarily turns off tags
            "a":"<ul>",
        }
        end_dict={
            "li":"</p>",
            "a":f"</ul> [{len(self.links)}]"
        }
        tag_dict=(start_dict if start else end_dict)
        if tag in tag_dict:
            self.display(tag_dict[tag])
        else:
            self.display(f"<{'/' if not start else ''}{tag}>")

def eula_render(stdscr):
    max_size = (5,25) # Mostly Arbitrarily chosen
    lines, cols = stdscr.getmaxyx()
    the_eula=eula()
    parser = EULA_HTML_Parser(the_eula.addstr)
    parser.feed(https.request('GET',const.EULA_URL).data.decode("utf-8"))
    
    pos = 0
    agree = False
    curses.curs_set(0)
    stdscr.clear()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    
    #Pad will put 2 spaces on the left and right, hence the -4.
    #You get that the total spacing is 4. Hence run cols-4 in the call
    #The +2 comes from the top and bottom line.
    # win_buffer is a buffer amount to soak up quick window resizes
    win_buffer = 5
    numLines = the_eula.get_lines(cols-4) + 2 + win_buffer

    eulapad = curses.newpad(numLines,cols-2)
    the_eula.curse_all(eulapad, stdscr, pos)
    while True:
        last_lines, last_cols = lines, cols
        lines, cols = stdscr.getmaxyx()
        stdscr.erase()
        if lines < max_size[0] or cols < max_size[1]:
            curses.resize_term(max_size[0], max_size[1])
            lines, cols = stdscr.getmaxyx()
        
        stdscr.addstr(lines - 1,4,"I agree", curses.A_STANDOUT if agree else 0)
        stdscr.addstr(lines - 1, cols - 19,"I do not agree", 0 if agree else curses.A_STANDOUT)
        stdscr.refresh()
        
        if cols == last_cols and lines == last_lines:  # If the window hasn't changed
            eulapad.refresh(pos,0,1,2,lines - 2, cols - 2)
            eula_length=eulapad.getmaxyx()[0]
        else:
            numLines = the_eula.get_lines(cols - 4) + 2 + win_buffer
            eulapad.resize(numLines,cols-2)
            eula_length=eulapad.getmaxyx()[0]
            if pos > (eula_length - lines - win_buffer):
                pos = (eula_length - lines - win_buffer)
            the_eula.curse_all(eulapad, stdscr, pos)
            
        key = stdscr.getch()
        if key == curses.KEY_UP and pos > 0:
            pos -= 1
        elif key == curses.KEY_DOWN and pos < (eula_length - lines - win_buffer):
            pos += 1
        elif key == curses.KEY_RIGHT:
            agree = False
        elif key == curses.KEY_LEFT:
            agree = True
        elif key == curses.KEY_ENTER or key == 10 or key == 13:
            break
    return agree

def eula_check(stdscr):
    try:
        return eula_render(stdscr)
    except curses.error:
        print("Window is too small!")
        raise
if __name__ == "__main__":
    print(curses.wrapper(eula_check))
