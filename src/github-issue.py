import logging

import socketio
import uvicorn
from fastapi import FastAPI

app = FastAPI()
sio = socketio.AsyncClient(logger=True, engineio_logger=True)

logging.basicConfig(format='%(asctime)s %(levelname)-8s: %(message)s')


@app.on_event('startup')
async def startup():
    await sio.connect('http://localhost:8080')


@app.on_event('shutdown')
async def shutdown():
    await sio.disconnect()


@app.get('/')
async def root():
    return {'message': 'Hello world'}


@sio.event
async def connect():
    print('connection established')
    await sio.emit('Hello server')


@sio.on('redemption')
async def on_message(data):
    print('Channel points redeemed!', data)


@sio.event
async def disconnect():
    print('disconnected from server')


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
