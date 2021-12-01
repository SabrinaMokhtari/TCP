import socket
import threading
from struct import *
import time
import datetime
import random


class TCPThread(threading.Thread):
    def __init__(self, seq_num, strt, interval):
        super(TCPThread, self).__init__()
        self.seq_num = seq_num
        self.strt = strt
        self.interval = interval

    def run(self):
        # print("Thread", self.seq_num, "started", "current time is ", cal_current_time(), "and interval is "\
        # , self.interval)
        # print("before sleep", self.seq_num)
        global start_time
        time.sleep(self.interval)
        # print("after sleep", self.seq_num)
        t = cal_current_time()
        if not check_packet[self.seq_num]:
            if t - self.strt > self.interval:
                print("Packet", self.seq_num, "Has Been Dropped")
                start_time[self.seq_num] = cal_current_time()
                decrease_wnd_size()
                send_packets(self.seq_num)


def read_pic():
    with open("pic.png", "rb") as image:
        f = image.read()
        b = bytearray(f)
    return b


def decrease_wnd_size():
    global WND_SIZE
    global SSTHRESHOLD
    global r_wnd
    if WND_SIZE >= 2:
        SSTHRESHOLD = WND_SIZE // 2
        WND_SIZE = 1
        r_wnd = l_wnd
    # print("l", l_wnd, "r", r_wnd, "threshold", SSTHRESHOLD)


def increase_wnd_size():
    global WND_SIZE
    global l_wnd
    global r_wnd
    linear = False
    while check_packet[l_wnd]:
        l_wnd += 1
        if WND_SIZE < SSTHRESHOLD:  # grow exponentially
            if r_wnd + 2 < 45:  # r_wnd < 43
                WND_SIZE += 1
                r_wnd += 2
            elif r_wnd == 43:
                r_wnd += 1

        else:  # grow linear
            if r_wnd + 1 < 45:
                linear = True
                r_wnd += 1
    if linear:
        WND_SIZE += 1
    # print("l", l_wnd, "r", r_wnd)
    return


def cal_current_time():
    t = str(datetime.datetime.now()).split()[1].split(":")
    min_ = 0
    if t[1][0] == '0':
        min_ = int(t[1][1])
    else:
        min_ = int(t[1][0]) * 10 + int(t[1][1])
    sec = float(t[2])
    return min_ * 60 + sec


def drop_packet(seq_num):
    global ESTIMATED_RTT
    global DEV_RTT
    global start_time
    ESTIMATED_RTT = cal_est_rtt()
    DEV_RTT = cal_dev_rtt()
    interval = calc_time_interval()
    strt = cal_current_time()
    t = TCPThread(seq_num=seq_num, strt=strt, interval=interval)
    t.start()


def send_packets(seq_num):
    global ESTIMATED_RTT
    global DEV_RTT
    global start_time
    global CHECK_SUM

    l_p = 536 * seq_num
    r_p = min((l_p + 536), len(data))
    r = random.random()
    if r < c_prob and 0 < seq_num < 45:
        print("corrupting", seq_num)
        CHECK_SUM = corrupt_checksum(data[l_p: r_p])
    else:
        CHECK_SUM = calc_checksum(data[l_p: r_p])
    # print("CHECKSUM", CHECK_SUM)
    p = pack('!HHLLBBBH', SRC_PORT, DST_PORT, seq_num, ACK_NUM, ACK, SYN, FIN, CHECK_SUM) + pack('536s',
                                                                                                 data[l_p:r_p])
    sender_socket.sendto(p, address)
    # print(data[l_p:r_p])
    ESTIMATED_RTT = cal_est_rtt()
    DEV_RTT = cal_dev_rtt()
    interval = calc_time_interval()
    # print(ESTIMATED_RTT, DEV_RTT, interval, SAMPLE_RTT)
    strt = cal_current_time()
    if SYN == 0 and ACK == 0 and FIN == 0:
        t = TCPThread(seq_num=seq_num, strt=strt, interval=interval)
        t.start()
    return


def cal_est_rtt():
    return ((1 - ALPHA) * ESTIMATED_RTT) - (ALPHA * SAMPLE_RTT)


def cal_dev_rtt():
    return ((1 - BETA) * DEV_RTT) + (BETA * abs(SAMPLE_RTT - ESTIMATED_RTT))


def calc_time_interval():
    return ESTIMATED_RTT + (4 * SAMPLE_RTT)


def update_sample_rtt(index):
    global SAMPLE_RTT
    global start_time
    global end_time
    count = 0
    for i in range(len(start_time)):
        if end_time[i] != -1:
            count += 1
    return ((count - 1) * SAMPLE_RTT + (end_time[index] - start_time[index])) / count


def corrupt_checksum(p_data):
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
    s += 0b000000000000000001
    s_ = int(format(s, '#018b'), 2)
    return ~s_ & 0xffff


def calc_checksum(p_data):
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
    return ~s_ & 0xffff


data = read_pic()
num_of_packets = (len(data) // 536) + 1
print(data)

DST_IP = "127.0.0.1"
DST_PORT = 20001
SRC_PORT = 54682
SEQ_NUM = 0
ACK_NUM = 0
ACK = 0
SYN = 1
FIN = 0
CHECK_SUM = 0
BFR_SIZE = 1024
ZERO_DATA = bytearray([0 for i in range(536)])

check_packet = [False] * num_of_packets
start_time = [0] * num_of_packets
end_time = [-1] * num_of_packets

WND_SIZE = 1
SSTHRESHOLD = 8
l_wnd = 0
r_wnd = 0

DEV_RTT = 0
ESTIMATED_RTT = 1
ALPHA = 0.125
BETA = 0.25
SAMPLE_RTT = 0

packet_sent = 0
c_prob = 0.1
d_prob = 0.1
sent_FIN = False

sender_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
packet_bytes = pack('!HHLLBBBH', SRC_PORT, DST_PORT, SEQ_NUM, ACK_NUM, ACK, SYN, FIN, CHECK_SUM) + pack('536s',
                                                                                                        ZERO_DATA)
sender_socket.sendto(packet_bytes, (DST_IP, DST_PORT))

while True:

    packet_from_receiver = sender_socket.recvfrom(BFR_SIZE)
    message = packet_from_receiver[0]
    address = packet_from_receiver[1]

    msg = unpack('!HHLLBBBH', message)
    DST_PORT = address[1]
    SRC_PORT = msg[1]

    if msg[4] == 1 and msg[5] == 1:  # receiver sent syn and ack then sender should send ACK and then packet
        ACK = 1
        SYN = 0
        FIN = 0
        print("Connection Stablished")
        send_packets(SEQ_NUM)

        SYN = 0
        FIN = 0
        ACK = 0
        start_time[SEQ_NUM] = cal_current_time()
        send_packets(SEQ_NUM)
        packet_sent += 1
        SEQ_NUM += 1

    elif msg[4] == 0 and msg[5] == 0 and msg[6] == 1:  # receiver sent fin so sender should send ack and break
        ACK = 1
        FIN = 0
        SYN = 0
        print("Connection Closed")
        send_packets(SEQ_NUM)
        break

    elif msg[4] == 1 and msg[5] == 0 and msg[6] == 0:  # receiver sent ack
        if sent_FIN:    # receiver sent the ACK before FIN so receiver should wait for FIN
            continue
        print("Receiver sent ack", int(msg[3]))
        check_packet[int(msg[3])] = True
        end_time[int(msg[3])] = cal_current_time()
        SAMPLE_RTT = update_sample_rtt(int(msg[3]))
        finished = True

        for i in range(len(check_packet)):
            if not check_packet[i]:
                finished = False

        if finished:  # sender should send fin
            FIN = 1
            ACK = 0
            SYN = 0
            print("Sender Finished Sending Packets")
            sent_FIN = True
            send_packets(SEQ_NUM)

        elif packet_sent < num_of_packets:  # sender should send multiple packets
            increase_wnd_size()
            SYN = 0
            FIN = 0
            ACK = 0

            while SEQ_NUM <= r_wnd:
                r = random.random()
                if r < d_prob:
                    print("Dropping", SEQ_NUM)
                    start_time[SEQ_NUM] = cal_current_time()
                    drop_packet(SEQ_NUM)
                    packet_sent += 1
                    SEQ_NUM += 1
                else:
                    start_time[SEQ_NUM] = cal_current_time()
                    send_packets(SEQ_NUM)
                    packet_sent += 1
                    SEQ_NUM += 1
            # start_time[SEQ_NUM] = cal_current_time()
            # send_packets(SEQ_NUM)
            # packet_sent += 1
            # SEQ_NUM += 1

        else:
            pass
