import sys
from opclib import opc
import numpy as np


NUM_LEDS = 500
IP_ADDRESSES = {
    '1': '10.10.3.15:7890',  # HEAD_1
    '2': '10.10.3.12:7890',  # HEAD_2
    '3': '10.10.3.13:7890',  # HEAD_3
    '4': '10.10.3.14:7890',  # HEAD_4
    '5': '10.10.3.16:7890',  # HEAD_5
    '6': '10.10.3.10:7890',  # HEAD_6
    'f': '10.10.3.11:7890',  # FIRE_PIT
}

def main():
    if len(sys.argv) > 1:
        object_id = sys.argv[1]
    else:
        object_id = "1"
    count = 1

    # Create a client object
    address = IP_ADDRESSES[object_id]
    client = opc.Client(address)

    # Test if it can connect (optional)
    if client.can_connect():
        print('connected to %s' % address)
    else:
        # We could exit here, but instead let's just print a warning
        # and then keep trying to send pixels in case the server
        # appears later
        print('WARNING: could not connect to %s' % address)

    # Send messages to all the bars
    while True:
        rgbs = np.zeros((NUM_LEDS, 3), int)
        for i in range(NUM_LEDS):
            rgbs[i, :] = (0, 0, 0)
        for i in range(count - 1):
            rgbs[i, :] = (255, 255, 255)
        rgbs[count - 1, :] = (255, 0, 0)
        client.put_pixels(rgbs, channel=1)
        count = int(input("Number of LEDs: "))


if __name__ == '__main__':
    main()
