import asyncio
from QUIC import QUIC_CONNECTION

LOCAL_ADDRESS = '127.0.0.1'
TARGET_PORT = 9191
FILE_TO_SEND = "random_data_file.txt"


async def transmit_data(file_to_send: str, num_of_streams: int):
    """
    This method is used to send data to the receiver. The data is read from a file and sent to the receiver.
    The method is defined as an asynchronous method to allow for the use of the await keyword,
    which is used to wait for the completion of the send_data method.
    """
    conn = QUIC_CONNECTION()
    conn.connect_to(LOCAL_ADDRESS, TARGET_PORT)

    with open(file_to_send, "rb") as file:
        content = file.read()

    # num_of_streams = int(input("Enter the desired number of streams: "))
    payload = [content] * num_of_streams
    await conn.send_data(payload)

    # Adding a small delay before closing the connection
    await asyncio.sleep(0.01)
    conn.end_communication()


if __name__ == '__main__':
    asyncio.run(transmit_data(FILE_TO_SEND, 3))
