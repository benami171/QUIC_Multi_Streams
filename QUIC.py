import random
from socket import socket, AF_INET, SOCK_DGRAM
import math
import struct
import time
import asyncio
from enum import IntEnum
from random import randint
from typing import Dict, List, Tuple
from dataclasses import dataclass

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

    def listen_incoming_connections(self, host: str, port: int):
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

        connect_packet = QUIC_PACKET(FLAGS.SYN)  # create a SYN type packet
        self.sock.sendto(connect_packet.serialize_data(), (self.host_address, self.port))

        received_data, address = self.sock.recvfrom(QUIC_PACKET.Max_size)
        received_packet = QUIC_PACKET.deserialize_data(received_data)[0]

        if received_packet.packet_flag == FLAGS.SYN_ACK:
            print("Received SYN_ACK packet from server")
        else:
            raise Exception("Connection failed")

    async def send_data(self, list_of_files: List[bytes]) -> None:
        for i, file in enumerate(list_of_files):
            self.out_streams[i + 1] = file

        await self.send_to_streams()
        print("Data sent successfully")
        self.out_streams.clear()
        final_packet = QUIC_PACKET(FLAGS.FIN)
        self.sock.sendto(final_packet.serialize_data(), (self.host_address, self.port))

    async def send_to_streams(self) -> None:
        # generate random frame size
        frame_size = int(random.uniform(1000, 2000))
        # calculate the frame payload size (without the header)
        frame_payload_size = frame_size - QUIC_PACKET.FRAME_LENGTH
        # calculate the number of frames per packet
        frames_per_packet = math.ceil(QUIC_PACKET.Max_size / frame_size)
        await asyncio.gather(*(self.send_stream_data(stream_id, frame_payload_size, frames_per_packet) for stream_id in
                               self.out_streams))

    async def send_stream_data(self, stream_id: int, frame_payload_size: int, frames_per_packet: int) -> None:
        """
        1. get the data from each stream by stream_id
        2. generate random frame size and calculate number of frames needed.
        3. calculate frames per packet
        4. calculate number of packets needed.
        5. divide the data to frames and add the frames to the packet.
        6. send the frames on the stream.
        """
        data_from_stream = self.out_streams[stream_id]
        needed_frames_amount = math.ceil(len(data_from_stream) / frame_payload_size)
        needed_packets_amount = math.ceil(needed_frames_amount / frames_per_packet)

        for i in range(needed_packets_amount):
            #
            if i == 0:
                packet = QUIC_PACKET(FLAGS.FIRST_PACKET)
            elif i == needed_packets_amount - 1:
                packet = QUIC_PACKET(FLAGS.LAST_PACKET)
            else:
                packet = QUIC_PACKET(FLAGS.DATA_PACKET)
                for frame_offset in range(frames_per_packet):
                    if frame_offset == frames_per_packet - 1:
                        awaiting_data = data_from_stream[frame_offset * frame_payload_size:]
                        packet.link_frame(stream_id, frame_offset, awaiting_data)
                    else:
                        awaiting_data = data_from_stream[
                                        frame_offset * frame_payload_size:(frame_offset + 1) * frame_payload_size]
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
        received_packets_amount = 0
        received_bytes_amount = 0
        while True:
            received_data, address = self.sock.recvfrom(QUIC_PACKET.Max_size)
            received_packet, received_frames = QUIC_PACKET.deserialize_data(received_data)

            if received_packet.packet_flag != (FLAGS.SYN or
                                               FLAGS.ACK or
                                               FLAGS.SYN_ACK or
                                               FLAGS.FIN):

                frames_received_counter += len(received_frames)
                # GOT THE FIRST PACKET OF THE SPECIFIC STREAM, START MEASURING TIME
                if received_packet.packet_flag == FLAGS.FIRST_PACKET:
                    if received_frames[0].stream_id not in self.streams_stats:
                        self.streams_stats[received_frames[0].stream_id] = Stats(received_frames[0].stream_id, 0, 0, 0,
                                                                             time.time())
                    if OVERALL_DATA not in self.connection_stats:
                        self.connection_stats[OVERALL_DATA] = Stats(0, 0, 0, 0, time.time())

                if len(received_frames) > 0:
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
        for stream_id, stats in self.streams_stats.items():
            print(f"Stream ID: {stream_id}")
            print(f"Number of packets: {stats.packets_amount}")
            print(f"Number of frames: {stats.frames_amount}")
            print(f"Total bytes: {stats.total_bytes_amount}")
            print(f"Time: {stats.time}")
            print("\n")



    # will be used when we get FIN packet.
    def terminate_connection(self) -> None:
        if self.is_closed:
            return
        else:
            print(f"Got FIN packet, terminating connection")
            self.sock.close()
            self.is_closed = True


    # send FIN packet to the other side.
    def end_communication(self):
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
    Max_size = 65535
    HEADER_LENGTH = struct.calcsize('!BIQ')
    FRAME_LENGTH = struct.calcsize('!IIQ')
    MAX_DATA_SIZE = Max_size - HEADER_LENGTH

    def __init__(self, flag):
        QUIC_PACKET.packet_id_counter += 1
        self.packet_ID = QUIC_PACKET.packet_id_counter
        self.packet_flag = flag
        self.packet_data = bytearray()  # using bytearray because it is mutable and can be modified

    @classmethod
    def deserialize_data(cls, data: bytes) -> Tuple['QUIC_PACKET', List['QUIC_FRAME']]:

        packet_header = struct.unpack('!BIQ', data[:cls.HEADER_LENGTH])
        flag, packet_id, data_size = packet_header
        packet = QUIC_PACKET(flag)
        packet.packet_ID = packet_id
        packet.packet_data = bytearray(data[cls.HEADER_LENGTH:])

        packet_frames = []
        frame_position_offset = 0
        while frame_position_offset < len(packet.packet_data):
            frame_header = struct.unpack('!IIQ', packet.packet_data[
                                                 frame_position_offset:frame_position_offset + cls.FRAME_LENGTH])
            stream_id, position_in_stream, frame_size = frame_header
            frame_position_offset += cls.FRAME_LENGTH  # skip to the next frame by frame length
            frame_data = packet.packet_data[frame_position_offset:frame_position_offset + frame_size]
            packet_frames.append(QUIC_FRAME(stream_id, position_in_stream, frame_data))
            frame_position_offset += frame_size

        return packet, packet_frames

    def serialize_data(self) -> bytes:
        packet_header = struct.pack('!BIQ', self.packet_flag, self.packet_ID, len(self.packet_data))
        return packet_header + self.packet_data

    def link_frame(self, stream_id: int, position_in_stream: int, data: bytes) -> None:
        frame_to_link = struct.pack('!IIQ', stream_id, position_in_stream, len(data))
        if len(self.packet_data) + len(frame_to_link) > QUIC_PACKET.MAX_DATA_SIZE:
            raise Exception("Frame size is too large")
        self.packet_data += frame_to_link


class QUIC_FRAME:

    def __init__(self, stream_id: int, position_in_stream: int, data: bytes):
        self.stream_id = 0
        self.position_in_stream = 0
        self.frame_data = data

    def __len__(self):
        return len(self.frame_data)
