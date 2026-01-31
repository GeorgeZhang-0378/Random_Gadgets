import time
import pyautogui

print("Move mouse; Ctrl+C to stop.")
while True:
    x, y = pyautogui.position()
    print(x, y)
    time.sleep(0.2)

