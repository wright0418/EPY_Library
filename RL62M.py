"""
RL62M is UART AT command module ,baudrate = 115200
It can be set to PERIPHERAL(Server / Device ) mode.
also , It can be set to CENTRAL mode( Client / Master ) mode
How to use the Library
from machine import *
import RL62M
uart = UART(1,115200,timeout=200,read_buf_len=512)
BLE = RL62M.GATT(uart,role='PERIPHERAL') or 'CENTRAL'
PERIPHERAL/CENTRAL Mode --
    msg = BLE.RecvData() : recv data and check connect/disconnect status , msg is string type(UTF-8)
    BLE.SendData('ABC')
CENTRAL Mode --
    BLE.ScanConnect() # scan and select the most near device (scan 5sec)
    # don't need scan , use device mac address connect
    BLE.ScanConnect(mac='7002000008B6')
V1.000 = first release version
V1.001
    - fixed mac connect change data mode
V1.002
    - fixed data receve return issues
    - fixed change ROLE check message error
V1.004 (2021.9.27)
    - use utime for delay
    - tested by Raspberry Pi Pico uart0
V1.100 (2022.1.1)
    - 更改廣播接收 資料格式 for Richlink RPi Gateway ，max group 20 , data is 8bit ASCII code  

V1.110 (2022.11.2)
    - 更改廣播傳送 資料格式 for Richlink RPi Gateway ，max group 20 , data is 8bit ASCII code  

"""
from utime import sleep_ms as delay
import utime

class GATT:

    def __init__(self, uart, role='PERIPHERAL'):
        self.ROLE = ''
        self.MODE = ''
        self.mac = ''
        self.state = 'DISCONNECTED'
        self.Adv_Interval_ms = 200
        self.AdvState = 0
        self.AdvScanState = 0
        self.AdvData = []
        self.AdvDataHeader = '1709726C'  # 2022.1102 modify for epy adv mode
        self.ScanFilterName = ''
        self.ble = uart
        self._init_RL62M()
        self.ChangeRole(role)
        self.ble.deinit()
        self.ble.init(115200, timeout=20, read_buf_len=128)

    def __del__(self):
        self.ble.deinit()

    ''' init RL62M to Command mode and enable sysmsg'''

    def _init_RL62M(self):
        delay(500)
        msg = ''
        while "OK" not in msg:
            self.ble.write('!CCMD@')
            delay(200)
            self.ble.write('AT\r\n')
            delay(50)
            msg = self.ble.read(self.ble.any())
            if msg == None:
                msg = ''
        self.MODE = 'CMD'
        msg = str(self.WriteCMD_withResp('AT+ADDR=?'), 'utf-8')
        #print (msg)
        self.mac = msg.strip().split(' ')[1]

        msg = self.WriteCMD_withResp('AT+EN_SYSMSG=?')
        if "EN_SYSMSG 0" in msg:
            msg = self.WriteCMD_withResp('AT+EN_SYSMSG=1')

        msg = self.ble.read(self.ble.any())   # Clear all UART Buffer

    def writeCMD_respons(self, atcmd, datamode=True):
        if self.MODE == 'DATA':
            self.ChangeMode('CMD')
        self.ble.write(atcmd+'\r\n')
        delay(50)
        msg = self.ble.read(self.ble.any())
        if msg == None:
            msg = ''
        if 'SYS-MSG: CONNECTED OK' in msg:
            self.state = 'CONNECTED'
        elif 'SYS-MSG: DISCONNECTED OK' in msg:
            self.state = 'DISCONNECTED'
        if datamode == True:
            self.ChangeMode('DATA')
        return (msg)

    def WriteCMD_withResp(self, atcmd, timeout=50):
        self.ChangeMode('CMD')
        self.ble.write('{0}\r\n'.format(atcmd))
        start = utime.ticks_ms()
        resp = b""
        while utime.ticks_diff(utime.ticks_ms(), start) < timeout:
            n = self.ble.any()
            if n:
                resp += self.ble.read(n)
            delay(10)
        return resp

    def ChangeMode(self, mode):
        if mode == self.MODE:
            return
        elif mode == 'CMD':
            delay(150)
            self.ble.write('!CCMD@')
            delay(200)
            msg = self.ble.readline() or ''
            while 'SYS-MSG: CMD_MODE OK' not in msg:
                msg = self.ble.readline() or ''
                delay(50)
            self.MODE = 'CMD'
        elif mode == 'DATA':
            msg = self.WriteCMD_withResp('AT+MODE_DATA')
            while 'SYS-MSG: DATA_MODE OK' not in msg:
                delay(100)
            self.MODE = 'DATA'
        else:
            pass

    def SendData(self, data):
        self.ChangeMode('DATA')
        self.ble.write(data+'\r\n')
        return

    def RecvData(self):
        msg = self.ble.readline()
        if msg :
            if 'SYS-MSG: CONNECTED OK' in msg:
                self.state = 'CONNECTED'
                return ''
            elif 'SYS-MSG: DISCONNECTED OK' in msg:
                self.state = 'DISCONNECTED'
                return ''
            elif len(msg)==1:
                ord_ = ord(msg)
                if  32 <= ord_ <=  126 :
                    return (str(msg, 'utf-8').strip())
                else:
                    return None
            else:
                return (str(msg, 'utf-8').replace('x\00','').strip())
        else:
            return None

    def ChangeRole(self, role):
        if self.ROLE == '':
            msg = self.WriteCMD_withResp('AT+ROLE=?')

            if 'PERIPHERAL' in msg:
                self.ROLE = 'PERIPHERAL'
            elif 'CENTRAL' in msg:
                self.ROLE = 'CENTRAL'

        if role == self.ROLE:
            return
        else:

            if role == 'PERIPHERAL':
                # 1.5sec for epy ble v1.03
                msg = self.WriteCMD_withResp('AT+ROLE=P', timeout=1500)

            else:
                msg = self.WriteCMD_withResp(
                    'AT+ROLE=C', timeout=1500)  # 1.5sec for epy ble v1.03
            if 'READY OK' not in msg:
                # print('Change Role fail ;', msg)
                pass

            self.ROLE = role
            self.ChangeMode('DATA')
            return

    def ScanConnect(self, mac='', name_header='EPY_', filter_rssi=60):
        device = []
        if self.ROLE != 'CENTRAL':
            self.ChangeRole("CENTRAL")
        if mac == '':
            msg = str(self.WriteCMD_withResp(
                'AT+SCAN_FILTER_RSSI={}'.format(filter_rssi)), 'utf-8')
            msg = str(self.WriteCMD_withResp(
                'AT+SCAN_FILTER_NAME={}'.format(name_header)), 'utf-8')
            # print(msg)
            while len(device) == 0:
                msg = str(self.WriteCMD_withResp(
                    'AT+SCAN', timeout=5000), 'utf-8')
                msg = msg.split('\r\n')
                for dev in msg:
                    sdev = dev.split(' ')
                    if len(sdev) == 5:
                        device.append(sdev)
            sorted(device, key=lambda x: int(x[3]), reverse=False)
            # print(device)
            msg = self.WriteCMD_withResp(
                'AT+CONN={}'.format(device[0][0]))
        else:
            msg = self.WriteCMD_withResp(
                'AT+CONN={}'.format(mac))

        for i in range(10):
            msg = self.RecvData()
            if self.state == 'CONNECTED':
                self.ChangeMode('DATA')
                break
            delay(200)
        return

    def disconnect(self):
        msg = self.WriteCMD_withResp('AT+DISC')
        #print ('disconn',msg)
        for i in range(10):
            msg = self.RecvData()
            if self.state == 'DISCONNECTED':
                break
            delay(100)
        return

    def SetAdvInterval_ms(self, time_ms=50):
        # 50/100/200/500/1000/2000/5000/10000/20000/50000
        self.EnableAdvMode(enable=0)

        if time_ms != self.Adv_Interval_ms and self.ROLE == 'PERIPHERAL':
            msg = self.WriteCMD_withResp('AT+ADV_INTERVAL={}'.format(time_ms))
            if "OK" in msg:
                self.Adv_Interval_ms = time_ms
        self.EnableAdvMode(enable=1)
        return

    def EnableAdvMode(self, enable=1):  # enable 廣播功能

        if self.ROLE == 'PERIPHERAL':
            msg = self.WriteCMD_withResp('AT+ADVERT={}'.format(enable))
            if "OK" in msg:
                self.AdvState = enable
        return

    def SetAdvData(self):
        data = self.AdvDataHeader+''.join(self.AdvData)
        # print(data)
        msg = self.WriteCMD_withResp(
            'AT+AD_SET=0,{}'.format(data))
        return

    def EnableAdvScan(self, enable=1):  # 開啟廣播接收
        if self.AdvScanState != enable and self.ROLE == 'CENTRAL':
            msg = self.WriteCMD_withResp(
                'AT+ADV_DATA_SCAN={}'.format(enable))
            if "OK" in msg:
                self.AdvScanState = enable

    def AdvSendData(self, group=1, data='0'):
        # need modify to new format
        if self.AdvData == []:
            self.AdvData = ['0']*40
        if self.ROLE != 'PERIPHERAL':
            self.ChangeRole("PERIPHERAL")
        if group >= 1 and group <= 20:
            self.AdvData[(group-1)*2] = hex(ord(data))[2]
            self.AdvData[(group-1)*2+1] = hex(ord(data))[3]
        self.EnableAdvMode(enable=0)
        self.SetAdvData()
        self.EnableAdvMode(enable=1)

    def SetScanFilterName(self, name='rl'):
        if self.ScanFilterName != name:
            msg = self.WriteCMD_withResp('AT+SCAN_FILTER_NAME={0}'.format(name))
            if "OK" in msg:
                self.ScanFilterName = name

    def AdvRecvData(self, group=0, who_mac='None'):
        if who_mac == 'None':
            return 'Error'
        str_data = ''
        if self.ROLE != 'CENTRAL':
            self.ChangeRole("CENTRAL")
        self.EnableAdvScan(enable=1)
        self.SetScanFilterName()  # 更新呼叫的函式名稱
        msg = self.ble.readline()
        msg = str(msg, 'utf-8').strip() if msg else ''
        if not msg:
            return None
        parts = msg.split(' ')
        if len(parts) < 4:
            return None
        if 'ADV_DATA' in parts[0] and who_mac in parts[1]:
            data_piece = parts[3][8:48]
        else:
            return None
        group = int(group)
        if group < 1 or group > 20:
            # 處理全部group，簡化印出處理
            str_data = []
            for i in range(20):
                group_piece = data_piece[i*2:i*2+2]
                try:
                    str_data.append(chr(int(group_piece, 16)))
                except Exception:
                    str_data.append('.')
            return 'Error'
        else:
            group_piece = data_piece[(group-1)*2:(group-1)*2+2]
            try:
                return chr(int(group_piece, 16))
            except Exception:
                return '~'
