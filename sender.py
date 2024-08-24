from QUIC import QUIC_CONNECTION, FLAGS

def main():
    sender = QUIC_CONNECTION()
    sender.connect_to('127.0.0.1', 8855)
    print("Connection established with receiver")

    # send data


if __name__ == "__main__":
    main()