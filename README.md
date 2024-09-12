# QUIC Multi-Streams Project

This project implements the multi streams aspect of QUIC protocol in Python.
The project was made as part of Computer Networks course at Ariel University.
The assignment's guidelines can be found [here](project_guidelines.pdf), and the outcome of the project can be found [here](project_outcome.pdf).
## Table of Contents
- [Project Structure](#project-structure)
- [Project Details](#project-details)
  - [QUIC_CONNECTION class](#quic_connection-class)
  - [QUIC_PACKET and QUIC_FRAME classes](#quic_packet-and-quic_frame-classes)
- [Usage](#usage)
  - [Running the Receiver](#running-the-receiver)
  - [Running the Sender](#running-the-sender)
  - [Running the Tests](#running-the-tests)
- [Requirements](#requirements)
- [Installation](#installation)
- [Contributing](#contributing)

## Project Structure

- `QUIC.py`: Contains the main implementation of the QUIC protocol, including connection management, packet handling, and data transmission.
- `receiver.py`: Script to run the receiver that listens for incoming connections and receives data.
- `sender.py`: Script to run the sender that connects to the receiver and sends data.
- `QUIC_TEST.py`: Contains test cases to verify the functionality of the QUIC protocol implementation.

## Project Details

### QUIC_CONNECTION class

The `QUIC_CONNECTION` class is responsible for managing the connection between the sender and the receiver. It handles the following:
- Establishing connections (connect_to and listen_to methods)
- Sending data (send_data and send_to_streams methods)
- Receiving data (receive_data method)
- Terminating connections (terminate_connection and end_communication methods)

### QUIC_PACKET and QUIC_FRAME classes
- `QUIC_PACKET`: Represents a packet in the QUIC protocol, including serialization and deserialization methods.
- `QUIC_FRAME`: Represents a frame within a QUIC packet, including stream ID, position, and data.

## Usage

### Running the Receiver

To start the receiver, run the following command:
```sh
python receiver.py
```
The receiver will listen for incoming connections on 0.0.0.0:9191. 

### Running the Sender

```aiignore
python sender.py
```
The sender will connect to the receiver at 127.0.0.1:9191 and send the contents of random_data_file.txt over 3 streams.

### Running the Tests

To run the test , execute the following command:
```sh
python QUIC_TEST.py
```

It will run the test which simulates a connection between a sender and a receiver, sending data over multiple streams and verifying that the data received by the receiver, is the same as the data that was sent by the sender, making sure that the deserialization and serialization of the data conducted successfully.


## Requirements

- Python 3.7+
- `asyncio` module

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/benami171/QUIC_Multi_Streams.git
    cd QUIC_Multi_Streams
    ```

2. Ensure you have Python 3.7+ installed.

## Authors
- [Gal Ben Ami](https://github.com/benami171)
- [Elroei Carmel](https://github.com/ElroiCarmel)
- [Aharon Basous](https://github.com/Aharonba)
- [Gidi Rabi](https://github.com/GidiRabi)

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.
