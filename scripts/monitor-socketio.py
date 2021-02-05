import argparse
import asyncio

import socketio

parser = argparse.ArgumentParser(description='Monitor rooms on a socket.io server')
parser.add_argument('--rooms', help='Names of rooms to monitor', nargs='+', type=str, required=True)
parser.add_argument('--server', help='Server to connect to', type=str, default='https://api.0xqwerty.com')
args = parser.parse_args()

sio = socketio.AsyncClient()


@sio.event
def message(data):
    print('Received message: ', data)


@sio.on('redemption')
async def on_message(data):
    print('Channel points redeemed: ', data)


@sio.event
async def connect():
    print('Connected!')
    for streamer in args.rooms:
        await sio.emit('join', f'streamer:{streamer}')


@sio.event
async def connect_error():
    print('Connection failed!')


@sio.event
async def disconnect():
    print('Disconnected!')


async def main():
    await sio.connect(args.server)
    await sio.wait()


asyncio.run(main())
