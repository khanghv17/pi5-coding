import multiprocessing
from common import Video
import cv2
import requests
import os
import paho.mqtt.client as mqtt
from common import Event
import orjson
import numpy as np

def send_video(mac_address: str, url: str, queue_in: multiprocessing.Queue):

    i = 1
    while True:
        # TODO: write_video 
        item : Video = queue_in.get()
        tmp = item.list_frame[0]
        frame_height, frame_width = tmp.shape[0], tmp.shape[1]
        os.makedirs("video", exist_ok=True)
        video_path = f"video/video_{i}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
        # fourcc = cv2.VideoWriter_fourcc(*'XVID') 

        output = cv2.VideoWriter(filename=video_path, fourcc=fourcc, fps=12, frameSize=(frame_width, frame_height))
        for frame in item.list_frame:
            output.write(frame)
        output.release()

        # TODO: send video
        with open(video_path, "rb") as f: # tự động đóng file với with
            files = {
                "file": (f"video_{i}.mp4", f, "video/mp4")
                }
            data = {
                "mac_address": mac_address,
                "camera_url": item.camera_url,
                "created_at": item.created_at.isoformat()
            }
            response = requests.post(url, files=files, data=data)
            if not (response.status_code == 200 or response.status_code == 201):
                print("Cannot send video")

        # TODO: delete video after sending successfully
        os.remove(video_path)
        if i >= 10:
            i = 1
        else:
            i += 1
