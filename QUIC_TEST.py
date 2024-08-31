# from QUIC import *
# import threading
# import asyncio
#
# HOST = '127.0.0.1'
# PORT = 9191
# FILE_TO_SEND = "random_data_file.txt"
# NUMBER_OF_STREAMS = 3
#
#
# async def start_receiver():
#     conn = QUIC_CONNECTION()
#     conn.listen_incoming_connections(HOST, PORT)
#     file_data = []
#
#     while True:
#         new_file_data = await conn.receive_data()
#         if new_file_data is None:
#             break
#         file_data = new_file_data
#
#     if len(file_data) != NUMBER_OF_STREAMS:
#         print("Error: Insufficient number of files received")
#         return
#
#     with open(FILE_TO_SEND, 'rb') as f1:
#         original_data = f1.read()
#         for file in file_data:
#             if original_data != file:
#                 print("Error: Files are not equal")
#                 return
#
#     print("Comparison successful")
#     return
#
#
# async def start_sender():
#     await asyncio.sleep(1)  # wait for the receiver to start listening
#     with open(FILE_TO_SEND, "rb") as f:
#         file_data = f.read()
#         conn = QUIC_CONNECTION()
#         conn.connect_to(HOST, PORT)
#         await conn.send_data([file_data] * NUMBER_OF_STREAMS)
#         conn.end_communication()
#
#
# def run_async_function(func):
#     # Run the async function
#     asyncio.set_event_loop(asyncio.new_event_loop())
#     loop = asyncio.get_event_loop()
#     result = loop.run_until_complete(func())
#     loop.close()
#     return result
#
#
# def main():
#     receiver_result = None
#
#     def run_receiver():
#         nonlocal receiver_result
#         receiver_result = run_async_function(start_receiver)
#
#     def run_sender():
#         run_async_function(start_sender)
#
#     # Run the receiver and sender in two different threads
#     receiver_thread = threading.Thread(target=run_receiver)
#     sender_thread = threading.Thread(target=run_sender)
#
#     receiver_thread.start()
#     sender_thread.start()
#
#     # Wait for the two threads to finish
#     receiver_thread.join()
#     sender_thread.join()
#
#     # Print the results
#     print(receiver_result)
#
#
# if __name__ == '__main__':
#     main()
import time

from QUIC import QUIC_CONNECTION as QuicConn
import threading
import asyncio

# Server and client configuration
SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 9191
SOURCE_FILE = "random_data_file.txt"
STREAMS_COUNT = 3


async def receive_files():
    # Setup QUIC connection and listen for incoming connections
    receiver_conn = QuicConn()
    receiver_conn.listen_incoming_connections(SERVER_ADDRESS, SERVER_PORT)
    received_files = []

    while True:
        incoming_data = await receiver_conn.receive_data()
        if incoming_data is None:
            break
        received_files = incoming_data

    # Verify the number of received files
    if len(received_files) != STREAMS_COUNT:
        print("Error: Mismatch in the number of received files")
        return

    # Compare each received file with the original file data
    with open(SOURCE_FILE, 'rb') as original_file:
        original_content = original_file.read()
        for received_content in received_files:
            if received_content != original_content:
                print("Error: Discrepancy found in file contents")
                return

    print("File transfer successful and contents match.")
    return


async def send_files():
    # Delay to ensure the receiver is ready
    await asyncio.sleep(1)

    # Read and send file data using QUIC connection
    with open(SOURCE_FILE, "rb") as source_file:
        file_content = source_file.read()
        sender_conn = QuicConn()
        sender_conn.connect_to(SERVER_ADDRESS, SERVER_PORT)
        await sender_conn.send_data([file_content] * STREAMS_COUNT)
        sender_conn.end_communication()


def execute_async_task(async_task):
    # Initialize and run the event loop for asynchronous tasks
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(async_task())
    finally:
        loop.close()
    return result


def execute_receiver():
    return execute_async_task(receive_files)


def execute_sender():
    time.sleep(1)
    return execute_async_task(send_files)


def run_transfer():
    receiver_output = None

    # Wrapper functions for threading
    def initiate_receiver():
        nonlocal receiver_output
        receiver_output = execute_receiver()

    def initiate_sender():
        execute_sender()

    # Create and start threads for receiver and sender
    receiver_thread = threading.Thread(target=initiate_receiver)

    sender_thread = threading.Thread(target=initiate_sender)

    receiver_thread.start()
    sender_thread.start()

    # Wait for both threads to complete
    receiver_thread.join()
    sender_thread.join()

    # Display the result of the file transfer
    print(receiver_output)


if __name__ == '__main__':
    run_transfer()
