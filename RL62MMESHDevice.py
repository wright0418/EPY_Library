'''
Group ID -- Type
C001 -- LIGHT
C002 -- PLUGA
C003 -- SWITCH
C005 -- EPY
C007 -- FAN

version 1.0.1
1. fixed epy mesh send/recv bug
version 1.0.2
1. add mesh recv action callback
'''
from utime import sleep_ms, ticks_ms, ticks_diff
import ubinascii as binascii
import gc

class MeshDevice:

    def __init__(self, uart):

        self.ble = uart
        self.got_flag = False
        self.got_msg = ''
        self.mac_addr = self.MyMac_Addr()
        self.recv_action_callback = []
        self.airBoxData = [0,0,0,0]

    def __del__(self):
        self.ble.deinit()

    def uart_recv(self):
        timeout = 50
        pre_ticks = ticks_ms()
        while True:
            if self.ble.any():
                try:
                    msg = str(self.ble.readline(), 'utf-8').strip().split(' ')
                    type = msg[0]
                    other = msg[1:]
                    # print(type, other)
                    if 'MDTS-MSG' in type or 'MDTGP-MSG' in type:
                        if len(msg) > 2:
                            self.got_flag = True
                            self.got_msg = (msg[1], msg[3])
                            return None, None
                    return type, other
                except:
                    return None, None

            elif ticks_diff(ticks_ms(), pre_ticks) > timeout:
                return None, None
            if gc.mem_free() <1000:
                gc.collect()
            sleep_ms(10)

    def WriteCMD_withResp(self, atcmd_):
        _ = self.ble.write(atcmd_+'\r\n')
        type, msg = self.uart_recv()
        # print(atcmd_)
        return type, msg

    def Re_try_WriteCMD(self, atcmd):
        times = 10
        while times > 0:
            type, m = self.WriteCMD_withResp(atcmd)
            # print('===', type, m)
            try:
                if type:
                    if m[0] == "ERROR":
                        times -= 1
                        sleep_ms(1000)
                        continue
                    else:
                        return m[0]  # SUCCESS
            except:
                times -= 1
                sleep_ms(1000)
                continue

    def NodeReset(self):
        self.WriteCMD_withResp('AT+NR')

    def MyMac_Addr(self):
        _, msg = self.WriteCMD_withResp('AT+ADDR')
        # print(msg)
        return msg[0][-4:]

    def SendData_Light(self, dst, C=0, W=0, R=0, G=0, B=0):
        msg = self.Re_try_WriteCMD(
            'AT+MDTS 0 0x87F000{}{}070100{:02X}{:02X}{:02X}{:02X}{:02X}'.format(self.mac_addr, dst, C, W, R, G, B))

    def SendData_Switch(self, dst, on_off):
        msg = self.Re_try_WriteCMD(
            'AT+MDTS 0 0x87F000{}{}030200{:02X}'.format(self.mac_addr, dst, on_off))

    def SendData_Fan(self, dst, speed=None, OnOff=None, timer=None, swing=None, mode=None):
        """
        使用查表法去建立傳送的資料與限制
        """
        commands = {
            'speed': (speed, 24, '04040007'),
            'timer': (timer, 8, '04040006'),
            'swing': (swing, None, '04040005'),
            'mode': (mode, None, '04040005'),
            'OnOff': (OnOff, None, '04040001')
        }
        for key, value in commands.items():
            if value[0] is not None:
                if value[1] is not None:
                    if value[0] > value[1]:
                        continue
                msg = self.Re_try_WriteCMD(
                    'AT+MDTS 0 0x87F000{}{}{}{:02X}'.format(self.mac_addr, dst, value[2], value[0]))

    def SendData_EPY(self, dst,send_msg):
        send_msg = binascii.unhexlify(self.mac_addr) + send_msg[:14]
        length = len(send_msg)
        send_data = str(binascii.hexlify(send_msg), 'utf-8')
        msg = self.Re_try_WriteCMD(
            'AT+MDTS 0 0x87F000{}{}{:02X}FF00{}'.format(self.mac_addr, dst, length, send_data))
        return (msg)

    def ReadMeshMsg(self,filter_source=None):
        self.uart_recv()
        if self.got_flag:
            self.got_flag = False
            source = self.got_msg[1][2:6]
            if filter_source is not None:
                if source != filter_source:
                    return None
                else:
                    char_data = str(binascii.unhexlify(self.got_msg[1][8:]), 'utf-8')
                    return char_data
            else:
                char_data = str(binascii.unhexlify(self.got_msg[1][8:]), 'utf-8')
                return source,char_data
        else:
            return None

    def set_mesh_recv_action(self, from_mac ,msg_key,action_cb):
        self.recv_action_callback.append((from_mac,msg_key,action_cb))
    
    def process_recv_action(self):
        recv_msg = self.ReadMeshMsg()
        if recv_msg is not None:
            for recv_action_item in self.recv_action_callback:
                if recv_msg[0] == recv_action_item[0] and recv_msg[1] == recv_action_item[1]:
                    recv_action_item[2]()
                    break

    def ReadAirBox(self,index =0):
        self.uart_recv()
        if self.got_flag:
            self.got_flag = False
            #87 source_addr(F000) length(0A) data(xxxxxx)
            try:
                source = self.got_msg[1][2:6]
                type = self.got_msg[1][8:10]
                if source == "F000":
                    # print (self.got_msg[1][10:])
                    char_data = float(str(binascii.unhexlify(self.got_msg[1][10:]), 'utf-8'))
                    if type == "01":
                        self.airBoxData[0] = char_data
                    elif type == "02":
                        self.airBoxData[1] = char_data
                    elif type == "03":
                        self.airBoxData[2] = char_data
                    elif type == "04":
                        self.airBoxData[3] = char_data
            except:
                pass
            return self.airBoxData[index]
                

if __name__ == '__main__':
    from machine import UART
    import gc
    try:
        uart = UART(0, 115200, timeout=20)
    except:
        uart.deinit()
        uart = UART(0, 115200, timeout=20)
    MD = MeshDevice(uart)

    while True:
        data = MD.ReadAirBox(1)
        print(data)


    def recv_action_ON():
        print('recv action_ON')
    def recv_action_OFF():
        print('recv action_OFF')


    while True:
        PM = MD.ReadAirBox(0)
        Temperature = MD.ReadAirBox(1)
        Humidity = MD.ReadAirBox(2)
        CO2 = MD.ReadAirBox(3)
        print(PM,Temperature,Humidity,CO2)
        sleep_ms(100)

    # MD.set_mesh_recv_action('0726','ON',recv_action_ON)
    # MD.set_mesh_recv_action('0726','OFF',recv_action_OFF)
    # while True:
    #     MD.process_recv_action()
    #     sleep_ms(1)


    # # MD.SendData_Light(mac_addr/group , C,W,R,G,B)
    # MD.SendData_Light('11CF', 0, 0, 0, 255, 0)
    # MD.SendData_Light('C001', 0, 0, 255, 255, 0)
    # # MD.SendData_Switch('C002', 1)  # Off
    # # MD.SendData_Fan('C007', OnOff=1, swing=1, speed=3, timer=2)
    # MD.SendData_EPY('C005', "I am ePy01")

''' ---   Send sample code'''
    # while True:
    #     for i in range(0, 256, 32):
    #         MD.SendData_Light('C001', 0, 0, 0, i, 0)
    #         MD.SendData_Light('C001', 0, 0, 0, i, 0)
    #         sleep_ms(500)
    #     for i in range(0, 256, 32):
    #         MD.SendData_Light('C001', 0, 0, i, 0, 0)
    #         sleep_ms(500)
    #     for i in range(0, 256, 32):
    #         MD.SendData_Light('C001', 0, 0, 0, 0, i)
    #         sleep_ms(500)
    #     for i in range(0, 256, 32):
    #         MD.SendData_Light('C001', 0, 0, i, 0, i)
    #         sleep_ms(500)
'''---- recv sample code----'''
    # while True:
    #     msg = MD.ReadMeshMsg(filter_source='0726')
    #     msg = MD.ReadMeshMsg()
    #     if msg:
    #         if len(msg) == 2:
    #           print('{} say {}'.format(msg[0],msg[1]))
    #         else:
    #           print(msg)
    #     sleep_ms(1)

