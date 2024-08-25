# from QUIC import QUIC_CONNECTION
# import asyncio
#
# async def start_receiver():
#     connection = QUIC_CONNECTION()
#     print("Listening for incoming connections")
#     connection.listen_incoming_connections('0.0.0.0', 4422)
#     while True:
#         print("Waiting for incoming data")
#         data = await connection.receive_data()
#         if data is None:
#             break
#         print(f"Received data: {data}")
#
#
#
# if __name__ == "__main__":
#     asyncio.run(start_receiver())

from QUIC import *

HOST = '0.0.0.0'  # listen on all interfaces
PORT = 4422


async def receiver() -> None:
    conn = QUIC_CONNECTION()
    conn.listen_incoming_connections(HOST, PORT)

    # Keep receiving file data until the connection is closed
    while (file_data := await conn.receive_data()) is not None:
        # save the file data to a file
        for i, file in enumerate(file_data):
            with open(f"file_{i}.txt", "wb") as f:
                print(" WRITING TO FILE ")
                f.write(file)
    conn.end_communication()


if __name__ == '__main__':
    asyncio.run(receiver())
