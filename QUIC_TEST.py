from QUIC import QUIC_CONNECTION
import threading
import asyncio

# Server address and port
SERVER = ('127.0.0.1', 9191)
# Source file to be transferred
SOURCE_FILE = "random_data_file.txt"
# Number of streams to be used for the transfer
STREAM_COUNT = 3


class FileTransferManager:
    @staticmethod
    async def handle_incoming_data():
        # Create a new QUIC connection and listen for incoming connections
        connection = QUIC_CONNECTION()
        connection.listen_to(*SERVER)
        received_data = None

        # Continuously receive data until no more data is incoming
        while True:
            incoming = await connection.receive_data()
            if incoming is None:
                break
            received_data = incoming

        # Check if the received data matches the expected number of streams
        if not received_data or len(received_data) != STREAM_COUNT:
            print(f"Error: Expected {STREAM_COUNT} streams, got {len(received_data) if received_data else 0}")
            return

        # Compare the received data with the original source file
        with open(SOURCE_FILE, 'rb') as original:
            original_content = original.read()
            for stream_data in received_data:
                if stream_data != original_content:
                    print("Error: Data mismatch detected")
                    return

        # Print success message if all data matches
        print("Success: All received data matches the source")

    @staticmethod
    async def transmit_data():
        # Wait for a short period to ensure the receiver is ready
        await asyncio.sleep(1)
        # Read the content of the source file
        with open(SOURCE_FILE, "rb") as source:
            content = source.read()
            # Create a new QUIC connection and connect to the server
            connection = QUIC_CONNECTION()
            connection.connect_to(*SERVER)
            # Send the data over the specified number of streams
            await connection.send_data([content] * STREAM_COUNT)
            # End the communication by sending a FIN packet
            connection.end_communication()


def execute_async(coroutine):
    """
    This function is used to run an asynchronous coroutine in a synchronous manner.
    meaning that it will block the main thread until the coroutine completes.
    """
    # Create a new event loop and set it as the current event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Run the coroutine until it completes
        return loop.run_until_complete(coroutine)
    finally:
        # Close the event loop
        loop.close()


def simulate_transfer():
    def initiate_receiver():
        # Execute the handle_incoming_data coroutine
        execute_async(FileTransferManager.handle_incoming_data())

    def initiate_sender():
        # Execute the transmit_data coroutine
        execute_async(FileTransferManager.transmit_data())

    # Create threads for the receiver and sender
    receive_thread = threading.Thread(target=initiate_receiver)
    send_thread = threading.Thread(target=initiate_sender)

    # Start the receiver and sender threads
    receive_thread.start()
    send_thread.start()

    # Wait for both threads to complete
    receive_thread.join()
    send_thread.join()


if __name__ == '__main__':
    # Start the file transfer simulation
    simulate_transfer()
