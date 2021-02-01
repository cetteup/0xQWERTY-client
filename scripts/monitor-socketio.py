import asyncio

import socketio

sio = socketio.AsyncClient()
streamers = ['lifebd', 'ghostgaminggg']


@sio.event
def message(data):
    print('Received message: ', data)


@sio.on('redemption')
async def on_message(data):
    print('Channel points redeemed: ', data)


@sio.event
async def connect():
    print('Connected!')
    for streamer in streamers:
        await sio.emit('join', f'streamer:{streamer}')


@sio.event
async def connect_error():
    print('Connection failed!')


@sio.event
async def disconnect():
    print('Disconnected!')


async def main():
    await sio.connect('https://api.0xqwerty.com')
    await sio.wait()


asyncio.run(main())
