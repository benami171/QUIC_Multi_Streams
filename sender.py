from QUIC import QUIC_CONNECTION, FLAGS
import asyncio

async def start_sender():
    quic_conn = QUIC_CONNECTION()
    quic_conn.connect_to('127.0.0.1', 8855)
    print("Connection established with receiver")
    await asyncio.sleep(0.001)

    num_of_streams = int(input("Enter the desired number of streams: "))

    with open("random_data.txt", "r") as file:
        file_data = file.read().encode()
        await quic_conn.send_data([file_data]*num_of_streams)
        print("Data sent")
        quic_conn.end_communication()



if __name__ == "__main__":
    asyncio.run(start_sender())