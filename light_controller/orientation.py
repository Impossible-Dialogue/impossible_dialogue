
import asyncio
from websockets.sync.client import connect
import time
import sys

IP_ADDRESSES = {
    '1': '10.10.3.15:7891',  # HEAD_1
    '2': '10.10.3.12:7891',  # HEAD_2
    '3': '10.10.3.13:7891',  # HEAD_3
    '4': '10.10.3.14:7891',  # HEAD_4
    '5': '10.10.3.16:7891',  # HEAD_5
    '6': '10.10.3.10:7891',  # HEAD_6
}


def main():
    if len(sys.argv) > 1:
        head_id = sys.argv[1]
    else:
        head_id = 1

    with connect("ws://" + IP_ADDRESSES[head_id]) as websocket:
        while True:
            websocket.send("imu/orientation_x")
            message = websocket.recv()
            orientation_x = 360.0 - float(message)

            websocket.send("imu/orientation_y")
            message = websocket.recv()
            orientation_y = 360.0 - float(message)

            websocket.send("imu/orientation_z")
            message = websocket.recv()
            orientation_z = 360.0 - float(message)

            websocket.send("imu/head_orientation")
            message = websocket.recv()
            head_orientation = float(message)

            websocket.send("imu/calibration_sys")
            message = websocket.recv()
            calibration_sys = int(message)

            websocket.send("imu/calibration_gyro")
            message = websocket.recv()
            calibration_gyro = int(message)
            
            websocket.send("imu/calibration_accel")
            message = websocket.recv()
            calibration_accel = int(message)
            
            websocket.send("imu/calibration_mag")
            message = websocket.recv()
            calibration_mag = int(message)

            websocket.send("imu/timestamp")
            message = websocket.recv()
            imu_timestamp = int(message)

            print(f"t: {imu_timestamp}, x: {orientation_x}, y: {orientation_y}, z: {orientation_z}, head: {head_orientation}, sys: {calibration_sys}, mag: {calibration_mag}, gyro: {calibration_gyro}, accel: {calibration_accel}")
            time.sleep(1/10.0)

main()
