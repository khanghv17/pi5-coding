import multiprocessing
# from fall_detection_model import Model
from common import SkeletonDetectionResult, Video, Event
import numpy as np
import torch
import onnxruntime as ort


def process_input(list_skeleton):
    if len(list_skeleton) < 60:
        k = len(list_skeleton)
        joints = []
        for i in range(0, 33):
            joints.append([0.0, 0.0, 0.0])
        while k < 60:
            list_skeleton.append(joints)
            k += 1
    # arr = np.array(list_skeleton).astype(np.float32)
    # input = torch.from_numpy(arr)
    # input = input.permute(2, 0, 1)
    # input = input.unsqueeze(0)
    arr = np.array(list_skeleton).astype(np.float32)  # (60, 33, 3)
    input_data = arr.transpose(2, 0, 1)  # (3, 60, 33)
    input_data = np.expand_dims(input_data, axis=0)  # (1, 3, 60, 33)

    return input_data



def detect_fall(queue_in: multiprocessing.Queue, queue_out_video: multiprocessing.Queue, queue_out_event: multiprocessing.Queue):
    # model = Model()
    # model.load_state_dict(torch.load("ctr-gcn-01-130.pth", weights_only=True, map_location="cpu"))
    # model.eval()
    session = ort.InferenceSession("ctrgcn.onnx")
    with torch.inference_mode():
        while True:
            item_in: SkeletonDetectionResult = queue_in.get()
            # TODO: detect
            input_data = process_input(item_in.list_skeleton)
            # output = model(input)
            # result = output.argmax(dim=1)
            outputs = session.run(None, {'input': input_data})
            predictions = outputs[0]
            # TODO: if no falling -> ignore
            print("Predictions: ", predictions)
            result = np.argmax(predictions, axis=1)
            if result == 0:
                print("Not a fall event")
                continue
            
            # TODO: if falling -> put event to queue
            print("Fall Detection Part is putting event")
            queue_out_event.put(Event(mac_address= "", camera_url=item_in.camera_url, created_at=item_in.created_at))
            queue_out_video.put(Video(camera_url=item_in.camera_url, list_frame=item_in.list_frame, created_at=item_in.created_at))