# from QUIC import QUIC_CONNECTION, FLAGS
# import asyncio
#
# async def start_sender():
#     quic_conn = QUIC_CONNECTION()
#     quic_conn.connect_to('127.0.0.1', 4422)
#     print("Connection established with receiver")
#     await asyncio.sleep(0.001)
#
#     num_of_streams = int(input("Enter the desired number of streams: "))
#
#     with open("random_data.txt", "r") as file:
#         file_data = file.read().encode()
#         await quic_conn.send_data([file_data]*num_of_streams)
#         print("Data sent")
#         await asyncio.sleep(0.001)
#         quic_conn.end_communication()
#
#
#
# if __name__ == "__main__":
#     asyncio.run(start_sender())

import asyncio

from QUIC import *

HOST = '127.0.0.1'
PORT = 4422


async def sender():
    with open("random_data.txt", "r") as f:
        file_data = f.read()

        conn = QUIC_CONNECTION()

        conn.connect_to(HOST, PORT)
        await conn.send_data([file_data.encode()]*3)
        # sleep for two seconds
        await asyncio.sleep(0.01)
        conn.end_communication()


if __name__ == '__main__':
    asyncio.run(sender())
