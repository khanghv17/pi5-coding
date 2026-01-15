### LIBRARY
import multiprocessing as mp
import paho.mqtt.client as mqtt
from getmac import get_mac_address
import cv2
import json
from enum import Enum
import orjson

## FILE
from detect_fall import detect_fall
from extract_skeleton import extract_skeleton
from send_to_server import send_video
from common import Event

############################# DEFINE ALL CONFIG
POST_VIDEO_URL = "http://192.168.1.191:9001/api/v1/event/upload-video"

# mqtt
MQTT_BROKER = "broker.emqx.io"     # đổi nếu dùng broker khác
MQTT_PORT = 1883
MQTT_QOS = 2

# MAC_ADDRESS = get_mac_address(interface="eth0")
MAC_ADDRESS = get_mac_address()

print("MAC_ADDRESS: ", MAC_ADDRESS)

CAMERA_LIST = {}
CAMERA_FALL_DETECTION_ACTIVE_LIST = []


class Action(Enum):
    START = "START"
    ADD_CAMERA = "ADD_CAMERA"
    DELETE_CAMERA = "DELETE_CAMERA"
    RUN_FALL_DETECTION = "RUN_FALL_DETECTION"
    STOP_FALL_DETECTION = "STOP_FALL_DETECTION"
    RESET = "RESET"
    SYNC = "SYNC"

class ServerRequest: # REQUEST FROM SERVER
    def __init__(self, action, url):
        self.action = action
        self.url = url

class ServerResponse: # RESPONSE TO SERVER
    def __init__(self, action: str, success: bool, url: str, message: str):
        self.mac_address = MAC_ADDRESS
        self.action = action
        self.success = success
        self.url = url
        self.message = message

TOPIC_SUBSCRIBE = MAC_ADDRESS
TOPIC_SEND_SERVER = "notify_server"
TOPIC_SEND_FALL_EVENT = "notify_fall_event"
############################# DEFINE ALL CONFIG - END














############################# HANDLE SIGNAL





def handle_start(payload):
    response = ServerResponse(Action.START.value, True, "", "Device is running")
    client.publish(topic=TOPIC_SEND_SERVER, payload=json.dumps(response.__dict__), qos=MQTT_QOS)


def handle_add_camera(payload):
    payload = json.loads(payload)
    camera_url = payload.get("url")
    # TODO: check xem có trong list chưa
    if camera_url in CAMERA_LIST:
        response = ServerResponse(Action.ADD_CAMERA.value, False, camera_url, "this camera exists already")
        client.publish(topic=TOPIC_SEND_SERVER, payload=json.dumps(response.__dict__), qos=MQTT_QOS)
        return

    # TODO: check xem có mở được luồng camera hay không
    cap = cv2.VideoCapture(camera_url)
    if not cap.isOpened():
        response = ServerResponse(Action.ADD_CAMERA.value, False, camera_url, "cannot open this stream")
        client.publish(topic=TOPIC_SEND_SERVER, payload=json.dumps(response.__dict__), qos=MQTT_QOS)
        cap.release()
        return
    cap.release()
    
    # TODO: add camera vào list
    CAMERA_LIST[camera_url] = mp.Event()


    # TODO: notify adding success
    response = ServerResponse(Action.ADD_CAMERA.value, True, camera_url, "add camera successfully")
    client.publish(topic=TOPIC_SEND_SERVER, payload=json.dumps(response.__dict__), qos=MQTT_QOS)
    return 

def handle_delete_camera(payload):
    payload = json.loads(payload)
    camera_url = payload.get("url")
    # TODO: check xem có trong list chưa
    if camera_url not in CAMERA_LIST:
        response = ServerResponse(Action.DELETE_CAMERA.value, False, camera_url, "this camera does not exist")
        client.publish(topic=TOPIC_SEND_SERVER, payload=json.dumps(response.__dict__), qos=MQTT_QOS)
        return
    
    # TODO: if it is running fall detection, stop running
    if camera_url in CAMERA_FALL_DETECTION_ACTIVE_LIST:
        CAMERA_LIST[camera_url].set()
        CAMERA_FALL_DETECTION_ACTIVE_LIST.remove(camera_url)
    
    # TODO: delete camera from list
    CAMERA_LIST.pop(camera_url)

    # TODO: notify deleting success
    response = ServerResponse(Action.DELETE_CAMERA.value, True, camera_url, "delete camera successfully")
    client.publish(topic=TOPIC_SEND_SERVER, payload=json.dumps(response.__dict__), qos=MQTT_QOS)
    return 

def handle_run_fall_detection(payload):
    payload = json.loads(payload)
    camera_url = payload.get("url")
    # TODO: check xem có trong list không
    if camera_url not in CAMERA_LIST:
        response = ServerResponse(Action.RUN_FALL_DETECTION.value, False, camera_url, "this camera does not exist")
        client.publish(topic=TOPIC_SEND_SERVER, payload=json.dumps(response.__dict__), qos=MQTT_QOS)
        return
    
    # TODO: check xem trong list active đã có camera này chưa
    if camera_url in CAMERA_FALL_DETECTION_ACTIVE_LIST:
        response = ServerResponse(Action.RUN_FALL_DETECTION.value, True, camera_url, "this camera has been running fall detection already")
        client.publish(topic=TOPIC_SEND_SERVER, payload=json.dumps(response.__dict__), qos=MQTT_QOS)
        return
    
    # TODO: check xem có mở được luồng camera hay không
    cap = cv2.VideoCapture(camera_url)
    if not cap.isOpened():
        response = ServerResponse(Action.RUN_FALL_DETECTION.value, False, camera_url, "cannot open this camera stream")
        client.publish(topic=TOPIC_SEND_SERVER, payload=json.dumps(response.__dict__), qos=MQTT_QOS)
        cap.release()
        return
    cap.release()
    
    # TODO: reset event cho camera
    CAMERA_LIST[camera_url].clear()

    # TODO: new process detect skeleton
    p_extract_skeleton = mp.Process(target=extract_skeleton, args=(CAMERA_LIST[camera_url], camera_url, skeleton_detection_result_queue))
    p_extract_skeleton.start()

    # TODO: add camera vào list active
    CAMERA_FALL_DETECTION_ACTIVE_LIST.append(camera_url)

    # TODO: notify running fall detection success
    response = ServerResponse(Action.RUN_FALL_DETECTION.value, True, camera_url, "run fall detection for camera successfully")
    client.publish(topic=TOPIC_SEND_SERVER, payload=json.dumps(response.__dict__), qos=MQTT_QOS)
    return 

def handle_stop_fall_detection(payload):
    payload = json.loads(payload)
    camera_url = payload.get("url")
    # TODO: check xem có trong list không
    if camera_url not in CAMERA_LIST:
        response = ServerResponse(Action.STOP_FALL_DETECTION.value, False, camera_url, "this camera does not exist")
        client.publish(topic=TOPIC_SEND_SERVER, payload=json.dumps(response.__dict__), qos=MQTT_QOS)
        return
    
    # TODO: check xem camera có đang được chạy fall detection hay không
    if camera_url not in CAMERA_FALL_DETECTION_ACTIVE_LIST:
        response = ServerResponse(Action.STOP_FALL_DETECTION.value, False, camera_url, "this camera is not running fall detection")
        client.publish(topic=TOPIC_SEND_SERVER, payload=json.dumps(response.__dict__), qos=MQTT_QOS)
        return

    # TODO: gửi tín hiệu dừng fall detection cho camera
    CAMERA_FALL_DETECTION_ACTIVE_LIST.remove(camera_url)
    CAMERA_LIST[camera_url].set()

    # TODO: notify stopping fall detection for camera successfully
    response = ServerResponse(Action.STOP_FALL_DETECTION.value, True, camera_url, "stop fall detection for camera successfully")
    client.publish(topic=TOPIC_SEND_SERVER, payload=json.dumps(response.__dict__), qos=MQTT_QOS)
    return 

def handle_reset(payload):
    # TODO: stop all running-fall-detection camera
    for active_camera in CAMERA_FALL_DETECTION_ACTIVE_LIST:
        CAMERA_FALL_DETECTION_ACTIVE_LIST.remove(active_camera)
        CAMERA_LIST[active_camera].set()
    
    # TODO: clear camera list
    CAMERA_LIST.clear()

    # TODO: notify server
    response = ServerResponse(Action.RESET.value, True, "", "reset camera sucessfully")
    client.publish(topic=TOPIC_SEND_SERVER, payload=json.dumps(response.__dict__), qos=MQTT_QOS)
    return 


action_handlers = {
    Action.START.value: handle_start,
    Action.ADD_CAMERA.value: handle_add_camera,
    Action.DELETE_CAMERA.value: handle_delete_camera,
    Action.RUN_FALL_DETECTION.value: handle_run_fall_detection,
    Action.STOP_FALL_DETECTION.value: handle_stop_fall_detection,
    Action.RESET.value: handle_reset
    }


# Callback - successful connection
def on_connect(client, userdata, flags, rc, properties):
    print("MQTT Connected with result code: ", rc)
    subscribe_topic = f"{MAC_ADDRESS}"
    client.subscribe(subscribe_topic)

# Callback - receiving message
def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    newpayload = json.loads(payload)

    handler = action_handlers.get(newpayload["action"])
    print("handler: ", handler)
    if handler:
        handler(payload)

def notify_event(queue_in: mp.Queue):
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(MQTT_BROKER, MQTT_PORT)

    while True:
        item: Event = queue_in.get()
        item.mac_address = MAC_ADDRESS
        client.publish(topic=TOPIC_SEND_FALL_EVENT, payload=orjson.dumps(item.__dict__), qos=MQTT_QOS)


############################# HANDLE SIGNAL - END


















############################# MAIN PART

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
# Gán các callback
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT)

# TODO: Declare Queues

skeleton_detection_result_queue = mp.Queue()
video_queue = mp.Queue()
event_queue = mp.Queue()

if __name__ == '__main__':

    # p_extract_skeleton =mp.Process(target=extract_skeleton, args=)
    p_detect_fall = mp.Process(target=detect_fall, args=(skeleton_detection_result_queue, video_queue, event_queue))
    p_send_video = mp.Process(target=send_video, args=(MAC_ADDRESS, POST_VIDEO_URL, video_queue))
    p_notify_event = mp.Process(target=notify_event, args=(event_queue, ))

    p_detect_fall.start()
    p_send_video.start()
    p_notify_event.start()

    # p_detect_fall.join()
    # p_send_video.join()
    # p_notify_event.join()

    # Run loop on mqtt client
    client.loop_forever()

############################# MAIN PART - END
