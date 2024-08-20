
import asyncio
from websockets.sync.client import connect
import time

HEAD_1_ADDRESS = '10.10.3.15:7891'
HEAD_2_ADDRESS = '10.10.3.12:7891'
HEAD_3_ADDRESS = '10.10.3.13:7891'
HEAD_4_ADDRESS = '10.10.3.14:7891'
HEAD_5_ADDRESS = '10.10.3.16:7891'
HEAD_6_ADDRESS = '10.10.3.10:7891'

def hello():
    with connect("ws://" + HEAD_3_ADDRESS) as websocket:
        while True:
            websocket.send("imu/orientation_x")
            message = websocket.recv()
            orientation_x = 360.0 - float(message)

            websocket.send("imu/head_orientation")
            message = websocket.recv()
            head_orientation = float(message)

            print(f"orientation_x: {orientation_x}, head_orientation: {head_orientation}")
            time.sleep(1/10.0)

hello()
