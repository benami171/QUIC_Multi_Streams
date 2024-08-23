from QUIC import QUIC_CONNECTION, FLAGS

def main():
    sender = QUIC_CONNECTION()
    sender.connect('127.0.0.1', 8855)
    print("Connection established with receiver")

if __name__ == "__main__":
    main()