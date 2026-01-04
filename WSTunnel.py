#!/usr/bin/env python

"""Echo server using the asyncio API."""

import asyncio
import easygui
import socket
from websockets import ConnectionClosed, InvalidMessage
from websockets.asyncio.server import serve
from websockets.asyncio.client import connect

server = None

uri = easygui.enterbox("Enter the websocket location you would like to proxy to.")
    
print(f'Using {uri} for proxy destination')

target = None
client = None
forward_task = None
backwards_task = None

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

async def forward(websocket):
    async for message in websocket:
        await target.send(message)
    
async def and_back(websocket):
    async for message2 in target.__aiter__():
        await websocket.send(message2)
        
async def two_ways(websocket):
    print("New Connection")
    global client
    global forward_task
    global backwards_task
    if(client):
        print("Killing Old Session")
        await client.close()
        forward_task.cancel()
        backwards_task.cancel()
    client = websocket
    forward_task = asyncio.create_task(forward(websocket))
    backwards_task = asyncio.create_task(and_back(websocket))
    print('Starting Tasks')
    try:
        print("Opening Socket")
        msg = "Now Running Websocket Proxy"
        choices = ["Yes","No","No opinion"]
        # reply = easygui.buttonbox(msg, choices=choices)
        await asyncio.gather(forward_task, backwards_task)
        
    except ConnectionClosed:
        client = None
        print('Ending Tasks')
        forward_task.cancel()
        backwards_task.cancel()

async def main():
    port = 8765
    available_port = False
    while not available_port:
        port_in_use = is_port_in_use(port)
        if(port_in_use):
            port = port + 1
        else:
            available_port = True

    async with serve(two_ways, "localhost", port) as server2:
        connected = False
        print(f'Use ws://localhost:{port} to connect')
        global target
        try:
            if('//' in uri):
                print('connection to native protocol')
                target = await connect(uri)
            else:
                print('connection to wss')
                target = await connect('wss://' + uri)
        except:
            print('connection to ws')
            target = await connect('ws://' + uri)
            
        await server2.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())