import cv2 as cv
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import tkinter as tk
from tkinter import ttk

m = tk.Tk()

scope = "user-library-read"
#https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(scope=scope)
)

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

def is_ok_gesture(hand_landmarks, frame_width, frame_height):
    lm = hand_landmarks.landmark
    ix, iy = lm[8].x * frame_width, lm[8].y * frame_height
    tx, ty = lm[4].x * frame_width, lm[4].y * frame_height

    dist = ((ix - tx) **2  + (iy - ty) ** 2) ** 0.5

    middle_up = lm[12].y < lm[10].y
    ring_up = lm[16].y < lm[14].y
    pinky_up = lm[20].y < lm[18].y

    if dist < frame_width * 0.06 and middle_up and ring_up and pinky_up:
        return True
    return False

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

            height, width, _ = frame.shape

            if total_fingers == 5:
                cv.putText(
                    frame, "Play/Pause", (10,60),
                    cv.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2
                )
                if sp.current_playback()["is_playing"]:
                    sp.pause_playback()
                else:
                    sp.start_playback()

            if fingers[0] == 1 and total_fingers == 1:
                cv.putText(
                    frame, "Next", (10,90), 
                    cv.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2
                )
                sp.next_track()

            if fingers[0] == 0 and total_fingers == 1:
                cv.putText(
                    frame, "Previous", (10,120),
                    cv.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2
                )
                sp.previous_track()

            if is_ok_gesture(hand_landmarks, width, height):
                cv.putText(
                    frame, "Like/Unlike Song", (10,150),
                    cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2
                )
                playback = sp.current_playback()

                if playback and playback["item"]:
                    track_id = playback["item"]["id"]
                    saved = sp.current_user_saved_tracks_contains([track_id])[0]

                    if saved:
                        sp.current_user_saved_tracks_delete([track_id])
                    else:
                        sp.current_user_saved_tracks_add([track_id])


    cv.imshow('Hand Tracking', frame)

    if cv.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv.destroyAllWindows()