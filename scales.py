from hx711 import HX711
from utime import sleep_us


class Scales(HX711):
    def __init__(self, d_out, pd_sck):
        super(Scales, self).__init__(d_out, pd_sck)
        self.offset = 0

    def reset(self):
        self.power_off()
        self.power_on()

    def tare(self):
        self.offset = self.read()

    def raw_value(self):
        return self.read() - self.offset

    def stable_value(self, reads=10, delay_us=500):
        values = []
        for _ in range(reads):
            values.append(self.raw_value())
            sleep_us(delay_us)
        return self._stabilizer(values)//100

    @staticmethod
    def _stabilizer(values, deviation=10):
        weights = []
        try:
            for prev in values:
                weights.append(sum([1 for current in values if abs(
                    prev - current) / (prev / 100) <= deviation]))
            return sorted(zip(values, weights), key=lambda x: x[1]).pop()[0]
        except:
            return 0


if __name__ == "__main__":
    from machine import Pin
    from utime import sleep_ms

    scales = Scales(d_out=Pin.epy.P16, pd_sck=Pin.epy.P17)  # I2C0
    sleep_ms(1000)  # delay 1s for sensor ready

    scales.tare()
    print ("start")
    while True:
        val = scales.stable_value()
        print(' raw = {}  '.format(val))
        if val > 1000:
            print(' {}g '.format(val/1000))
        sleep_ms(500)
