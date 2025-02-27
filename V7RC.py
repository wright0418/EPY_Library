from machine import UART
from utime import sleep_ms
import gc
import _thread

class V7RC():
    def __init__(self, uart, debug=False):
        self.uart = uart
        self.debug = debug
        self.rx_buffer = bytearray(19)
        self.rx_buffer_view = memoryview(self.rx_buffer)
        self.rx = bytearray(1)
        self.recv_data = None
        self.SRT_cb = None
        self.LED_cb = None
        self.LE2_cb = None
        self.SRV_cb = None
        self.SS8_cb = None
        _thread.start_new_thread(self.recv_thread, ())

    def recv_thread(self,rate = 10):
        while True:
            self.rx = self.uart.read(1)
            if self.rx == b'#':
                while self.uart.any() < 19:
                    pass
                self.rx = self.uart.readinto(self.rx_buffer,19)
                self.paser(self.rx_buffer_view)
                if self.debug:
                    print('recv_data=>', self.rx_buffer)
                if gc.mem_free() <1000 :
                    gc.collect()
                    sleep_ms(1000//rate)

    def paser(self, data):
        try:
            if data[0:3] == b'SRT' and self.SRT_cb:
                self.SRT_cb((int(bytes(data[3:7]))-1500)//5, (int(bytes(data[7:11]))-1500)//5,
                            (int(bytes(data[11:15]))-1500)//5, (int(bytes(data[15:19]))-1500)//5)
            elif data[0:3] == b'LED' and self.LED_cb:
                self.LED_cb(data[3:19])
            elif data[0:3] == b'LE2' and self.LE2_cb:
                self.LE2_cb(data[3:19])
            elif data[0:3] == b'SRV' and self.SRV_cb:
                self.SRV_cb((int(bytes(data[3:7]))-1500)//5,
                            (int(bytes(data[7:11]))-1500)//5)
            elif data[0:3] == b'SS8' and self.SS8_cb:
                self.SS8_cb((int(bytes(data[3:5]), 16)-150)*2,
                            (int(bytes(data[5:7]), 16)-150)*2,
                            (int(bytes(data[7:9]), 16)-150)*2,
                            (int(bytes(data[9:11]), 16)-150)*2,
                            (int(bytes(data[11:13]), 16)-150)*2,
                            (int(bytes(data[13:15]), 16)-150)*2,
                            (int(bytes(data[15:17]), 16)-150)*2,
                            (int(bytes(data[17:19]), 16)-150)*2)
        except Exception as e:
            if self.debug:
                print(e)
            pass

    def set_callback(self, cmd, callback):
        if cmd == 'SRV':
            self.SRV_cb = callback
        elif cmd == 'SRT':
            self.SRT_cb = callback
        elif cmd == 'SS8':
            self.SS8_cb = callback

    def set_use_random(self, use_random):
        self.use_random = use_random

# 初始化 UART
uart = UART(1, 115200, timeout=20, read_buf_len=40)
v7rc = V7RC(uart, debug=True)

# 設置回調函數
def SRV_callback(M1, M2):
    print('SRV Callback: M1={M1}, M2={M2}'.format(M1=M1, M2=M2))

v7rc.set_callback('SRV', SRV_callback)

while True:
    sleep_ms(500)
    pass
