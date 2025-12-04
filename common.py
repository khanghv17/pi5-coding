class SkeletonDetectionResult:
    def __init__(self, camera_url, list_frame, list_skeleton, created_at):
        self.list_frame = list_frame,
        self.list_skeleton = list_skeleton
        self.camera_url = camera_url
        self.created_at = created_at

class Video:
    def __init__(self, camera_url, list_frame, created_at):
        self.list_frame = list_frame
        self.camera_url = camera_url
        self.created_at = created_at

class Event:
    def __init__(self, camera_url, created_at):
        self.camera_url = camera_url
        self.created_at = created_at
        

        