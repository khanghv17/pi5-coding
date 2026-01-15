from datetime import datetime


class SkeletonDetectionResult:
    def __init__(self, camera_url: str, list_frame: list, list_skeleton: list, created_at: datetime):
        self.list_frame = list_frame
        self.list_skeleton = list_skeleton
        self.camera_url = camera_url
        self.created_at = created_at

class Video:
    def __init__(self, camera_url: str, list_frame: list, created_at: datetime):
        self.list_frame = list_frame
        self.camera_url = camera_url
        self.created_at = created_at

class Event:
    def __init__(self, mac_address: str, camera_url: str, created_at: datetime):
        self.mac_address = mac_address
        self.camera_url = camera_url
        self.created_at = created_at
    
        