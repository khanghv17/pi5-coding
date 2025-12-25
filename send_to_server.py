import multiprocessing
from common import Video
import cv2
import requests
import os
import paho.mqtt.client as mqtt
from common import Event

def send_video(mac_address: str, url: str, queue_in: multiprocessing.Queue):

    i = 1
    while True:
        # TODO: write_video 
        item : Video = queue_in.get()
        frame_height, frame_width = item.list_frame[0].shape[0], item.list_frame[0].shape[1]
        video_path = f"video/video_{i}.mp4"
        output = cv2.VideoWriter(video_path, "H264", fps=15, frameSize=(frame_height, frame_width))
        for frame in item.list_frame:
            output.write(frame)

        # TODO: send video
        data = {
            "mac_address": "",
            "time" : item.created_at,
            "file": open(video_path, "rb")
        }
        with open(video_path, "rb") as f: # tự động đóng file với with
            files = {
                "file": (video_path, f, "video/mp4")
                }
            response = requests.post(url, files=files)
            if not (response.status_code == 200 or response.status_code == 201):
                print("Cannot send video")

        # TODO: delete video after sending successfully
        os.remove(video_path)
        if i >= 10:
            i = 1
        else:
            i += 1
