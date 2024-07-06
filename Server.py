from aioquic.asyncio import connect
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import StreamDataReceived, ConnectionTerminated

class QuicClientProtocol(QuicConnectionProtocol):
    def quic_event_received(self, event):
        if isinstance(event, StreamDataReceived):
            print(f"Data received from server on stream {event.stream_id}: {event.data.decode()}")

async def run_client():
    configuration = QuicConfiguration(is_client=True)
    
    # Connect to the server
    async with connect('127.0.0.1', 4433, configuration=configuration, create_protocol=QuicClientProtocol) as protocol:
        try:
            # Open multiple streams for different types of data
            for i in range(5):
                stream_id = protocol._quic.get_next_available_stream_id()
                data_message = f"Data from stream {i}".encode()
                protocol._quic.send_stream_data(stream_id, data_message, end_stream=True)
            
            # Wait for all streams to be acknowledged or closed
            await protocol._quic.wait_closed()
        
        except Exception as e:
            print(f"An error occurred: {e}")
            protocol._quic.close()

# Start the client
import asyncio
asyncio.run(run_client())
