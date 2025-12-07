import cv2 as cv
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
from io import BytesIO
import time

with open("../secretfiles/GestureMediaControl/client_id.txt") as file1:
            client_id = file1.read().strip()
with open("../secretfiles/GestureMediaControl/client_secret.txt") as file2:
            client_secret = file2.read().strip()
with open("../secretfiles/GestureMediaControl/redirect_uri.txt") as file3:
            redirect_uri = file3.read().strip()
with open("../secretfiles/GestureMediaControl/scope.txt") as file4:
            scope = file4.read().strip()

m = tk.Tk()
m.title('Spotify Gesture Media Control')

album_art_img = tk.Label(m)
album_art_img.pack()

track_label = tk.Label(m, text="Song: ", font=("Arial", 14))
track_label.pack()

artist_label = tk.Label(m, text="Artist: ", font=("Arial", 12))
artist_label.pack()

status_label = tk.Label(m, text="Status: ", font=("Arial", 12))
status_label.pack()

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope
    )
)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.6
)
mp_draw = mp.solutions.drawing_utils

cap = cv.VideoCapture(0)

cooldowns = {
    "playpause": 0,
    "next": 0,
    "previous": 0,
    "like": 0
}
COOLDOWN_TIME = 1.0


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

    dist = ((ix - tx) ** 2  + (iy - ty) ** 2) ** 0.5

    middle_up = lm[12].y < lm[10].y
    ring_up = lm[16].y < lm[14].y
    pinky_up = lm[20].y < lm[18].y

    if dist < frame_width * 0.06 and middle_up and ring_up and pinky_up:
        return True
    return False

camera_label = tk.Label(m)
camera_label.pack()

def process():
    ret, frame = cap.read()
    if not ret:
        m.after(10, process)
        return

    frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)
    current_time = time.time()
    
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
                if current_time - cooldowns["playpause"] > COOLDOWN_TIME:
                    if sp.current_playback()["is_playing"]:
                        sp.pause_playback()
                    else:
                        sp.start_playback()
                    cooldowns["playpause"] = current_time

            if fingers[0] == 1 and total_fingers == 1:
                cv.putText(
                    frame, "Next", (10,90), 
                    cv.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2
                )
                if current_time - cooldowns["next"] > COOLDOWN_TIME:
                    sp.next_track()
                    cooldowns["next"] = current_time

            if fingers[0] == 0 and total_fingers == 1:
                cv.putText(
                    frame, "Previous", (10,120),
                    cv.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2
                )
                if current_time - cooldowns["previous"] > COOLDOWN_TIME:
                    sp.previous_track()
                    cooldowns["previous"] = current_time

            if is_ok_gesture(hand_landmarks, width, height):
                cv.putText(
                    frame, "Like/Unlike Song", (10,150),
                    cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2
                )
                if current_time - cooldowns["like"] > COOLDOWN_TIME:
                    playback = sp.current_playback()
                    if playback and playback["item"]:
                        track_id = playback["item"]["id"]
                        saved = sp.current_user_saved_tracks_contains([track_id])[0]
                        if saved:
                            sp.current_user_saved_tracks_delete([track_id])
                        else:
                            sp.current_user_saved_tracks_add([track_id])
                    cooldowns["like"] = current_time
    
    img = Image.fromarray(frame_rgb)
    imgtk = ImageTk.PhotoImage(image=img)

    camera_label.config(image=imgtk)
    camera_label.image = imgtk

    m.after(10, process)

def update_gui():
    playback = sp.current_playback()

    if playback and playback["item"]:
        track = playback["item"]["name"]
        artist = playback["item"]["artists"][0]["name"]
        img_url = playback["item"]["album"]["images"][1]["url"]

        track_label.config(text=f"Track: {track}")
        artist_label.config(text=f"Artist: {artist}")
        status_label.config(text="Playing" if playback["is_playing"] else "Paused")

        response = requests.get(img_url)
        img_data = Image.open(BytesIO(response.content))
        img_data = img_data.resize((200, 200))
        cover = ImageTk.PhotoImage(img_data)

        album_art_img.config(image=cover)
        album_art_img.image = cover

    m.after(5000, update_gui)

process()
update_gui()
m.mainloop()

cap.release()