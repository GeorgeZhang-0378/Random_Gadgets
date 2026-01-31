import time
import pyautogui

print("Switch to TextEdit NOW.")
print("Click will happen in 3 seconds...")
time.sleep(3)

x, y = pyautogui.position()
print(f"Clicking at x={x}, y={y}")

pyautogui.mouseDown(x, y)
time.sleep(0.05)
pyautogui.mouseUp(x, y)

print("Done.")

