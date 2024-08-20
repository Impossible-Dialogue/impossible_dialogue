import sys
from opclib import opc
import numpy as np


NUM_LEDS = 500
HEAD_1_ADDRESS = '10.10.3.15:7890'
HEAD_2_ADDRESS = '10.10.3.12:7890'
HEAD_3_ADDRESS = '10.10.3.13:7890'
HEAD_4_ADDRESS = '10.10.3.14:7890'
HEAD_5_ADDRESS = '10.10.3.16:7890'
HEAD_6_ADDRESS = '10.10.3.10:7890'
FIRE_PIT_ADDRESS = '10.10.3.11:7890'

def main():
    # Create a client object
    client = opc.Client(FIRE_PIT_ADDRESS)
    if len(sys.argv) > 1:
        count = int(sys.argv[1])
    else:
        count = 20


    # Test if it can connect (optional)
    if client.can_connect():
        print('connected to %s' % FIRE_PIT_ADDRESS)
    else:
        # We could exit here, but instead let's just print a warning
        # and then keep trying to send pixels in case the server
        # appears later
        print('WARNING: could not connect to %s' % ADDRESS)

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
