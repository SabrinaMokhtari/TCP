import socket
import time
from struct import *

SRC_IP = "127.0.0.1"
SRC_PORT = 20001
DST_PORT = 54682
SEQ_NUM = 0
ACK_NUM = 0
ACK = 0
SYN = 1
FIN = 0
CHECK_SUM = 0
BFR_SIZE = 1024
PACK_SIZE = 45
IMG = bytearray(23770)
achieved_syn = True


def send_packet():
    p = pack('!HHLLBBBH', SRC_PORT, DST_PORT, SEQ_NUM, ACK_NUM, ACK, SYN, FIN, CHECK_SUM)
    receiver_socket.sendto(p, address)
    return


def calc_checksum(p_data, checksum):
    a = 0
    b = 0
    s = 0
    for i in range(0, len(p_data), 2):
        a = format(p_data[i], '#019b')
        if i + 1 < len(p_data):
            b = format(p_data[i + 1], '#019b')
        else:
            b = format(0, '#019b')
        d = int(a, 2) + int(b, 2)
        if d & 0b100000000000000000 == 0b100000000000000000:  # wrap around
            d += 0b000000000000000001
        s += d
    s_ = int(format(s, '#018b'), 2)
    # print(checksum, ~s_ & 0xffff)
    if checksum == (~s_ & 0xffff):
        return True
    return False


def write_back_pic():
    image = open("new_pic.png", "wb")
    image.write(IMG)
    image.close()
    return


receiver_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
receiver_socket.bind((SRC_IP, SRC_PORT))
print("Receiver is Listening")


def receive_img(msg):
    global IMG
    l = msg[2] * 536
    r = min(l + 536, len(IMG))
    IMG[l:r] = msg[8][:r - l]
    return


while True:
    packet_from_sender = receiver_socket.recvfrom(BFR_SIZE)
    message = packet_from_sender[0]
    address = packet_from_sender[1]

    msg = unpack('!HHLLBBBH536s', message)
    DST_PORT = address[1]
    SRC_PORT = msg[1]
    ACK_NUM = msg[2]

    if msg[4] == 0 and msg[5] == 1 and msg[6] == 0:  # sender wants to start communication
        ACK = 1
        SYN = 1
        FIN = 0
        print("Receiver IS Sending ACK and SYN")
        send_packet()

    elif msg[4] == 0 and msg[5] == 0 and msg[6] == 1:  # sender is done
        ACK = 1
        FIN = 0
        SYN = 0
        print("Receiver IS Sending ACK then FIN ")
        send_packet()
        ACK = 0
        FIN = 1
        SYN = 0
        send_packet()

    elif msg[4] == 1 and msg[5] == 0 and msg[6] == 0:
        if achieved_syn:  # Communication started
            achieved_syn = False
            continue
        else:  # CLOSE
            print("Connection Closed")
            print(len(IMG), IMG)
            write_back_pic()
            break

    elif msg[6] == 0 and msg[5] == 0 and msg[4] == 0:  # server sent img
        # print(msg[8])
        if calc_checksum(msg[8], msg[7]):
            receive_img(msg)
            ACK = 1
            SYN = 0
            FIN = 0
            print("Client Sent IMG")
            send_packet()
            print("Packet ", int(msg[2]), " Acked")
        else:
            print("Packet", msg[2], "Has Corrupted")
