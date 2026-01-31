import time
from datetime import datetime
from pathlib import Path

import mss
import mss.tools
import pyautogui

# =========================
# CONFIG (EDIT THESE)
# =========================

# Screenshot region: top-left (-1449, 230), bottom-right (-272, 1079)
# Convert to MSS region dict: left/top/width/height
REGION = {
    "left": -1638,
    "top": 230,
    "width": (-184) - (-1638),  
    "height": 1079 - 230          
}

# click fixed screen coordinates (if UI doesn't move)
# TODO: Replace these with YOUR button coordinates
CLICK_X, CLICK_Y = -1673, 192

# Interval between cycles (seconds): screenshot + click, then wait
INTERVAL = 1.2

# Output folder (Desktop/screenbot/captures)
OUT_DIR = Path.home() / "Desktop" / "screenbot" / "captures"

# Stop conditions (set to None to disable)
MAX_SHOTS = 90      # e.g. 200 to stop after 200 screenshots
MAX_SECONDS = None    # e.g. 300 to stop after 5 minutes

# Hotkeys (optional): p = pause/resume, q = quit
ENABLE_HOTKEYS = False
#Or true 

# Safety: move mouse to a corner to stop immediately
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


def timestamp_name(counter: int) -> str:
    """
    Generates time-sortable filenames like:
    20260127_101530_123_000001.png
    """
    now = datetime.now()
    base = now.strftime("%Y%m%d_%H%M%S")
    ms = f"{now.microsecond // 1000:03d}"
    return f"{base}_{ms}_{counter:06d}.png"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Running... (pyautogui FAILSAFE enabled: move mouse to a corner to stop)")
    print(f"Saving screenshots to: {OUT_DIR}")
    print(f"REGION = {REGION}")
    print(f"CLICK  = ({CLICK_X}, {CLICK_Y})")
    print(f"INTERVAL = {INTERVAL}s")
    if ENABLE_HOTKEYS:
        print("Hotkeys: press 'p' to pause/resume, 'q' to quit")

    paused = False
    quit_flag = False

    # Optional hotkeys
    hotkeys_active = ENABLE_HOTKEYS
    if hotkeys_active:
        try:
            import keyboard  # pip install keyboard

            def toggle_pause():
                nonlocal paused
                paused = not paused
                print("\nPaused." if paused else "\nResumed.")

            def request_quit():
                nonlocal quit_flag
                quit_flag = True
                print("\nQuit requested.")

            keyboard.add_hotkey("p", toggle_pause)
            keyboard.add_hotkey("q", request_quit)
        except Exception as e:
            print(f"Hotkeys disabled (keyboard issue): {e}")
            hotkeys_active = False

    t0 = time.time()
    counter = 0

    with mss.mss() as sct:
        while True:
            if quit_flag:
                break

            # Stop after time?
            if MAX_SECONDS is not None and (time.time() - t0) >= MAX_SECONDS:
                print("\nStopping: reached MAX_SECONDS.")
                break

            # Stop after count?
            if MAX_SHOTS is not None and counter >= MAX_SHOTS:
                print("\nStopping: reached MAX_SHOTS.")
                break

            if paused:
                time.sleep(0.1)
                continue

            start = time.time()

            # 1) Screenshot region
            shot = sct.grab(REGION)
            out_path = OUT_DIR / timestamp_name(counter)
            mss.tools.to_png(shot.rgb, shot.size, output=str(out_path))

            # 2) Click the button (fixed coordinates)
            pyautogui.click(CLICK_X, CLICK_Y)

            counter += 1

            # 3) Wait so cycles are roughly INTERVAL seconds apart
            elapsed = time.time() - start
            time.sleep(max(0.0, INTERVAL - elapsed))

    print(f"\nDone. Captured {counter} screenshots.")
    print("If your clicks/screenshots failed on macOS, check Screen Recording + Accessibility permissions.")


if __name__ == "__main__":
    main()

