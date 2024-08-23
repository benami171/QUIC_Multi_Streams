from QUIC import QUIC_CONNECTION

def main():
    connection = QUIC_CONNECTION()
    connection.listen_incoming_connections('127.0.0.1', 8855)


if __name__ == "__main__":
    main()