import cv2 as cv
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import pyautogui

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.6
)
mp_draw = mp.solutions.drawing_utils

cap = cv.VideoCapture(0)

def count_fingers(hand_landmarks):
    tip_ids = [8, 12, 16, 20]
    fingers = []

    landmarks = hand_landmarks.landmark

    if landmarks[4].x < landmarks[3].x:
        fingers.append(1)
    else:
        fingers.append(0)

    for tip in tip_ids:
        if landmarks[tip].y < landmarks[tip - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)

    return fingers.count(1), fingers


while True:
    ret, frame = cap.read()
    
    if not ret:
        break

    frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            total_fingers, fingers = count_fingers(hand_landmarks)

            if total_fingers == 5:
                cv.putText(frame, "Play/Pause", (10,60),
                            cv.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
                pyautogui.press("space")

            if fingers[0] == 1 and total_fingers == 1:
                cv.putText(frame, "Next", (10,90),
                            cv.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2)
                pyautogui.hotkey("shift", "n")

            if fingers[0] == 0 and total_fingers == 1:
                cv.putText(frame, "Previous", (10,120),
                            cv.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2)
                pyautogui.hotkey("shift", "p")

    cv.imshow('Hand Tracking', frame)

    if cv.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv.destroyAllWindows()