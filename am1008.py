#  micropython -- AM1008 Module
import ustruct as struct
from machine import UART
import gc
class AM1008:
    read_cmd = [0x11, 0x02, 0x01, 0x01, 0xEB]
    def __init__(self, uart, timeout=1000):
        self.uart = UART(uart, 9600, timeout=timeout)
        self.co2 = None
        self.voc = None
        self.humidity = None
        self.temperature = None
        self.PM1p0_grimm = None
        self.PM2p5_grimm = None
        self.PM10_grimm = None
        self.PM1p0_tsi = None
        self.PM2p5_tsi = None
        self.PM10_tsi = None
    
    def _read(self):
        gc.collect()
        self.uart.read(self.uart.any())
        self.uart.write(bytearray(self.read_cmd))
        data = self.uart.read(25)
        try:
            self.co2 = struct.unpack('>H', data[3:5])[0]
            self.voc = struct.unpack('>H', data[5:7])[0]
            self.humidity = int(struct.unpack('>H', data[7:9])[0]/10)
            self.temperature = (struct.unpack('>H', data[9:11])[0]-500)/10
            self.PM1p0_grimm = struct.unpack('>H', data[11:13])[0]
            self.PM2p5_grimm = struct.unpack('>H', data[13:15])[0]
            self.PM10_grimm = struct.unpack('>H', data[15:17])[0]
            self.PM1p0_tsi = struct.unpack('>H', data[17:19])[0]
            self.PM2p5_tsi = struct.unpack('>H', data[19:21])[0]
            self.PM10_tsi = struct.unpack('>H', data[21:23])[0]
        except:
            pass
    def _get_and_reset(self, attribute):
        if getattr(self, attribute) is None:
            self._read()
        value = getattr(self, attribute)
        setattr(self, attribute, None)
        return value

    def get_co2(self):
        return self._get_and_reset('co2')

    def get_voc(self):
        return self._get_and_reset('voc')

    def get_humidity(self):
        return self._get_and_reset('humidity')

    def get_temperature(self):
        return self._get_and_reset('temperature')

    def get_PM1p0_grimm(self):
        return self._get_and_reset('PM1p0_grimm')

    def get_PM2p5_grimm(self):
        return self._get_and_reset('PM2p5_grimm')

    def get_PM10_grimm(self):
        return self._get_and_reset('PM10_grimm')

    def get_PM1p0_tsi(self):
        return self._get_and_reset('PM1p0_tsi')

    def get_PM2p5_tsi(self):
        return self._get_and_reset('PM2p5_tsi')

    def get_PM10_tsi(self):
        return self._get_and_reset('PM10_tsi')
    
if __name__ == '__main__':
    from utime import sleep_ms
    am1008 = AM1008(3)
    while True:
        print ('CO2:{} ppm\tvoc:{}\thumity:{}%\ttemperature:{} oC'.format(
            am1008.get_co2(), am1008.get_voc(), am1008.get_humidity(), am1008.get_temperature()))
        print ('PM1.0 Grimm:{} ug/m3\tPM2.5 Grimm:{} ug/m3\tPM10 Grimm:{} ug/m3'.format(
            am1008.get_PM1p0_grimm(), am1008.get_PM2p5_grimm(), am1008.get_PM10_grimm()))
        print ('PM1.0 TSI:{} ug/m3\tPM2.5 TSI:{} ug/m3\tPM10 TSI:{} ug/m3'.format(
            am1008.get_PM1p0_tsi(), am1008.get_PM2p5_tsi(), am1008.get_PM10_tsi()))


        sleep_ms(2000)

