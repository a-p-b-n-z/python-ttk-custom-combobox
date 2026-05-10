# Python TTK Custom Combobox (CuCo)

A robust, lightweight, and heavily optimized custom Combobox implementation for Python Tkinter applications.

## Overview

**CuCo** is a drop-in replacement for `ttk.Combobox` that fixes layout limitations and styling rigidity while providing advanced features and cross-platform optimization.

### Why CuCo?

- ✅ **Dynamic Grid/Pack Integration** - Blends seamlessly into complex layouts
- ✅ **In-Place Data Mutation** - Swap datasets on the fly without breaking references
- ✅ **Race Condition Protection** - Event guards eliminate focus-timing crashes
- ✅ **Advanced Text Interception** - Type to filter while navigating with arrow keys
- ✅ **Universal Mouse Wheel Support** - Cross-platform scroll wheel (Windows, macOS, Linux)
- ✅ **Smart Resize Handling** - List repositions intelligently, even shows above when needed
- ✅ **Case-Smart Auto-Correct** - Automatically corrects case when matching entries

---

## Key Features

### Dynamic Grid Injection
Instantiates cleanly using unified geometry redirection (`.grid()` and `.pack()`), allowing seamless integration into complex layouts.

### In-Place Memory Mutation
Leverages Python slice mutation (`ListForCombo[:] = NewList`) to swap datasets dynamically without breaking underlying memory references.

### Event Guarding
Protects key operational methods (`key_down`, `key_up`, `button_release`) using native component assertions. Eliminates focus-timing race conditions and operating system window-lag crashes—no artificial `after()` delay loops needed.

### Advanced Text Interception & Filtering
Intercepts active keystrokes to allow typing search filters while navigating options natively via:
- Arrow keys (Up/Down)
- Page Up/Down
- Return (select)
- Tab (select and move to next field)
- Escape (close)

### Universal Mouse Wheel Scroll Engine
Integrates cross-platform scroll wheel capabilities seamlessly across:
- **Windows** - MouseWheel events
- **macOS** - MouseWheel events  
- **Linux** - Button-4/Button-5 events

### Seamless Resize Handling
- List stays in correct position during window resize/restore
- Automatically shows above if not enough space below
- Adapts to dynamic data changes

---

## Basic Operation

### Tab into Combo
Nothing happens initially—you're just tabbing through. Start typing or press PgUp/PgDwn/Arrow keys to open the options.

### Click into Combo
- **Click on existing text** - Opens for free, non-validated text entry
- **Click on blank space** - Opens the dropdown with options

### Editing & Selection
- Dropdown shows as long as matching text exists
- Closes when no matches found
- Auto-corrects case when matching entry is selected
- Selection via Click, Enter, or Tab

### Data Validation
When enabled (default), resets text to empty string if input doesn't match any option. Allows form-level validation handling.

---

## Installation & Usage

### Quick Start

```python
import tkinter as tk
from CuCo import CuCo

root = tk.Tk()
root.title("CuCo Example")

# Create a custom combobox
countries = ['Canada', 'USA', 'Mexico']
combo = CuCo(root, lstListValues=countries)
combo.pack(padx=10, pady=10)

root.mainloop()
```

### Running the Demo

Simply run the `CuCo.py` file directly:

```bash
python CuCo.py
```

This demonstrates three different CuCo instances with various configurations and features.

---

## API Reference

### Constructor Parameters

```python
CuCo(parent, tplFont=None, strStyle=None, intTextWidth=20, 
     intArrowSize=14, intListRows=5, lstListValues=None, blnValidate=True)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `parent` | tk.Widget | **Required** | Parent widget |
| `tplFont` | tuple | `('Verdana', 14, 'bold')` | Font tuple: (name, size, weight) |
| `strStyle` | str | `'TEntry'` | TTK style name |
| `intTextWidth` | int | `20` | Width of the entry field |
| `intArrowSize` | int | `14` | Scrollbar arrow size |
| `intListRows` | int | `5` | Maximum visible rows in dropdown |
| `lstListValues` | list | `[]` | Initial list of options |
| `blnValidate` | bool | `True` | Enable data validation |

### Methods

#### `get()` - Get Current Value
```python
value = combo.get()
```

#### `set(value)` - Set Current Value
```python
combo.set('Canada')
```

#### `delete(first, last=tk.END)` - Delete Text
```python
combo.delete(0, tk.END)  # Clear all
```

#### `grid(**kwargs)` - Grid Layout
```python
combo.grid(row=0, column=0, padx=10, pady=10)
```

#### `pack(**kwargs)` - Pack Layout
```python
combo.pack(padx=10, pady=10)
```

---

## Usage Examples

### Example 1: Positional Arguments
```python
combo1 = CuCo(root, 
              ('Cascadia Mono', 22, 'bold'), 
              'Base.TEntry', 
              60, 22, 5, countries, False)
combo1.grid(row=1, column=0)
```

### Example 2: Using None for Defaults
```python
combo2 = CuCo(frame, None, None, 10, 14, 8, animals, True)
combo2.pack(side='left', padx=10)
```

### Example 3: Named Arguments
```python
combo3 = CuCo(root, 
              tplFont=('Verdana', 16, 'bold'),
              strStyle='Custom.TEntry',
              intTextWidth=30,
              lstListValues=my_list,
              blnValidate=True)
combo3.grid(row=2, column=0)
```

### Example 4: Dynamic List Changes
```python
# Update the list on-the-fly using slice mutation
combo.lstListValues[:] = ['New', 'List', 'Items']
# The dropdown automatically adapts
```

---

## System Requirements

- **Python 3.10+** (uses match/case statements)
- **Tkinter** (included with most Python distributions)
- **OS Support**: Windows, macOS, Linux

### Tested On
- Ryzen 5 3600
- Windows 11
- Python 3.14.3
- IDLE

---

## License

MIT License - Feel free to use, modify, improve, and repost as you see fit.

---

## Known Limitations & Future Improvements

- Multi-monitor support for intelligently placing dropdown above/below
- Modal behavior with Alt-Tab key (ESC key suggested as workaround)

---

## Notes

This code comes without warranties of any kind on an "as is where is" basis. Use at your own discretion.

The implementation prioritizes performance and reliability over feature bloat, making it suitable for production applications.
