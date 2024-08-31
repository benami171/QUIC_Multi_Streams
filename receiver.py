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

import asyncio
from QUIC import QUIC_CONNECTION

BIND_ADDRESS = '0.0.0.0'
LISTEN_PORT = 9191


async def accept_data() -> None:
    conn = QUIC_CONNECTION()
    conn.listen_incoming_connections(BIND_ADDRESS, LISTEN_PORT)

    while True:
        data_batch = await conn.receive_data()
        if data_batch is None:
            break

        """
        taking the data_batch and writing each data chunk to a separate file
        """
        for index, data_chunk in enumerate(data_batch):
            file_name = f"output_f{index}.txt"
            with open(file_name, "wb") as output_file:
                output_file.write(data_chunk)

    conn.end_communication()


def main():
    asyncio.run(accept_data())


if __name__ == '__main__':
    main()

