#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/5/23 18:11
# @Version : 1.0
# @File    : mindwave_parser.py
# @Author  : Jingsheng Tang
# @Version : 1.0
# @Contact : mrtang@nudt.edu.cn   mrtang_cs@163.com
# @License : (C) All Rights Reserved

import numpy as np

# Byte codes
CONNECT              = '\xc0'
DISCONNECT           = '\xc1'
AUTOCONNECT          = '\xc2'
SYNC                 = '\xaa'
EXCODE               = '\x55'
POOR_SIGNAL          = '\x02'
ATTENTION            = '\x04'
MEDITATION           = '\x05'
BLINK                = '\x16'
HEADSET_CONNECTED    = '\xd0'
HEADSET_NOT_FOUND    = '\xd1'
HEADSET_DISCONNECTED = '\xd2'
REQUEST_DENIED       = '\xd3'
STANDBY_SCAN         = '\xd4'
RAW_VALUE            = '\x80'

class eegData:
    def __init__(self):
        self.poor_signal = []
        self.attention = []
        self.meditation = []
        self.blink = []
        self.raw_value = []
        self.rhythm = []
        self.raw_ay = np.zeros(1)

class mindWaveParser():
    def __init__(self):
        self.buf = ''
        self.status = 'DISCONECTED'
        self.id = 0

    def parser(self,buf):
        self.eeg = eegData()
        self.buf += buf

        while len(self.buf)>0:
            try:
                indx = self.buf.index('\xaa\xaa')    #定位到包头
                if indx != 0:
                    print 'warning'
                # self.buf = self.buf[indx + 2:]
                indx += 1
                indx += 1
            except:
                print 'wrong'
                return None  #一个数据包都没有搜索到,这个包也不再有含义

            try:
                while True:
                    if self.buf[indx] == '\xaa':    #以\xaa\xaa为结尾的位置定位包头
                        print 'warning'
                    else:
                        break
                    indx += 1

                plength = ord(self.buf[indx])
                payload = self.buf[indx + 1: indx + 1 + plength]
                chksum = ord(self.buf[indx + 1 + plength])
            except:                                 #不完整的包
                break

            self.buf = self.buf[indx + 2 + plength:]

            # Verify its checksum
            val = sum(ord(b) for b in payload)
            val &= 0xff
            val = ~val & 0xff

            if val == chksum:
                self.parse_payload(payload)
            else:
                print 'bad package'

        self.eeg.raw_ay = np.array(self.eeg.raw_value)
        return self.eeg

    def parse_payload(self, payload):
        """Parse the payload to determine an action."""

        while payload:
            # Parse data row
            excode = 0
            try:
                code, payload = payload[0], payload[1:]
            except IndexError:
                pass
            while code == EXCODE:
                # Count excode bytes
                excode += 1
                try:
                    code, payload = payload[0], payload[1:]
                except IndexError:
                    pass
            if ord(code) < 0x80:
                # This is a single-byte code
                try:
                    value, payload = payload[0], payload[1:]
                except IndexError:
                    pass
                if code == POOR_SIGNAL:
                    self.eeg.poor_signal.append(ord(value))
                elif code == ATTENTION:
                    # Attention level
                    self.eeg.attention.append(ord(value))
                elif code == MEDITATION:
                    # Meditation level
                    self.eeg.meditation.append(ord(value))
                elif code == BLINK:
                    # Blink strength
                    self.eeg.blink.append(ord(value))
            else:
                # This is a multi-byte code
                try:
                    vlength, payload = ord(payload[0]), payload[1:]
                except IndexError:
                    continue
                value, payload = payload[:vlength], payload[vlength:]
                if code == RAW_VALUE:
                    raw=ord(value[0])*256+ord(value[1])
                    if (raw>=32768):
                        raw=raw-65536
                    raw *= 1e6 * 1.8/(4096.*2000)
                    self.eeg.raw_value.append(raw)
                if code == HEADSET_CONNECTED:
                    self.status = 'CONNECTED'
                    self.id = value.encode('hex')
                elif code == HEADSET_NOT_FOUND:
                    self.status = 'NOTFOUND'
                elif code == HEADSET_DISCONNECTED:
                    self.status = 'DISCONNECTED'
                elif code == REQUEST_DENIED:
                    self.status = 'REQUEST_DENIED'
                elif code == STANDBY_SCAN:
                    self.status = 'STANDBY_SCAN'

if __name__ == '__main__':
    # with open(r'd:\buf.txt','r') as f:
    #     buf = f.read()

    import serial
    import time
    from matplotlib import pyplot as plt

    s = serial.Serial('com3',57600)
    p = mindWaveParser()
    eeg = []
    time.sleep(2)
    plt.ion()
    while True:
        buf = s.read(12800)
        eg = p.parser(buf)
        if eg is not None:
            eeg = np.hstack((eeg,eg.raw_ay))
        plt.plot(eeg[:-512])
        eeg = eeg[:-1000]
        plt.show()
