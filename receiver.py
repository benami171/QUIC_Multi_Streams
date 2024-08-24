from QUIC import QUIC_CONNECTION
import asyncio

async def start_receiver():
    connection = QUIC_CONNECTION()
    print("Listening for incoming connections")
    connection.listen_incoming_connections('127.0.0.1', 8855)
    while True:
        print("Waiting for incoming data")
        data = await connection.receive_data()
        if data is None:
            break
        print(f"Received data: {data}")



if __name__ == "__main__":
    asyncio.run(start_receiver())
