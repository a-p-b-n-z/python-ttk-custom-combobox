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
    
    Possible improvements:
    Unmatched multi monitor support for handling the list below or above.
    Noticed the list being modal when Alt-Tabbing, suggest the ESC key ...
"""


#====================================================================================================
#====================================================================================================
# ***** class start *****
#====================================================================================================
#====================================================================================================
import tkinter as tk
from tkinter import ttk, font as tkfont

class CuCo:
    def __init__(self, 
                 parent: tk.Widget, 
                 tplFont: tuple = ('Verdana', 14, 'bold'), 
                 strStyle: str = 'TEntry', 
                 intTextWidth: int = 20, 
                 intArrowSize: int = 14, 
                 intListRows: int = 5, 
                 lstListValues: list = None, 
                 blnValidate: bool = True):

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

        self.intScreenHeight = self.root.winfo_screenheight()

        # Variable Initialization - Placeholders
        self.lstValuesSorted = []
        self.intValuesCount = 0
        self.intListLines = 0
        self.dictNavigate = {'Up': -1, 'Down': 1, 'Prior': -1, 'Next': 1}
        
        self.lstBindings = []

        self.winDD_Visible = False
        self.blnNoKeyUp = False
        self.blnFirstShow = True
        self.blnComboActive = False

        self.winDD = None
        self.sb = None
        self.lb = None
        self.winDD_height = 0

        # Create the Main Entry (txtCombo)
        self.txtCombo = ttk.Entry(parent, style=self.strStyle, width=self.intTextWidth, font=self.tplFont)
        self.txtCombo.bind("<FocusIn>", self.fShowDD, add='+')
        self.txtCombo.bind('<ButtonRelease-1>', self.button_release, add='+')
        self.txtCombo.bind('<KeyPress>', self.key_down, add='+')
        self.txtCombo.bind('<KeyRelease>', self.key_up, add='+')
        self.txtCombo.bind("<FocusOut>", self.focus_out, add='+')
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

    def MakeDD(self):
        # Create the Dropdown Window (Toplevel)
        self.winDD = tk.Toplevel(self.root, name='cucowindd')
        self.winDD.withdraw()
        self.winDD.wm_attributes('-topmost', True)
        self.winDD.wm_overrideredirect(True)

        # Style the scrollbar
        ttk.Style(self.winDD).theme_use('clam')
        ttk.Style(self.winDD).configure('winDD.Vertical.TScrollbar', arrowsize=self.intArrowSize)

        # Create Scrollbar
        self.sb = ttk.Scrollbar(self.winDD, orient=tk.VERTICAL, style='winDD.Vertical.TScrollbar', command=self.scrollbar_scroll)
        self.sb.pack(side='right', fill='y')

        # Create List
        self.SVlstValuesSorted = tk.StringVar(value=self.lstValuesSorted)
        self.lb = tk.Listbox(self.winDD,
                        listvariable=self.SVlstValuesSorted,
                        font=self.tplFont, borderwidth=1, relief="solid", 
                        activestyle='none', selectbackground='#0078d7',
                        takefocus=True, exportselection=False,
                        selectmode="single",
                        yscrollcommand=self.sb.set)
        self.lb.pack(side="left", fill="both", expand=True)

        # Bindings for the Dropdown components
        self.lb.bindtags((str(self.winDD), str(self.lb)))
        self.lb.bind('<Button-1>', self.item_clicked)
        self.lb.bind('<MouseWheel>', self.mouse_scroll)     # Windows & macOS
        self.lb.bind('<Button-4>', self.mouse_scroll)       # Linux Scroll Up
        self.lb.bind('<Button-5>', self.mouse_scroll)       # Linux Scroll Down
        self.winDD.bind('<KeyPress>', self.key_down)
        self.winDD.bind('<KeyRelease>', self.key_up)
        self.winDD.bind('<FocusOut>', self.focus_out)
        self.winDD.bind('<Destroy>', self.on_destroy)

        self.blnComboActive = False
#====================================================================================================
    def fShowDD(self, e):
        if self.winDD is None: self.MakeDD()

        if self.blnComboActive: return

        # Refresh list data and set associated values
        self.lstValuesSorted = sorted(self.lstListValues, key=str.casefold) if self.lstListValues else ['-- None --']
        self.SVlstValuesSorted.set(self.lstValuesSorted)
        self.intValuesCount = len(self.lstValuesSorted)
        self.intListLines = min(self.intListRows, self.intValuesCount)
        self.dictNavigate = {'Up': -1, 'Down': 1, 'Prior': -self.intListLines, 'Next': self.intListLines}

        # Set window height here rather than in MakeDD in case new list has fewer items than original List Lines
        self.lb.config(height=self.intListLines)
        self.winDD.update_idletasks()
        self.winDD_height = self.winDD.winfo_reqheight()

        # Resize and position DD window
        self.update_position()

        self.winDD_Visible = False # used by sync_windows 
        self.blnNoKeyUp = False    # used by key_down to tell key_up to not do anuthing
        self.blnFirstShow = True   # handle (first key up event when tabbing) or (first mouse up when clicking) into txtCombo
        self.blnComboActive = True # allows for navigation between txtCombo and winDD

        # Setup root window sync bindings (destroyed in focus_out)
        self.lstBindings = [
            (self.root, '<Unmap>', self.root.bind('<Unmap>', self.sync_windows, add='+')),
            (self.root, '<Map>', self.root.bind('<Map>', self.sync_windows, add='+')),
            (self.root, '<Configure>', self.root.bind('<Configure>', self.update_position, add='+'))
        ]
#====================================================================================================
    def update_position(self, e=None):
        if e and e.widget != self.root: return

        x = self.txtCombo.winfo_rootx()
        y = self.txtCombo.winfo_rooty()
        z = self.txtCombo.winfo_width()
        
        yy = y + self.txtCombo.winfo_height()
        if (yy + self.winDD_height) > self.intScreenHeight:
            if y > (self.intScreenHeight - yy): yy = y - self.winDD_height
            
        self.winDD.wm_geometry(f'{z}x{self.winDD_height}+{x}+{yy}')
#====================================================================================================
    def sync_windows(self, e):
        if e.widget == self.root:
            if e.type == tk.EventType.Unmap: self.winDD.withdraw()
            elif e.type == tk.EventType.Map and self.winDD_Visible: self.winDD.deiconify()
#====================================================================================================
    def scrollbar_scroll(self, *args):
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
    def listbox_move_to(self, intIndex):
        self.lb.selection_clear(0, tk.END)
        self.lb.activate(intIndex)
        self.lb.selection_set(intIndex)
        self.lb.yview(max(0, intIndex - (self.intListLines // 2)))
#====================================================================================================
    def item_clicked(self, e=None):
        intIndex = self.lb.nearest(e.y) if e else self.lb.index('active')
        self.txtCombo.delete(0, tk.END)
        self.txtCombo.insert(0, self.lstValuesSorted[intIndex])
        self.winDD.withdraw(); self.winDD_Visible = False
#====================================================================================================
    def key_down(self, e):
        if self.winDD and self.winDD.winfo_exists():
            match e.keysym:
                case 'Return' if self.winDD.winfo_viewable():
                    self.item_clicked()
                    self.blnNoKeyUp = True
                    return 'break'

                case 'Tab' if self.winDD.winfo_viewable():
                    if self.txtCombo.get():
                        self.item_clicked()

                    oFocusNext = self.txtCombo.tk_focusNext()
                    if oFocusNext:
                        oFocusNext.focus_set()

                    self.blnNoKeyUp = True
                    return 'break'

                case 'Escape':
                    self.winDD.withdraw(); self.winDD_Visible = False
                    self.blnNoKeyUp = True
                    return 'break'

                case 'Up' | 'Down' | 'Prior' | 'Next':
                    if self.winDD.winfo_viewable():
                        new_idx = max(0, min(self.lb.index(tk.ACTIVE) + self.dictNavigate[e.keysym], self.intValuesCount - 1))
                        self.listbox_move_to(new_idx)
                    else:
                        self.key_up()
                        self.winDD.deiconify(); self.winDD_Visible = True

                    self.blnNoKeyUp = True
                    return 'break'
            
            if e.widget in (self.winDD, self.lb):
                match e.keysym:
                    case 'BackSpace':
                        intCursorPosition = self.txtCombo.index(tk.INSERT)
                        if intCursorPosition > 0:
                            self.txtCombo.delete(intCursorPosition - 1)
                        return 'break'

                    case 'Delete':
                        intCursorPosition = self.txtCombo.index(tk.INSERT)
                        self.txtCombo.delete(intCursorPosition)
                        return 'break'

                    case _ if e.char and e.char.isprintable():
                        self.txtCombo.insert(tk.INSERT, e.char)
                        return 'break'
#====================================================================================================
    def key_up(self, e=None):
        if self.winDD and self.winDD.winfo_exists():
            if self.blnNoKeyUp: self.blnNoKeyUp = False; return
            
            strPrefix = self.txtCombo.get()
            intNewIndex = 0 if not strPrefix else self.get_list_index(strPrefix)
            self.listbox_move_to(max(0, intNewIndex))
            
            if self.blnFirstShow:
                self.blnFirstShow = False
            elif e:
                if intNewIndex == -1:
                    self.winDD.withdraw(); self.winDD_Visible = False
                else:
                    if self.txtCombo.index(tk.INSERT) == self.txtCombo.index(tk.END):
                        if strPrefix.casefold() == self.lstValuesSorted[intNewIndex].casefold():
                            self.txtCombo.delete(0, tk.END)
                            self.txtCombo.insert(0, self.lstValuesSorted[intNewIndex])

                    self.winDD.deiconify(); self.winDD_Visible = True
#====================================================================================================
    def button_release(self, e):
        if self.winDD and self.winDD.winfo_exists():
            if self.blnFirstShow:
                self.blnFirstShow = False

            self.key_up()
            if self.txtCombo.index(tk.INSERT) == self.txtCombo.index(tk.END):
                self.winDD.deiconify(); self.winDD_Visible = True
            else:
                self.winDD.withdraw(); self.winDD_Visible = False
#====================================================================================================
    def focus_out(self, e):
        if self.root.focus_get() in (None, self.txtCombo):
            return

        if self.winDD: self.winDD.withdraw(); self.winDD_Visible = False
        
        if self.blnValidate:
            strPrefix = self.txtCombo.get()
            intIndex = self.get_list_index(strPrefix)
            if intIndex == -1 or strPrefix != self.lstValuesSorted[intIndex]:
                self.txtCombo.delete(0, tk.END)

        for oWidget, strEvent, strID in self.lstBindings:
            try: oWidget.unbind(strEvent, strID)
            except: pass
        self.lstBindings = []
        
        self.blnComboActive = False
        self.txtCombo.selection_clear()
#====================================================================================================
    def on_destroy(self, e):
        if e.widget == self.winDD:
            for oWidget, strEvent, strID in self.lstBindings:
                try: oWidget.unbind(strEvent, strID)
                except: pass
            self.lstBindings = []

            self.winDD = None
#====================================================================================================
    def get(self):
        return self.txtCombo.get()
#====================================================================================================
    def set(self, value):
        self.txtCombo.delete(0, tk.END)
        self.txtCombo.insert(0, value)
#====================================================================================================
    def delete(self, first, last=tk.END):
        self.txtCombo.delete(first, last)
#====================================================================================================
    def grid(self, **kwargs):
        self.txtCombo.grid(**kwargs)
#====================================================================================================
    def pack(self, **kwargs):
        self.txtCombo.pack(**kwargs)
#====================================================================================================
#====================================================================================================
# ***** class end *****
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




#-----
ttk.Label(root, text='freestyle, choose or type anything you want:', style='Base.TLabel', width=71).grid(row=0, column=0, columnspan=2, sticky='w', padx=(10, 0))

ttk.Label(root, text='Combo 1:', style='Base.TLabel', width=10).grid(row=1, column=0, sticky='w', padx=(10, 0))
myCuCo1 = CuCo(root, tplFont, 'Base.TEntry', 60, 22, 5, countries, False) # all arguments passed positionally
myCuCo1.grid(row=1, column=1, sticky='w', padx=(10, 0))
myCuCo1.set('yesterday was a rainy day')
#-----
root.rowconfigure(2, minsize=50)
#-----
frame1 = ttk.Frame(root, padding='0')
frame1.grid(row=3, column=0, columnspan=2, sticky='nsew')

ttk.Label(frame1, text='combo with default font/style and data validation, packed in a frame:', style='Base.TLabel', width=71).pack(side='left', padx=(10, 0))

frame2 = ttk.Frame(root, padding='0')
frame2.grid(row=4, column=0, columnspan=2, sticky='nsew')
ttk.Label(frame2, text='Combo 2:', style='Base.TLabel', width=10).pack(side='left', padx=(10, 0))
myCuCo2 = CuCo(frame2, None, None, 10, 14, 8, animals, True) # arguments passed positionally but using None for default values
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
