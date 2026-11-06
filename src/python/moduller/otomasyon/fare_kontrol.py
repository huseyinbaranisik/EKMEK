import sys
import pyautogui
import json

def click_mouse(x, y):
    try:
        pyautogui.moveTo(x, y, duration=0.5)
        pyautogui.click()
        print(json.dumps({"basari": True}))
    except Exception as e:
        print(json.dumps({"basari": False, "hata": str(e)}))

if __name__ == "__main__":
    if len(sys.argv) > 2:
        try:
            x = int(sys.argv[1])
            y = int(sys.argv[2])
            click_mouse(x, y)
        except ValueError:
            print(json.dumps({"basari": False, "hata": "Koordinatlar sayı olmalıdır"}))
    else:
        print(json.dumps({"basari": False, "hata": "Eksik parametre"}))
