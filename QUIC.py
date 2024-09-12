import random
from socket import socket, AF_INET, SOCK_DGRAM
import math
import struct
import time
import asyncio
from enum import IntEnum
from typing import Dict, List, Tuple

OVERALL_DATA = 0  # The position in the stats dictionary for overall data that was sent/received

class FLAGS(IntEnum):
    SYN = 1
    SYN_ACK = 2
    ACK = 3
    DATA_PACKET = 4
    END_OF_DATA = 5
    FIN = 6
    FIRST_PACKET = 7
    LAST_PACKET = 8


class QUIC_CONNECTION:

    def __init__(self):
        # Initialize attributes for the connection state
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.is_closed = False

        # Variables to store host and port for reuse
        self.host_address = None
        self.port = None

        # Initialize stream-related attributes
        self.stream_ID = 0  # each stream has a unique ID

        # Dictionaries to store incoming and outgoing streams
        # Dictionaries to store stream statistics, and connection statistics for further analysis
        self.in_streams: Dict[int, bytes] = {}
        self.out_streams: Dict[int, bytes] = {}
        self.streams_stats: Dict[int, Stats] = {}
        self.connection_stats: Dict[int, Stats] = {}

    def listen_to(self, host: str, port: int):
        """Listen for incoming connections."""
        print(f"Listening for incoming connections on {host}:{port}")
        self.host_address = host
        self.port = port
        # bind the socket to the host and port
        self.sock.bind((self.host_address, self.port))
        received_data, address = self.sock.recvfrom(QUIC_PACKET.Max_size)

        received_packet = QUIC_PACKET.deserialize_data(received_data)[0]
        if received_packet.packet_flag == FLAGS.SYN:
            print(f"Received SYN packet from client in address: {address}")
            received_packet.packet_flag = FLAGS.SYN_ACK
            self.sock.sendto(received_packet.serialize_data(), address)
        else:
            # at this point we only want to receive SYN packets
            raise Exception("Unexpected packet received")

    def connect_to(self, host: str, port: int):
        self.host_address = host
        self.port = port

        # Create a packet of type SYN (synchronize) to initiate the connection
        connect_packet = QUIC_PACKET(FLAGS.SYN)  # create a SYN type packet

        # Send the SYN packet to the specified host and port using a socket
        self.sock.sendto(connect_packet.serialize_data(), (self.host_address, self.port))

        # Wait to receive data from the server
        received_data, address = self.sock.recvfrom(QUIC_PACKET.Max_size)

        # Deserialize the received data into a QUIC_PACKET object
        received_packet = QUIC_PACKET.deserialize_data(received_data)[0]

        # Check if the received packet has a SYN_ACK flag, which indicates that the server acknowledged the connection request
        if received_packet.packet_flag == FLAGS.SYN_ACK:
            print("GOT SYN_ACK FROM THE SERVER")
        else:
            raise Exception("Connection failed")

    async def send_data(self, list_of_files: List[bytes]) -> None:

        # Store each file in the out_streams dictionary with a unique index as the key
        for i, file in enumerate(list_of_files):
            self.out_streams[i + 1] = file

        # Asynchronously send the data from all streams to the server
        await self.send_to_streams()
        print("Data sent successfully")

        # Clear the out_streams dictionary to free memory or prepare for new data
        self.out_streams.clear()

        # Create a packet signaling the end of data transmission using the END_OF_DATA flag
        final_packet = QUIC_PACKET(FLAGS.END_OF_DATA)

        # Send the end-of-data packet to the server to signal the completion of data transmission
        self.sock.sendto(final_packet.serialize_data(), (self.host_address, self.port))

    async def send_to_streams(self) -> None:
        # Use asyncio.gather to run the `send_stream_data` coroutine for each stream concurrently
        await asyncio.gather(*(self.send_stream_data(stream_id) for stream_id in self.out_streams))

    async def send_stream_data(self, stream_id: int) -> None:
        """
        1. get the data from each stream by stream_id
        2. generate random frame size and calculate number of frames needed.
        3. calculate frames per packet
        4. calculate number of packets needed.
        5. divide the data to frames and add the frames to the packet.
        6. send the frames on the stream.
        """
        data_from_stream = self.out_streams[stream_id]
        # generate random frame size
        frame_size = int(random.uniform(1000, 2000))
        # calculate the frame payload size (without the header)
        frame_payload_size = frame_size - QUIC_PACKET.FRAME_LENGTH
        # calculate the number of frames per packet
        frames_per_packet = math.floor(QUIC_PACKET.MAX_DATA_SIZE / frame_size)
        needed_frames_amount = math.ceil(len(data_from_stream) / frame_payload_size)
        packet_payload_size = frames_per_packet * frame_payload_size
        needed_packets_amount = math.ceil(needed_frames_amount / frames_per_packet)
        current_frame = 0

        for i in range(needed_packets_amount):
            #
            if i == 0:
                packet = QUIC_PACKET(FLAGS.FIRST_PACKET)

            elif i == needed_packets_amount - 1:
                packet = QUIC_PACKET(FLAGS.LAST_PACKET)
            else:
                packet = QUIC_PACKET(FLAGS.DATA_PACKET)

            bytes_added_until_now = i * packet_payload_size
            for frame_offset in range(frames_per_packet):
                start_index = bytes_added_until_now + frame_offset * frame_payload_size
                if current_frame == needed_frames_amount - 1:
                    end_index = start_index + min((packet_payload_size - (frame_offset - 1) * frame_payload_size),
                                                  frame_payload_size)
                else:
                    end_index = start_index + frame_payload_size
                awaiting_data = data_from_stream[start_index:end_index]
                current_frame += 1

                packet.link_frame(stream_id, frame_offset, awaiting_data)
            self.sock.sendto(packet.serialize_data(), (self.host_address, self.port))
            await asyncio.sleep(0.001)

    async def receive_data(self) -> List[bytes] | None:
        """
        1. receive data from the socket and divide it into packet and frames
        2. if the packet is not SYN/ACK/SYN_ACK/FIN start measuring time
        3. if the stream_id is not in the streams stats dictionary,add it
        :return:
        """
        frames_received_counter = 0
        while True:
            received_data, address = self.sock.recvfrom(QUIC_PACKET.Max_size)
            received_packet, received_frames = QUIC_PACKET.deserialize_data(received_data)

            if received_packet.packet_flag not in (FLAGS.SYN, FLAGS.ACK,
                                                   FLAGS.SYN_ACK, FLAGS.FIN):

                frames_received_counter += len(received_frames)
                # GOT THE FIRST PACKET OF THE SPECIFIC STREAM, START MEASURING TIME

                if received_packet.packet_flag == FLAGS.FIRST_PACKET:
                    if received_frames[0].stream_id not in self.streams_stats:
                        self.streams_stats[received_frames[0].stream_id] = Stats(received_frames[0].stream_id, 0, 0, 0,
                                                                                 time.time())
                    if OVERALL_DATA not in self.connection_stats:
                        self.connection_stats[OVERALL_DATA] = Stats(0, 0, 0, 0, time.time())

                if len(received_frames) != 0:
                    self.streams_stats[received_frames[0].stream_id].frames_amount += len(received_frames)
                    self.connection_stats[OVERALL_DATA].frames_amount += len(received_frames)
                # GOT THE LAST PACKET OF THE SPECIFIC STREAM, MEASURING END TIME
                if received_packet.packet_flag == FLAGS.LAST_PACKET:
                    self.streams_stats[received_frames[0].stream_id].time = time.time() - self.streams_stats[
                        received_frames[0].stream_id].time

                # GOT THE LAST PACKET OF THE PAYLOAD, MEASURING END TIME
                if received_packet.packet_flag == FLAGS.END_OF_DATA:
                    self.connection_stats[OVERALL_DATA].time = time.time() - self.connection_stats[OVERALL_DATA].time
                    self.print_stats()
                    break

                # UPDATE STATS
                self.streams_stats[received_frames[0].stream_id].packets_amount += 1
                self.streams_stats[received_frames[0].stream_id].total_bytes_amount += len(received_data)
                self.connection_stats[OVERALL_DATA].packets_amount += 1
                self.connection_stats[OVERALL_DATA].total_bytes_amount += len(received_data)

                # AFTER RECEIVING PACKET, SEND ACK
                self.sock.sendto(QUIC_PACKET(FLAGS.ACK).serialize_data(), address)
                for frame in received_frames:
                    if frame.stream_id not in self.in_streams:
                        self.in_streams[frame.stream_id] = frame.frame_data
                    else:
                        self.in_streams[frame.stream_id] += frame.frame_data

            if received_packet.packet_flag == FLAGS.FIN:
                self.terminate_connection()
                return None

        received_files = list(self.in_streams.values())
        self.in_streams.clear()
        return received_files

    def print_stats(self) -> None:

        """
         Prints the overall connection statistics and per-stream statistics, including the total bytes, packets,
         and average transmission rates per second for both the overall connection and individual streams.

         """

        # Overall statistics
        print("********** Overall Connection Statistics **********\n")

        # Gather overall statistics for all connections
        total_bytes = self.connection_stats[
            OVERALL_DATA].total_bytes_amount  # Total bytes transferred in the connection
        total_packets = self.connection_stats[OVERALL_DATA].packets_amount  # Total number of packets transferred
        total_time = self.connection_stats[OVERALL_DATA].time  # Total time for the connection in seconds

        # Calculate the average bytes per second and packets per second for the overall connection
        overall_avg_bytes_per_sec = total_bytes / total_time
        overall_avg_packets_per_sec = total_packets / total_time

        print(f"Overall average bytes per second: {overall_avg_bytes_per_sec:.2f} bytes/sec")
        print(f"Overall average packets per second: {overall_avg_packets_per_sec:.2f} packets/sec\n")

        # Iterate over each stream's statistics and print details
        for stream_id, stats in self.streams_stats.items():
            # Retrieve stream-specific statistics
            stream_total_bytes = stats.total_bytes_amount  # Total bytes transferred in the stream
            stream_total_packets = stats.packets_amount  # Total number of packets transferred in the stream
            stream_time = stats.time  # Total time for the stream in seconds

            # Calculate the average bytes per second and packets per second for the stream
            avg_bytes_per_sec = stream_total_bytes / stream_time
            avg_packets_per_sec = stream_total_packets / stream_time

            print(f"Stream ID: {stream_id}")
            print(f"  Total bytes: {stream_total_bytes} bytes")
            print(f"  Total packets: {stream_total_packets} packets")
            print(f"  Average bytes per second: {avg_bytes_per_sec:.2f} bytes/sec")
            print(f"  Average packets per second: {avg_packets_per_sec:.2f} packets/sec")
            print()

        print("********** End of Statistics **********")

    # will be used when we get FIN packet.
    def terminate_connection(self) -> None:
        """
        Terminates the connection when a FIN (Finish) packet is received.
        This method performs cleanup by closing the socket and marking the connection as closed.
        """

        print(f"Got FIN packet, terminating connection")
        self.sock.close()
        self.is_closed = True

    # send FIN packet to the other side.

    def end_communication(self):
        """
        Sends a FIN (Finish) packet to the other side to signal the end of communication,
        and then terminates the local connection.

        This method first checks if the connection is already closed. If not, it sends a FIN packet
        to signal that no more data will be sent and then calls `terminate_connection` to clean up the connection.
        """

        if self.is_closed:
            return

        self.sock.sendto(QUIC_PACKET(FLAGS.FIN).serialize_data(), (self.host_address, self.port))
        self.terminate_connection()


class Stats:
    def __init__(self, stream_id: int, packets_amount: int, frames_amount: int, bytes_amount: int, _time: float):
        self.stream_id = stream_id
        self.packets_amount = packets_amount
        self.frames_amount = frames_amount
        self.total_bytes_amount = bytes_amount
        self.time = _time


class QUIC_PACKET:
    packet_id_counter = 0
    Max_size = 9000
    HEADER_LENGTH = struct.calcsize('!BIQ')
    FRAME_LENGTH = struct.calcsize('!IIQ')
    MAX_DATA_SIZE = Max_size - HEADER_LENGTH

    def __init__(self, flag):

        """
            Initializes a QUIC_PACKET instance.

            Args:
                flag (int): A flag indicating the type or purpose of the packet. This flag is assigned to `self.packet_flag`.

            Attributes:
                packet_ID (int): A unique identifier for the packet, incremented for each new instance.
                packet_flag (int): The flag indicating the type of packet (e.g., SYN, ACK, FIN).
                packet_data (bytearray): A mutable sequence of bytes used to store the packet's data.
            Returns:
                None
            """

        # Increment the global packet ID counter to ensure unique IDs for each packet
        QUIC_PACKET.packet_id_counter += 1
        self.packet_ID = QUIC_PACKET.packet_id_counter
        self.packet_flag = flag

        # Initialize packet_data as an empty bytearray for storing data
        self.packet_data = bytearray()  # using bytearray because it is mutable and can be modified

    @classmethod
    def deserialize_data(cls, data: bytes) -> Tuple['QUIC_PACKET', List['QUIC_FRAME']]:

        """
        Deserializes a byte sequence into a QUIC_PACKET and its associated QUIC_FRAME objects.

        This method takes a byte sequence, extracts the packet header, and deserializes it into
        a QUIC_PACKET instance. It also processes the remaining data to extract QUIC_FRAME objects.

        """
        packet_header = struct.unpack('!BIQ', data[:cls.HEADER_LENGTH])
        flag, packet_id, data_size = packet_header
        packet = QUIC_PACKET(flag)
        packet.packet_ID = packet_id
        packet.packet_data = bytearray(data[cls.HEADER_LENGTH: cls.HEADER_LENGTH + data_size])

        packet_frames = []
        frame_position_offset = 0
        while frame_position_offset < len(packet.packet_data):
            frame_header = struct.unpack('!IIQ',
                                         packet.packet_data[
                                         frame_position_offset:frame_position_offset + cls.FRAME_LENGTH])
            stream_id, position_in_stream, frame_size = frame_header
            frame_position_offset += cls.FRAME_LENGTH  # skip to the next frame by frame length
            frame_data = packet.packet_data[frame_position_offset:frame_position_offset + frame_size]
            frame_to_add = QUIC_FRAME(stream_id, position_in_stream, frame_data)
            packet_frames.append(frame_to_add)
            frame_position_offset += frame_size

        return packet, packet_frames

    def serialize_data(self) -> bytes:
        """
          Serializes the QUIC_PACKET instance into a byte sequence for transmission or storage.

          This method converts the packet's header and data into a byte sequence that can be easily sent over a network
          or stored in a file. The header includes the packet flag, packet ID, and the size of the data. The data itself
          is appended after the header.
          """
        packet_header = struct.pack('!BIQ', self.packet_flag, self.packet_ID, len(self.packet_data))
        return packet_header + self.packet_data

    def link_frame(self, stream_id: int, position_in_stream: int, data: bytes):
        """
           Appends a QUIC_FRAME to the packet's data.

           This method creates a frame with the given stream ID, position within the stream, and data, and then appends
           this frame to the packet's data. The method checks if the total packet data size exceeds the maximum allowed
           size and raises an exception if it does.

           """

        frame_to_link = struct.pack('!IIQ', stream_id, position_in_stream, len(data)) + data
        if len(self.packet_data) + len(frame_to_link) > QUIC_PACKET.MAX_DATA_SIZE:
            raise Exception("Frame size is too large")
        self.packet_data += frame_to_link


class QUIC_FRAME:
    """
    Represents a frame in a QUIC packet.

    A QUIC frame consists of a stream ID, a position within the stream, and the actual data of the frame. 
    This class provides the attributes to store these components and a method to get the length of the frame's data.

    """

    def __init__(self, stream_id: int, position_in_stream: int, data: bytes):
        self.stream_id = stream_id
        self.position_in_stream = position_in_stream
        self.frame_data = data

    def __len__(self):
        return len(self.frame_data)
