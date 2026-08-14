# Wavre

A gesture-controlled Spotify playback client. Control playback using hand gestures captured through your desktop webcam.

## Features

- Play/pause, skip, and like/unlike the current track
- Live webcam feed with hand skeleton overlay and gesture progress indicator
- Album art, track name, and artist displayed in real time

## Requirements

- Python 3.12+
- A connected webcam (Wavre will not work if one isn't connected)
- An active Spotify Premium account
- Spotify API credentials (see Setup)

## Dependencies

Install dependencies with:

```bash
pip install -r requirements.txt
```

| Package         | Purpose |
|-----------------|---|
| `opencv-python` | Webcam capture and frame rendering |
| `mediapipe`     | Hand landmark detection |
| `spotipy`       | Spotify Web API client |
| `Pillow`        | Image processing for album art |
| `requests`      | Fetching album art from URLs |
| `numpy`         | Numerical operations |

## Setup

1. Create a Spotify app at [developer.spotify.com](https://developer.spotify.com/dashboard)
2. Add the following files to `../secretfiles/GestureMediaControl/`:
   - `client_id.txt`
   - `client_secret.txt`
   - `redirect_uri.txt`
   - `scope.txt`

## Usage
```bash
python main.py
# For Mac users if needed:
python3 main.py
```

The Wavre window will open. Point your hand at the webcam and hold a gesture steady for a few seconds to trigger 
any below actions.

## Gestures Available

| Gesture | Action |
|---|---|
| All 5 fingers open | Play/Pause |
| Thumb only | Next track |
| One finger (non-thumb) | Previous track |
| OK sign | Like/Unlike |

Gestures must be held for around 8 frames to confirm, with a 2-second cooldown between actions.
