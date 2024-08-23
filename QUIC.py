import socket
import struct
import time
import asyncio
from enum import IntEnum
from typing import Dict, List, Tuple
from dataclasses import dataclass


class FLAGS(IntEnum):
    SYN = 1
    SYN_ACK = 2
    ACK = 3
    DATA_PACKET = 4
    END = 5
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
            print("Received SYN packet from client in address: {address}")
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

class Stream_Statistics:
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

        received_data = struct.unpack('!BIQ',data[:cls.HEADER_LENGTH])
        flag, packet_id, data_size = received_data

        return

    def serialize_data(self) -> bytes:

        pass



class QUIC_FRAME:

    def __init__(self, stream_id: int, position_in_stream: int):
        self.stream_id = 0
        self.position_in_stream = 0