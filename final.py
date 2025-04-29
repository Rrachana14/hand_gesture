import cv2
import mediapipe as mp
import pyautogui
import time
import tkinter as tk
import threading

# INITIALIZE
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

start_x = 0
swipe_in_progress = False
swipe_distance = 150  
cumulative_movement = 0

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()


def run_tkinter():
    global progress_value,root, canvas,progress_bar

    root = tk.Tk()
    root.attributes('-fullscreen',True) 
    root.attributes('-topmost',True)  
    root.attributes('-transparentcolor', 'black')
    root.configure(bg='black')

    canvas = tk.Canvas(root, width=root.winfo_screenwidth(), height=root.winfo_screenheight(), bg='black', highlightthickness=0)
    canvas.pack()

    bar_y = root.winfo_screenheight() - 200 
    bar_height = 50
    bar_width = 800
    bar_x = (root.winfo_screenwidth() - bar_width) // 2

    center_x = bar_x + bar_width // 2


    # Base line
    canvas.create_line(bar_x, bar_y, bar_x + bar_width, bar_y, fill='gray', width=5)

    swipe_limit = 120
    canvas.create_oval(center_x - swipe_limit - 5, bar_y - 5, center_x - swipe_limit + 5, bar_y + 5, fill='red')
    canvas.create_oval(center_x + swipe_limit - 5, bar_y - 5, center_x + swipe_limit + 5, bar_y + 5, fill='red')

    progress_bar = canvas.create_line(center_x, bar_y - 10, center_x, bar_y + 10, fill='green', width=5)

    def update_bar():
        new_x = center_x + progress_value
        canvas.coords(progress_bar, new_x, bar_y - 10, new_x, bar_y + 10)
        root.after(10, update_bar)
    update_bar()
    root.mainloop()


progress_value = 0
tkinter_thread = threading.Thread(target=run_tkinter, daemon=True)
tkinter_thread.start()



while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    h, w, c = img.shape

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)

            lm_list = []
            for id, lm in enumerate(handLms.landmark):
                lm_list.append((int(lm.x * w), int(lm.y * h)))

            for idx, point in enumerate(lm_list):
                cv2.putText(img, str(idx), point, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

            if lm_list:
                index_tip = lm_list[8]
                index_bottom = lm_list[5]

                fingers = []
                for id in [8, 12, 16, 20]:  
                    if lm_list[id][1] < lm_list[id-2][1]:  
                        fingers.append(1)
                    else:
                        fingers.append(0)

                
                if fingers[0] == 1 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0:
                    print("Jump detected")
                    cv2.putText(img, "Jump Detected!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 5)
                    pyautogui.press('up')

                elif fingers[0] == 0 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0:
                    print("Duck detected")
                    cv2.putText(img, "Duck Detected!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 5)
                    pyautogui.press('down')

                
                cx = lm_list[9][0]  

                if not swipe_in_progress:
                    start_x = cx
                    swipe_in_progress = True
                    cumulative_movement = 0
                else:
                    diff_x = cx - start_x
                    cumulative_movement = diff_x

                    if abs(diff_x) > swipe_distance:
                        if diff_x > 0:
                            print("Swipe Right Detected")
                            cv2.putText(img, "Right Swipe Detected!", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 5)
                            pyautogui.press('right')
                        else:
                            print("Swipe Left Detected")
                            cv2.putText(img, "Left Swipe Detected!", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 5)
                            pyautogui.press('left')
                        swipe_in_progress = False 

            else:
                swipe_in_progress = False

    else:
        swipe_in_progress = False

    if swipe_in_progress:
        progress = cumulative_movement
        progress = max(-400, min(400, progress))  
        progress_value = progress
    else:
        progress_value = 0  
    

    cv2.imshow('Hand Tracking', img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
