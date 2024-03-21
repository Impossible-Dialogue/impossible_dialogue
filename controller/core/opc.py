import asyncio

from opclib import opc


class OpenPixelControlClient(asyncio.Protocol):
    def __init__(self, generator, object_id):
        super().__init__()
        self.transport = None
        self.opc = None
        self.generator = generator
        self.object_id = object_id
        

    def connection_made(self, transport):
        """Store the OpenPixelControl transport and schedule the task to send data.
        """
        self.transport = transport
        self.opc = opc.Client("FOO:1234")
        self.opc._socket = transport.get_extra_info('socket')._sock
 
        if self.opc.can_connect():
            print('Open Pixel Control connection created')
        else:
            print('WARNING: could not connect to Open Pixel Control')

        asyncio.ensure_future(self.serve())
        print('OpenPixelControlClient.send() scheduled')

    def connection_lost(self, exc):
        print('OpenPixelControlClient closed')

    async def serve(self):
        while True:
            segments = await asyncio.shield(self.generator.result)
            (object_ids, led_segments, _) = await asyncio.shield(self.generator.result)
            for object_id in object_ids:
                # Only push pixels for this objects
                if object_id != self.object_id:
                    continue
                # Any led_segments available
                if object_id not in led_segments:
                    continue
            
                print('Sending OPC packet to object: %s' % object_id)
                segments = led_segments[object_id]
                for channel, segment in enumerate(segments):
                    self.opc.put_pixels(segment.colors, channel)


async def create_opc_connection(loop, protocol_factory, server_ip, server_port, *args, **kwargs):
    transport, protocol = await loop.create_connection(protocol_factory, server_ip, server_port)
    return transport, protocol