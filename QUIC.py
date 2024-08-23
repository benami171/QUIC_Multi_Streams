import random
import socket
import math
import struct
import time
import asyncio
from enum import IntEnum
from random import randint
from typing import Dict, List, Tuple
from dataclasses import dataclass

from numpy.distutils.conv_template import header


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
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._is_closed = False

        # Variables to store host and port for reuse
        self.host_address = None
        self.port_number = None

        # Initialize stream-related attributes
        self.stream_ID = 0  # each stream has a unique ID

        # Dictionaries to store incoming and outgoing streams
        self.in_streams: Dict[int, bytes] = {}
        self.out_streams: Dict[int, bytes] = {}

        # Dictionary to store stream statistics for further analysis
        self.stream_stats: Dict[int, Stream_Statistics] = {}

    def listen_incoming_connections(self, host: str, port: int):
        """Listen for incoming connections."""
        print(f"Listening for incoming connections on {host}:{port}")
        self.host_address = host
        self.port_number = port
        # bind the socket to the host and port
        self.sock.bind((self.host_address, self.port_number))
        received_data, address = self.sock.recvfrom(QUIC_PACKET.Max_size)

        received_packet = QUIC_PACKET.deserialize_data(received_data)[0]
        if received_packet.packet_flag == FLAGS.SYN:
            print(f"Received SYN packet from client in address: {address}")
            received_packet.packet_flag = FLAGS.SYN_ACK
            self.sock.sendto(received_packet.serialize_data(), address)
        else:
            # at this point we only want to receive SYN packets
            raise Exception("Unexpected packet received")


    def connect(self, host: str, port: int):
        self.host_address = host
        self.port_number = port

        connect_packet = QUIC_PACKET(FLAGS.SYN) # create a SYN type packet
        self.sock.sendto(connect_packet.serialize_data(), (self.host_address, self.port_number))

        received_data, address = self.sock.recvfrom(QUIC_PACKET.Max_size)
        received_packet = QUIC_PACKET.deserialize_data(received_data)[0]

        if received_packet.packet_flag == FLAGS.SYN_ACK:
            print("Received SYN_ACK packet from server")
        else:
            raise Exception("Connection failed")


    async def send_data(self, list_of_files: List[bytes]) -> None:
        for i,file in enumerate(list_of_files):
            self.out_streams[i+1] = file

        await self.send_to_streams()
        print("Data sent successfully")
        self.out_streams.clear()
        final_packet = QUIC_PACKET(FLAGS.FIN)
        self.sock.sendto(final_packet.serialize_data(), (self.host_address, self.port_number))

    async def send_to_streams(self) -> None:

        await asyncio.gather(*(self.send_stream_data(stream_id) for stream_id in self.out_streams))


    async def send_stream_data(self, stream_id: int):
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
        frame_payload_size = frame_size - QUIC_PACKET.FRAME_LENGTH
        needed_frames_amount = math.ceil(len(data_from_stream) / frame_payload_size)
        frames_per_packet = math.ceil(QUIC_PACKET.Max_size / frame_size)
        needed_packets_amount = math.ceil(needed_frames_amount / frames_per_packet)

        for i in range(needed_packets_amount):
            if i==0:
                start_packet = QUIC_PACKET(FLAGS.FIRST_PACKET)
            elif i == needed_packets_amount-1:
                end_packet = QUIC_PACKET(FLAGS.LAST_PACKET)
            else:
                packet = QUIC_PACKET(FLAGS.DATA_PACKET)
                for frame_offset in range(frames_per_packet):
                    if frame_offset == frames_per_packet-1:
                        awaiting_data = data_from_stream[frame_offset*frame_payload_size:]
                        packet.add_frame(stream_id,frame_offset,awaiting_data)
                    else:
                        awaiting_data = data_from_stream[frame_offset*frame_payload_size:(frame_offset+1)*frame_payload_size]
                        packet.add_frame(stream_id,frame_offset,awaiting_data)
                self.sock.sendto(packet.serialize_data(), (self.host_address, self.port_number))
                await asyncio.sleep(0.001)


    async def receive_data(self) -> List[bytes]:
        """
        1. receive data from the socket and divide it into packet and frames
        2. if the packet is not SYN/ACK/SYN_ACK/FIN start measuring time
        3. if the stream_id is not in the streams stats dictionary,add it
        :return:
        """
        received_data, address = self.sock.recvfrom(QUIC_PACKET.Max_size)
        received_packet, received_frames = QUIC_PACKET.deserialize_data(received_data)

        if received_packet.packet_flag != (FLAGS.SYN or FLAGS.ACK or FLAGS.SYN_ACK or FLAGS.FIN):
            if received_packet.packet_flag == FLAGS.FIRST_PACKET:
                self.stream_stats[received_frames[0].stream_id] = Stats(received_frames[0].stream_id,0,0,0,time.time())
            if received_packet.packet_flag == FLAGS.LAST_PACKET:
                end = time.time()
                self.stream_stats[received_frames[0].stream_id].time = end - self.stream_stats[received_frames[0].stream_id].time
        if received_packet.packet_flag == FLAGS.END_OF_DATA:
            end = time.time()
            self.stream_stats[0].time = end - self.stream_stats[0].time
            self.print_stats()

        self.stream_stats[received_frames[0].stream_id].packets_amount += 1
        self.stream_stats[received_frames[0].stream_id].bytes_amount += len(received_data)
        self.stream_stats[0].packets_amount += 1
        self.stream_stats[0].bytes_amount += len(received_data)


        for frame in frames:


    def print_stats(self):
        for stream_id, stats in self.stream_stats.items():
            print(f"Stream ID: {stream_id}")
            print(f"Number of packets: {stats.packets_amount}")
            print(f"Number of frames: {stats.frames_amount}")
            print(f"Total bytes: {stats.bytes_amount}")
            print(f"Time: {stats.time}")
            print("\n")

class Stats:
    def __init__(self, stream_id: int, packets_amount: int, frames_amount: int, bytes_amount: int, time: float):
        self.stream_id = stream_id
        self.packets_amount = packets_amount
        self.frames_amount = frames_amount
        self.bytes_amount = bytes_amount
        self.time = time
    """
    This class represents the statistics for a stream.
    """

    def __init__(self, stream_id: int):
        self.stream_id = stream_id
        self.number_of_packets = 0
        self.number_of_frames = 0
        self.total_bytes = 0
        self.time = time.time()


class QUIC_PACKET:
    packet_id_counter = 0
    Max_size = 65535

    HEADER_LENGTH = struct.calcsize('!BIQ')
    FRAME_LENGTH = struct.calcsize('!IIQ')
    MAX_DATA_SIZE = Max_size - HEADER_LENGTH


    def __init__(self,flag):
        self.packet_ID = ++QUIC_PACKET.packet_id_counter
        self.packet_flag = flag
        self.packet_data = bytearray()

    @classmethod
    def deserialize_data(cls, data: bytes) -> Tuple['QUIC_PACKET', List['QUIC_FRAME']]:

        packet_header = struct.unpack('!BIQ',data[:cls.HEADER_LENGTH])
        flag, packet_id, data_size = packet_header
        packet = QUIC_PACKET(flag)
        packet.packet_ID = packet_id
        packet.packet_data = bytearray(data[cls.HEADER_LENGTH:])

        packet_frames = []
        frame_position_offset = 0
        while frame_position_offset < len(packet.packet_data):
            frame_header = struct.unpack('!IIQ', packet.packet_data[frame_position_offset:frame_position_offset+cls.FRAME_LENGTH])
            stream_id, position_in_stream, frame_size = frame_header
            frame_position_offset += cls.FRAME_LENGTH # skip to the next frame by frame length
            frame_data = packet.packet_data[frame_position_offset:frame_position_offset+frame_size]
            packet_frames.append(QUIC_FRAME(stream_id, position_in_stream, frame_data))
            frame_position_offset += frame_size

        return packet, packet_frames

    def serialize_data(self) -> bytes:
        packet_header = struct.pack('!BIQ', self.packet_flag, self.packet_ID, len(self.packet_data))
        return packet_header + self.packet_data



class QUIC_FRAME:

    def __init__(self, stream_id: int, position_in_stream: int, data: bytes):
        self.stream_id = 0
        self.position_in_stream = 0
        self.frame_data = data

    def __len__(self):
        return len(self.frame_data)