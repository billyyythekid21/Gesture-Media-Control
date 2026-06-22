import time
import tkinter as tk
from io import BytesIO

import cv2 as cv
import mediapipe as mp
import requests
import spotipy
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from PIL import Image, ImageTk
from spotipy.oauth2 import SpotifyOAuth

with open("../secretfiles/GestureMediaControl/client_id.txt") as file1:
            client_id = file1.read().strip()
with open("../secretfiles/GestureMediaControl/client_secret.txt") as file2:
            client_secret = file2.read().strip()
with open("../secretfiles/GestureMediaControl/redirect_uri.txt") as file3:
            redirect_uri = file3.read().strip()
with open("../secretfiles/GestureMediaControl/scope.txt") as file4:
            scope = file4.read().strip()

m = tk.Tk()
m.title('Spotify Gesture Control')

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

base_options = mp_python.BaseOptions(model_asset_path='hand_landmarker.task')
options = mp_vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=mp_vision.RunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7
)
hand_landmarker = mp_vision.HandLandmarker.create_from_options(options)

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20),
]

cap = cv.VideoCapture(0)

cooldowns = {
    "playpause": 0,
    "next": 0,
    "previous": 0,
    "like": 0
}
COOLDOWN_TIME = 2.0

gesture_hold = {
    "playpause": 0,
    "next": 0,
    "previous": 0,
    "like": 0
}
HOLD_FRAMES_REQUIRED = 8


def draw_landmarks(frame, landmarks):
    h, w, _ = frame.shape
    points = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
    for start, end in HAND_CONNECTIONS:
        cv.line(frame, points[start], points[end], (0, 255, 0), 2)
    for pt in points:
        cv.circle(frame, pt, 4, (255, 0, 0), -1)


def count_fingers(hand_landmarks):
    tip_ids = [8, 12, 16, 20]
    fingers = []

    if hand_landmarks[4].x < hand_landmarks[3].x:
        fingers.append(1)
    else:
        fingers.append(0)

    for tip in tip_ids:
        if hand_landmarks[tip].y < hand_landmarks[tip - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)

    return fingers.count(1), fingers


def is_ok_gesture(hand_landmarks, frame_width, frame_height):
    ix, iy = hand_landmarks[8].x * frame_width, hand_landmarks[8].y * frame_height
    tx, ty = hand_landmarks[4].x * frame_width, hand_landmarks[4].y * frame_height

    dist = ((ix - tx) ** 2 + (iy - ty) ** 2) ** 0.5

    middle_up = hand_landmarks[12].y < hand_landmarks[10].y
    ring_up = hand_landmarks[16].y < hand_landmarks[14].y
    pinky_up = hand_landmarks[20].y < hand_landmarks[18].y

    return dist < frame_width * 0.06 and middle_up and ring_up and pinky_up


camera_label = tk.Label(m)
camera_label.pack()


def process():
    ret, frame = cap.read()
    if not ret:
        m.after(10, process)
        return

    frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
    timestamp_ms = int(time.time() * 1000)
    results = hand_landmarker.detect_for_video(mp_image, timestamp_ms)
    current_time = time.time()

    if results.hand_landmarks:
        for hand_landmarks in results.hand_landmarks:
            draw_landmarks(frame, hand_landmarks)

            total_fingers, fingers = count_fingers(hand_landmarks)

            height, width, _ = frame.shape

            active_gesture = None

            if total_fingers == 5:
                active_gesture = "playpause"
            elif fingers[0] == 1 and total_fingers == 1:
                active_gesture = "next"
            elif fingers[0] == 0 and total_fingers == 1:
                active_gesture = "previous"
            elif is_ok_gesture(hand_landmarks, width, height):
                active_gesture = "like"

            for key in gesture_hold:
                if key == active_gesture:
                    gesture_hold[key] += 1
                else:
                    gesture_hold[key] = 0

            if active_gesture == "playpause":
                progress = min(gesture_hold["playpause"], HOLD_FRAMES_REQUIRED)
                cv.putText(
                    frame, f"Play/Pause ({progress}/{HOLD_FRAMES_REQUIRED})", (10, 60),
                    cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
                )
                if gesture_hold["playpause"] >= HOLD_FRAMES_REQUIRED and current_time - cooldowns["playpause"] > COOLDOWN_TIME:
                    try:
                        playback = sp.current_playback()
                        if playback:
                            if playback["is_playing"]:
                                sp.pause_playback()
                            else:
                                sp.start_playback()
                    except spotipy.exceptions.SpotifyException as e:
                        print(f"Spotify error (play/pause): {e}")
                        status_label.config(text="No active Spotify device")
                    cooldowns["playpause"] = current_time

            elif active_gesture == "next":
                progress = min(gesture_hold["next"], HOLD_FRAMES_REQUIRED)
                cv.putText(
                    frame, f"Next ({progress}/{HOLD_FRAMES_REQUIRED})", (10, 90),
                    cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2
                )
                if gesture_hold["next"] >= HOLD_FRAMES_REQUIRED and current_time - cooldowns["next"] > COOLDOWN_TIME:
                    try:
                        sp.next_track()
                    except spotipy.exceptions.SpotifyException as e:
                        print(f"Spotify error (next): {e}")
                        status_label.config(text="No active Spotify device")
                    cooldowns["next"] = current_time

            elif active_gesture == "previous":
                progress = min(gesture_hold["previous"], HOLD_FRAMES_REQUIRED)
                cv.putText(
                    frame, f"Previous ({progress}/{HOLD_FRAMES_REQUIRED})", (10, 120),
                    cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2
                )
                if gesture_hold["previous"] >= HOLD_FRAMES_REQUIRED and current_time - cooldowns["previous"] > COOLDOWN_TIME:
                    try:
                        sp.previous_track()
                    except spotipy.exceptions.SpotifyException as e:
                        print(f"Spotify error (previous): {e}")
                        status_label.config(text="No active Spotify device")
                    cooldowns["previous"] = current_time

            elif active_gesture == "like":
                progress = min(gesture_hold["like"], HOLD_FRAMES_REQUIRED)
                cv.putText(
                    frame, f"Like/Unlike ({progress}/{HOLD_FRAMES_REQUIRED})", (10, 150),
                    cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2
                )
                if gesture_hold["like"] >= HOLD_FRAMES_REQUIRED and current_time - cooldowns["like"] > COOLDOWN_TIME:
                    try:
                        playback = sp.current_playback()
                        if playback and playback["item"]:
                            track_id = playback["item"]["id"]
                            saved = sp.current_user_saved_tracks_contains([track_id])[0]
                            if saved:
                                sp.current_user_saved_tracks_delete([track_id])
                            else:
                                sp.current_user_saved_tracks_add([track_id])
                    except spotipy.exceptions.SpotifyException as e:
                        print(f"Spotify error (like): {e}")
                        status_label.config(text="No active Spotify device")
                    cooldowns["like"] = current_time
    else:
        for key in gesture_hold:
            gesture_hold[key] = 0

    img = Image.fromarray(cv.cvtColor(frame, cv.COLOR_BGR2RGB))
    imgtk = ImageTk.PhotoImage(image=img)

    camera_label.config(image=imgtk)
    camera_label.image = imgtk

    m.after(10, process)


def update_gui():
    try:
        playback = sp.current_playback()
    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify error (update_gui): {e}")
        status_label.config(text="No active Spotify device")
        m.after(5000, update_gui)
        return

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
