import multiprocessing
from fall_detection_model import Model
from common import SkeletonDetectionResult, Video, Event
import numpy as np
import torch

def process_input(list_skeleton):
    if len(list_skeleton) < 300:
        k = len(list_skeleton)
        joints = []
        for i in range(0, 33):
            joints.append([0.0, 0.0, 0.0])
        while k < 300:
            list_skeleton.append(joints)
            k += 1
    # arr = np.stack([np.array(j).reshape(33, 3) for j in list_skeleton])
    arr = np.array(list_skeleton).astype(np.float32)
    input = torch.from_numpy(arr)
    input = input.permute(2, 0, 1)
    input = input.unsqueeze(0).unsqueeze(-1)

    return input



def detect_fall(queue_in: multiprocessing.Queue, queue_out_video: multiprocessing.Queue, queue_out_event: multiprocessing.Queue):
    model = Model()
    model.load_state_dict(torch.load("ctr-gcn-fall.pth", weights_only=True, map_location="cpu"))
    model.eval()
    with torch.inference_mode():
        while True:
            item_in: SkeletonDetectionResult = queue_in.get()
            # print("Fall Detecting ....")
            # TODO: detect
            input = process_input(item_in.list_skeleton)
            output = model(input)
            result = output.argmax(dim=1)
            print("result: ", result)

            # TODO: if no falling -> ignore
            if result == 0:
                continue
            
            # TODO: if falling -> put event to queue
            print("Fall Detection Part is putting event")
            queue_out_event.put(Event(camera_url=item_in.camera_url, created_at=item_in.created_at))
            queue_out_video.put(Video(camera_url=item_in.camera_url, list_frame=item_in.list_frame, created_at=item_in.created_at))