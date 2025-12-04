import cv2
import mediapipe
import time
import multiprocessing
from common import SkeletonDetectionResult
from datetime import datetime


def extract_skeleton(stop_event, camera_url: str, queue_out: multiprocessing.Queue):

    ##### 1. Mở camera xem có đọc được luồng không, nếu không thì return luôn
    cap = cv2.VideoCapture(camera_url)
    if not cap.isOpened():
        print("Cannot open camera stream")
        return
    
    # TODO: lưu giá trị cố định của camera
    FPS = cap.get(cv2.CAP_PROP_FPS)
    print("FPS: ", FPS)
    MAX_FRAME = FPS*10 # -> đảm bảo 10 giây 1 lần sẽ gửi kết quả để detect ngã



    ##### 2. Khai mô hình và những biến lưu kết quả
    mp_pose  = mediapipe.solutions.pose

    pose = mp_pose.Pose(
        model_complexity=1,        # 0 = fast, 1 = balanced, 2 = accurate (chậm hơn)
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    list_frames = []
    skeleton_frames = []
    frame_count = 0

    cam_frame = 0

    ##### 3. Chạy vòng lặp nhận các frame và xử lí
    while not stop_event.is_set():
        error_frame_count = 0
        while True:
            ret, frame = cap.read()
            cam_frame += 1
            
            ##### 4. Xử lí trường hợp không đọc được frame
            if not ret:
                error_frame_count += 1
                # TODO: if there are more than 10 continuous error frames, reset variables and break
                if error_frame_count > 10:
                    error_frame_count = 0
                    frame_count = 0
                    skeleton_frames.clear()
                    list_frames.clear()
                    print("Cannot read the camera stream")
                    time.sleep(10)
                    break
                continue # dòng này rất quan trọng
            
            # TODO: nếu frame không lỗi, reset giá trị error_frame_count
            error_frame_count = 0

            # TODO: Convert frame về dạng RGB chuẩn để xử lí
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = pose.process(rgb)


            ##### 5. Xử lí trường hợp không phát hiện landmarks trong frame
            if not result.pose_landmarks:
                error_frame_count += 1
                # TODO: if there are more than 10 continuous error frames, reset variables and break
                if error_frame_count > 10:
                    error_frame_count = 0
                    frame_count = 0
                    skeleton_frames.clear()
                    list_frames.clear()
                    time.sleep(1)
                    print("break because there is no person")
                    break
                continue # dòng này rất quan trọng
            
            # TODO: nếu frame không lỗi, reset giá trị error_frame_count
            error_frame_count = 0

            ##### 6. Lưu lại các landmarks trong frame
            joints = []
            for lm in result.pose_landmarks.landmark:
                joints.append([lm.x, lm.y, lm.z])  

            frame_count += 1
            skeleton_frames.append(joints)
            # print("cam_frame: ", cam_frame)

            ##### 7. Xử lí trường hợp số lượng frame cho một lần detect đã đủ
            if frame_count >= 300 or frame_count >= MAX_FRAME:
                # TODO: nếu event đã được set, thì dừng luôn, tránh lỗi
                if stop_event.is_set():
                    return

                # TODO: gửi list skeleton đi chỗ khác
                
                queue_out.put(SkeletonDetectionResult(camera_url=camera_url,
                                                      list_frame=list_frames,
                                                      list_skeleton=skeleton_frames,
                                                      created_at=datetime.now()))

                # TODO: set các giá trị về ban đầu
                frame_count = 0
                skeleton_frames.clear()
                list_frames.clear()
                
                print("Sent to queue")
                break



