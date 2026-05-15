"""
A robust, lightweight, and heavily optimized custom Combobox implementation for Python Tkinter
applications using ttk.Entry and a detached tk.Toplevel listbox.
Designed from scratch to fix the layout limitations and styling rigidity of the native ttk.Combobox.


Key Features & Optimizations:
    Dynamic Grid Injection:
    Instantiates cleanly using unified geometry redirection (.grid() and .pack()), allowing it to blend
    seamlessly into complex layouts.
    
    In-Place Memory Mutation:
    Leverages Python slice mutation (ListForCombo[:] = NewList) to swap datasets dynamically on the fly.
    The dropdown adapts to data updates cleanly without breaking underlying memory references.
    
    Event Guarding: Protects key operational event methods (key_down, key_up, and button_release)
    using native component check assertions. This eliminates focus-timing race conditions and operating
    system window-lag crashes completely without introducing artificial after() delay loops.
    
    Advanced Text Interception & Trapping:
    Intercepts active keystrokes to allow typing search filters while navigating options natively via
    arrow keys, Return, Tab, and Escape.
    
    Universal Mouse Wheel Scroll Engine:
    Integrates cross-platform scroll wheel capabilities that intercept OS-specific calls seamlessly
    across Windows, macOS, and Linux variants.

    Seamless Resize Handling:
    The list will stay in the right position regardless of form resize/restore.
    In addition, if the list will not fit below the text, it will show above provided there is more space.
    It will also snap to the edge of the monitor if the Entry itself is positioned past the edge of the screen.
    Supports multiple monitors, however due to the limitations of tk across multiple platforms, these need
    to be passed in from the project using platform specific methods.
    If not passed in, the values of the default monitor will be used as a failback which will work on single
    monitor system and on multi monitor default to just simply showing below the Entry component, the same
    as if the mid point of the Entry is outside any known monitor.
    The passed in monitors are expected to be a list of dictionaries with keys of left, top, right, bottom.
    A ctypes class has been included in the test code below for the purpose of testing on windows.


Basic Operation:
    Tab into combo:
    Nothing happens, you may only be tabbing past it.
    Start typing or use PgUp, PgDwn, Up/Down arrow and the options box opens.

    Click into combo:
    Clicking within existing text will not show the combo to allow entering free, non-validated text.
    Clicking within blank space will show the combo.

    Editing:
    The combo will show as long as there is matching text, then it will disappear.
    If the typed text matches an entry, it will auto-correct case should you choose to click into the next field.
    Selection is done using the standard Click, Enter and Tab methods.

    Data Validation:
    Using the data validation option resets the text to an empty string.
    This can then be handled in the data validation of the form.

Note:
    This script can be run as is for basic testing purposes.
    It also shows different ways of passing arguments to the class.
    This code comes without warranties of any kind on a 'as is where is' basis.
    Written and tested on a Ryzen 5 3600 with Win11, Python 3.14.3 and Idle.

Lastly:
    Please feel free to use, modify, improve, and repost this as you see fit.
"""


import tkinter as tk
from tkinter import ttk, font as tkfont


#====================================================================================================
#====================================================================================================
# ***** class to get monitors, found on the internet, win32 only *****
#====================================================================================================
#====================================================================================================
import ctypes
from ctypes import wintypes


# 1. Define required Win32 Structs
class RECT(ctypes.Structure):
    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long)
    ]

class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize', wintypes.DWORD),
        ('rcMonitor', RECT),
        ('rcWork', RECT),
        ('dwFlags', wintypes.DWORD)
    ]

# 2. Define the Callback Prototype required by EnumDisplayMonitors
# Prototype: BOOL CALLBACK MonitorEnumProc(HMONITOR, HDC, LPRECT, LPARAM)
MONITORENUMPROC = ctypes.WINFUNCTYPE(
    wintypes.BOOL, 
    wintypes.HMONITOR, 
    wintypes.HDC, 
    ctypes.POINTER(RECT), 
    wintypes.LPARAM
)

def win32_get_monitors():
    """Queries Windows OS directly to fetch exact virtual monitor dimensions."""
    monitors_list = []

    if root.tk.call('tk', 'windowingsystem') != 'win32': return monitors_list # added in case of testing on non-win32

    # Make the call High-DPI Aware to prevent Windows from virtualizing/lying about sizes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2) # Per-monitor DPI aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware() # Fallback for older Windows systems
        except Exception:
            pass

    def enum_callback(hMonitor, hdcMonitor, lprcMonitor, lParam):
        # Initialize the info struct with its own byte size
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        
        # Populate the struct via the active monitor handle
        if ctypes.windll.user32.GetMonitorInfoW(hMonitor, ctypes.byref(mi)):
            r = mi.rcMonitor
            w = r.right - r.left
            h = r.bottom - r.top
            
            monitors_list.append({
                'left': r.left,
                'top': r.top,
                'right': r.right,
                'bottom': r.bottom,
                'width': w,
                'height': h
            })
        return True  # Return True to keep enumerating next monitors

    # Trigger enumeration across the Windows user32 subsystem
    callback_instance = MONITORENUMPROC(enum_callback)
    ctypes.windll.user32.EnumDisplayMonitors(None, None, callback_instance, 0)
    
    return monitors_list
#====================================================================================================
#====================================================================================================
# ***** monitor class end *****
#====================================================================================================
#====================================================================================================




#====================================================================================================
#====================================================================================================
# ***** custom combo class start *****
#====================================================================================================
#====================================================================================================
class CuCo:
    def __init__(self, 
                 parent: tk.Widget, 
                 tplFont: tuple = ('Verdana', 14, 'bold'), 
                 strStyle: str = 'TEntry', 
                 intTextWidth: int = 20, 
                 intArrowSize: int = 14, 
                 intListRows: int = 5, 
                 lstListValues: list = None, 
                 blnValidate: bool = True,
                 lstMonitors: list = None):

        # Validation & Root Setup
        if parent is None: raise ValueError("CuCo requires a parent.")

        # Variable Initialization - Fixed Values
        self.root = parent.winfo_toplevel()

        self.tplFont = tplFont or ('Verdana', 14, 'bold')
        self.strStyle = strStyle or 'TEntry'
        self.intTextWidth = intTextWidth or 20
        self.intArrowSize = intArrowSize or 14
        self.intListRows = intListRows or 5
        self.lstListValues = lstListValues if lstListValues is not None else []
        self.blnValidate = blnValidate if blnValidate is not None else True
        self.lstMonitors = lstMonitors or [{'left': 0, 'top': 0, 'right': self.root.winfo_screenwidth(), 'bottom': self.root.winfo_screenheight()}]

        # Variable Initialization - Placeholders
        self.lstValuesSorted = []
        self.intValuesCount = 0
        self.intListLines = 0
        self.dictNavigate = {'Up': -1, 'Down': 1, 'Prior': -1, 'Next': 1}
        
        self.lstBindings = []

        self.blnWinVisible = False
        self.blnNoKeyUp = False
        self.blnFirstShow = True
        self.blnComboActive = False

        self.win = None
        self.sb = None
        self.lb = None
        self.intWinHeight = 0

        # Create the Main Entry (txt)
        self.txt = ttk.Entry(parent, style=self.strStyle, width=self.intTextWidth, font=self.tplFont)
        self.txt.bind("<FocusIn>", self.txt_focus_in, add='+')
        self.txt.bind('<ButtonRelease-1>', self.txt_mouse_up, add='+')
        self.txt.bind('<KeyPress>', self.key_down, add='+')
        self.txt.bind('<KeyRelease>', self.key_up, add='+')
        self.txt.bind("<FocusOut>", self.focus_out, add='+')
#====================================================================================================
    def dropdown_create(self):
        # Create the Dropdown Window (Toplevel)
        self.win = tk.Toplevel(self.root)
        self.win.withdraw()
        self.win.wm_attributes('-topmost', True)
        self.win.wm_overrideredirect(True)

        # Style the scrollbar
        ttk.Style(self.win).theme_use('clam')
        ttk.Style(self.win).configure('winDD.Vertical.TScrollbar', arrowsize=self.intArrowSize)

        # Create Scrollbar
        self.sb = ttk.Scrollbar(self.win, orient=tk.VERTICAL, style='winDD.Vertical.TScrollbar', command=self.sb_scroll)
        self.sb.pack(side='right', fill='y')

        # Create List
        self.SVlstValuesSorted = tk.StringVar(value=self.lstValuesSorted)
        self.lb = tk.Listbox(self.win,
                        listvariable=self.SVlstValuesSorted,
                        font=self.tplFont, borderwidth=1, relief="solid", 
                        activestyle='none', selectbackground='#0078d7',
                        takefocus=True, exportselection=False,
                        selectmode="single",
                        yscrollcommand=self.sb.set)
        self.lb.pack(side="left", fill="both", expand=True)

        # Bindings for the Dropdown components
        self.lb.bindtags((str(self.win), str(self.lb)))
        self.lb.bind('<Button-1>', self.lb_mouse_down)
        self.lb.bind('<MouseWheel>', self.mouse_scroll)     # Windows & macOS
        self.lb.bind('<Button-4>', self.mouse_scroll)       # Linux Scroll Up
        self.lb.bind('<Button-5>', self.mouse_scroll)       # Linux Scroll Down
        self.win.bind('<KeyPress>', self.key_down)
        self.win.bind('<KeyRelease>', self.key_up)
        self.win.bind('<FocusOut>', self.focus_out)
        self.win.bind('<Destroy>', self.win_on_destroy)

        self.blnComboActive = False
#====================================================================================================
    def txt_focus_in(self, e):
        if self.win is None: self.dropdown_create()

        if self.blnComboActive: return

        # Refresh list data and set associated values
        self.lstValuesSorted = sorted(self.lstListValues, key=str.casefold) if self.lstListValues else ['-- None --']
        self.SVlstValuesSorted.set(self.lstValuesSorted)
        self.intValuesCount = len(self.lstValuesSorted)
        self.intListLines = min(self.intListRows, self.intValuesCount)
        self.dictNavigate = {'Up': -1, 'Down': 1, 'Prior': -self.intListLines, 'Next': self.intListLines}

        # Set window height here rather than in dropdown_create in case new list has fewer items than original List Lines
        self.lb.config(height=self.intListLines)
        self.win.update_idletasks()
        self.intWinHeight = self.win.winfo_reqheight()

        self.blnWinVisible = False # keeps track of window state, deiconify/withdraw  
        self.blnNoKeyUp = False    # used by key_down to tell key_up to not do anuthing
        self.blnFirstShow = True   # handle (first key up event when tabbing) or (first mouse up when clicking) into txt
        self.blnComboActive = True # allows for navigation between txt and winDD

        # Setup root window sync bindings (destroyed in focus_out)
        self.lstBindings = [
            (self.root, '<Button-1>', self.root.bind('<Button-1>',self.root_mouse_down, add='+')),
            (self.root, '<Configure>', self.root.bind('<Configure>', self.root_configure, add='+'))
        ]
#====================================================================================================
    def root_mouse_down(self, e=None):
        if self.blnWinVisible and self.win and self.win.winfo_exists():
            self.win.withdraw(); self.blnWinVisible = False
#====================================================================================================
    def root_configure(self, e):
        if self.blnWinVisible and (e.widget == self.root) and self.win and self.win.winfo_exists():
            self.win.withdraw(); self.blnWinVisible = False
#====================================================================================================
    def dropdown_show(self):
        x = self.txt.winfo_rootx()
        y = self.txt.winfo_rooty()
        w = self.txt.winfo_width()
        h = self.txt.winfo_height()
        xc = x + (w // 2)
        yc = y + (h // 2)

        xx = x
        yy = y + h
        
        m = next((m for m in self.lstMonitors if m['left'] <= xc <= m['right'] and m['top'] <= yc <= m['bottom']), None)
        if m:
            # Top/Bottom
            if (yy + self.intWinHeight) > m['bottom']:
                space_below = m['bottom'] - yy
                space_above = y - m['top']
                if space_above > space_below:
                    yy = y - self.intWinHeight

            # Left/Right
            if xx < m['left']:
                xx = m['left']
            elif (xx + w) > m['right']:
                xx = m['right'] - w

        self.win.wm_geometry(f'{w}x{self.intWinHeight}+{xx}+{yy}')
        
        self.win.deiconify(); self.blnWinVisible = True
#====================================================================================================
    def mouse_scroll(self, e):
        if self.lb and self.lb.winfo_exists():
            # Linux systems use Button-4 and Button-5 events
            if e.num == 4:
                self.lb.yview_scroll(-1, "units")
            elif e.num == 5:
                self.lb.yview_scroll(1, "units")
            # Windows and macOS use the MouseWheel event with a delta value
            else:
                # e.delta is usually 120 or -120 on Windows; can be small floats on macOS
                direction = -1 if e.delta > 0 else 1
                self.lb.yview_scroll(direction, "units")
            return "break" # Prevents double-scrolling bugs
#====================================================================================================
    def sb_scroll(self, *args):
        try:
            if len(args) > 2 and args[0] == 'scroll' and args[2] == 'pages':
                self.lb.yview(max(0, self.lb.index('@0,0') + (int(args[1]) * self.intListLines)))
            else:
                self.lb.yview(*args)
        except: pass
#====================================================================================================
    def get_list_index(self, strPrefix):
        if not strPrefix: return -1

        strPrefix = strPrefix.casefold()
        return next((i for i, s in enumerate(self.lstValuesSorted) if s.casefold().startswith(strPrefix)), -1)
#====================================================================================================
    def lb_move_to(self, intIndex):
        self.lb.selection_clear(0, tk.END)
        self.lb.activate(intIndex)
        self.lb.selection_set(intIndex)
        self.lb.yview(max(0, intIndex - (self.intListLines // 2)))
#====================================================================================================
    def lb_mouse_down(self, e=None):
        intIndex = self.lb.nearest(e.y) if e else self.lb.index('active')
        self.txt.delete(0, tk.END)
        self.txt.insert(0, self.lstValuesSorted[intIndex])
        self.win.withdraw(); self.blnWinVisible = False
#====================================================================================================
    def key_down(self, e):
        if self.win and self.win.winfo_exists():
            match e.keysym:
                case 'Return' if self.blnWinVisible:
                    self.lb_mouse_down()
                    self.blnNoKeyUp = True
                    return 'break'

                case 'Tab' if self.blnWinVisible:
                    if self.txt.get():
                        self.lb_mouse_down()

                    oFocusNext = self.txt.tk_focusNext()
                    if oFocusNext:
                        oFocusNext.focus_set()

                    self.blnNoKeyUp = True
                    return 'break'

                case 'Escape':
                    self.win.withdraw(); self.blnWinVisible = False
                    self.blnNoKeyUp = True
                    return 'break'

                case 'Up' | 'Down' | 'Prior' | 'Next':
                    if self.blnWinVisible:
                        new_idx = max(0, min(self.lb.index(tk.ACTIVE) + self.dictNavigate[e.keysym], self.intValuesCount - 1))
                        self.lb_move_to(new_idx)
                    else:
                        self.key_up()
                        self.dropdown_show()

                    self.blnNoKeyUp = True
                    return 'break'
            
            if e.widget in (self.win, self.lb):
                match e.keysym:
                    case 'BackSpace':
                        intCursorPosition = self.txt.index(tk.INSERT)
                        if intCursorPosition > 0:
                            self.txt.delete(intCursorPosition - 1)
                        return 'break'

                    case 'Delete':
                        intCursorPosition = self.txt.index(tk.INSERT)
                        self.txt.delete(intCursorPosition)
                        return 'break'

                    case _ if e.char and e.char.isprintable():
                        self.txt.insert(tk.INSERT, e.char)
                        return 'break'
#====================================================================================================
    def key_up(self, e=None):
        if self.win and self.win.winfo_exists():
            if self.blnNoKeyUp: self.blnNoKeyUp = False; return
            
            strPrefix = self.txt.get()
            intNewIndex = 0 if not strPrefix else self.get_list_index(strPrefix)
            self.lb_move_to(max(0, intNewIndex))
            
            if self.blnFirstShow:
                self.blnFirstShow = False
            elif e:
                if intNewIndex == -1:
                    self.win.withdraw(); self.blnWinVisible = False
                else:
                    if self.txt.index(tk.INSERT) == self.txt.index(tk.END):
                        if strPrefix.casefold() == self.lstValuesSorted[intNewIndex].casefold():
                            self.txt.delete(0, tk.END)
                            self.txt.insert(0, self.lstValuesSorted[intNewIndex])

                    if not self.blnWinVisible: self.dropdown_show()
#====================================================================================================
    def txt_mouse_up(self, e):
        if self.win and self.win.winfo_exists():
            if self.blnFirstShow:
                self.blnFirstShow = False

            self.key_up()
            if self.txt.index(tk.INSERT) == self.txt.index(tk.END):
                if not self.blnWinVisible: self.dropdown_show()
            else:
                self.win.withdraw(); self.blnWinVisible = False
#====================================================================================================
    def focus_out_after_idle(self):
        oNewFocusWidget = self.root.focus_get()

        if oNewFocusWidget == None:
            if self.blnWinVisible and self.win and self.win.winfo_exists():
                self.win.withdraw(); self.blnWinVisible = False
            
        elif (oNewFocusWidget == self.txt) or (oNewFocusWidget.winfo_toplevel() == self.win):
            pass

        else:
            if self.blnWinVisible and self.win and self.win.winfo_exists():
                self.win.withdraw(); self.blnWinVisible = False

            if self.blnValidate:
                strPrefix = self.txt.get()
                intIndex = self.get_list_index(strPrefix)
                if intIndex == -1 or strPrefix != self.lstValuesSorted[intIndex]:
                    self.txt.delete(0, tk.END)

            for oWidget, strEvent, strID in self.lstBindings:
                try: oWidget.unbind(strEvent, strID)
                except: pass
            self.lstBindings = []
            
            self.blnComboActive = False
            self.txt.selection_clear()
#====================================================================================================
    def focus_out(self, e):
        self.win.after_idle(self.focus_out_after_idle)
#====================================================================================================
    def win_on_destroy(self, e):
        if e.widget == self.win:
            self.win = None
            
            for oWidget, strEvent, strID in self.lstBindings:
                try: oWidget.unbind(strEvent, strID)
                except: pass
            self.lstBindings = []
#====================================================================================================
    def get(self):
        return self.txt.get()
#====================================================================================================
    def set(self, value):
        self.txt.delete(0, tk.END)
        self.txt.insert(0, value)
#====================================================================================================
    def delete(self, first, last=tk.END):
        self.txt.delete(first, last)
#====================================================================================================
    def grid(self, **kwargs):
        self.txt.grid(**kwargs)
#====================================================================================================
    def pack(self, **kwargs):
        self.txt.pack(**kwargs)
#====================================================================================================
#====================================================================================================
# ***** custom combo class end *****
#====================================================================================================
#====================================================================================================




#====================================================================================================
#====================================================================================================
# ***** test script below *****
#====================================================================================================
#====================================================================================================
root = tk.Tk()
root.state('zoomed')

ttk.Style().theme_use('clam')
tplFont = ('Cascadia Mono', 22, 'bold')

ttk.Style().configure('Base.TLabel', relief='flat', borderwidth=0, font=tplFont)
ttk.Style().configure('Base.TEntry', relief='flat', borderwidth=0, fieldbackground="lightyellow")

countries = [
    'Antigua and Barbuda', 'Bahamas', 'Barbados', 'Belize', 'Canada',
    'Costa Rica', 'Cuba', 'Dominica', 'Dominican Republic', 'El Salvador',
    'Grenada', 'Guatemala', 'Haiti', 'Honduras', 'Jamaica', 'Mexico',
    'Nicaragua', 'Saint Kitts and Nevis', 'Panama', 'Saint Lucia', 
    'Saint Vincent and the Grenadines', 'Trinidad and Tobago', 'United States of America']
animals = [
    'Zebra', 'Alligator', 'Alpaca', 'Antelope', 'Bat', 'Bear', 'Beaver', 'Buffalo', 'Camel',
    'Cat', 'Cheetah', 'Chimpanzee', 'Cow', 'Crocodile', 'Deer', 'Dolphin', 'Eagle', 'Elephant',
    'Fox', 'Giraffe', 'Goat', 'Horse', 'Kangaroo', 'Lion', 'Monkey', 'Panda', 'Penguin',
    'Rabbit', 'Shark', 'Tiger', 'Whale', 'Wolf', 'Aardvark']

lstMonitors = win32_get_monitors()


#-----
ttk.Label(root, text='freestyle, choose or type anything you want:', style='Base.TLabel', width=71).grid(row=0, column=0, columnspan=2, sticky='w', padx=(10, 0))

ttk.Label(root, text='Combo 1:', style='Base.TLabel', width=10).grid(row=1, column=0, sticky='w', padx=(10, 0))
myCuCo1 = CuCo(root, tplFont, 'Base.TEntry', 60, 22, 5, countries, False) # all arguments passed positionally, lstMonitors not supplied
myCuCo1.grid(row=1, column=1, sticky='w', padx=(10, 0))
myCuCo1.set('yesterday was a rainy day')
#-----
root.rowconfigure(2, minsize=50)
#-----
frame1 = ttk.Frame(root, padding='0')
frame1.grid(row=3, column=0, columnspan=2, sticky='nsew')

ttk.Label(frame1, text='combo with default font/style and data validation, packed in a frame,', style='Base.TLabel', width=71).pack(side='top', padx=(10, 0))
ttk.Label(frame1, text='monitors passed in, now repositions at edges of multiple monitors:', style='Base.TLabel', width=71).pack(side='top', padx=(10, 0))

frame2 = ttk.Frame(root, padding='0')
frame2.grid(row=4, column=0, columnspan=2, sticky='nsew')
ttk.Label(frame2, text='Combo 2:', style='Base.TLabel', width=10).pack(side='left', padx=(10, 0))
myCuCo2 = CuCo(frame2, None, None, 10, 14, 8, animals, True, lstMonitors) # arguments passed positionally but using None for default values
myCuCo2.pack(side='left', padx=(10, 0))
myCuCo2.set(myCuCo2.lstListValues[0])
#-----
root.rowconfigure(5, minsize=50)
#-----
ttk.Label(root, text='dynamic list change:', style='Base.TLabel', width=71).grid(row=6, column=0, columnspan=2, sticky='w', padx=(10, 0))

lstToPass = []
def assign_countries():
    lstToPass[:] = countries

def assign_animals():
    lstToPass[:] = animals

button_container = ttk.Frame(root)
button_container.grid(row=7, column=1, padx=5, pady=5, sticky="nsew")

# Button 1: Assign Countries
btn_countries = ttk.Button(button_container, text="Countries", command=assign_countries)
btn_countries.grid(row=0, column=0, padx=(0, 5), sticky="w")

# Button 2: Assign Animals
btn_animals = ttk.Button(button_container, text="Animals", command=assign_animals)
btn_animals.grid(row=0, column=1, padx=(5, 0), sticky="w")

ttk.Label(root, text='Combo 3:', style='Base.TLabel', width=10).grid(row=8, column=0, sticky='w', padx=(10, 0))
myCuCo3 = CuCo(root, tplFont=tplFont, strStyle='Base.TEntry', intTextWidth=22, intArrowSize=22, lstListValues=lstToPass) # selected arguments passed by name
myCuCo3.grid(row=8, column=1, sticky='w', padx=(10, 0))
myCuCo3.set('-- None --')

root.mainloop()
