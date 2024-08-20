from opclib import opc
import time

HEAD_1_ADDRESS = '10.10.3.15:7890'
HEAD_2_ADDRESS = '10.10.3.12:7890'
HEAD_3_ADDRESS = '10.10.3.13:7890'
HEAD_4_ADDRESS = '10.10.3.14:7890'
HEAD_5_ADDRESS = '10.10.3.16:7890'
HEAD_6_ADDRESS = '10.10.3.10:7890'
FIRE_PIT_ADDRESS = '10.10.3.11:7890'

# Create a client object
client = opc.Client(FIRE_PIT_ADDRESS)

# Test if it can connect (optional)
if client.can_connect():
    print('connected to %s' % ADDRESS)
else:
    # We could exit here, but instead let's just print a warning
    # and then keep trying to send pixels in case the server
    # appears later
    print('WARNING: could not connect to %s' % ADDRESS)

# Send pixels forever at 30 frames per second
while True:
    my_pixels = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    if client.put_pixels(my_pixels, channel=1):
        print('...')
    else:
        print('not connected')
    time.sleep(1/30.0)