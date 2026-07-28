# Tab Copier

A small office-work helper for copying data from one form into another.

Instead of manually alt-tabbing back and forth to copy each field one at a
time, load all the values from "Form A" into a CSV file once. Then, while
filling out "Form B", just press **Tab** as you normally would to move
between fields — this tool detects the Tab press globally (even though it's
not the focused window) and automatically copies the next value onto your
clipboard, so **Ctrl+V** always pastes the right thing.

Tab still does its normal job of moving focus everywhere else — this tool
only listens for the key press, it never blocks or changes it.

## Requirements

- Windows
- Python 3.9+

## Setup

1. Clone or download this repository.
2. Open a terminal in the project folder.
3. Install the dependencies:

   ```
   pip install keyboard pyperclip
   ```

## Usage

1. Build a CSV file with the values from Form A, one per row, in the same
   order you'll tab through the fields on Form B. Each row can be either:
   - `Field Name,Value` (recommended — labels show up in the app), or
   - just `Value` (the app will label rows "Row 1", "Row 2", ...)

   See `sample_data.csv` for an example.

2. Run the app:

   ```
   python tab_copier.py
   ```

   or double-click `run.bat`.

3. Click **Load CSV...** and select your file.
4. Click into the first field on Form B and paste (`Ctrl+V`) — that's value #1.
5. Press **Tab** to move to the next field like normal. The next value is
   copied to your clipboard automatically. Paste, tab, paste, repeat until
   you reach the end of the list.

### Other controls

- **Reset to start** — go back to the first value.
- **Listening for Tab** — checkbox to pause/resume the global hook without
  closing the app.
- **Back / Skip / Copy current now** — manual controls if you need to
  redo a field, skip one without copying, or re-copy the current value.

## Note on permissions

The global Tab detection uses a low-level Windows keyboard hook. If the
other application (Form B) is running as **administrator** and this tool
is not, Windows won't let the hook see the key press. If Tab presses
aren't triggering a copy, right-click `run.bat` and choose **Run as
administrator**.
