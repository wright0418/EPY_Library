from machine import I2C
class JoyStick():
    def __init__(self, i2c):
        self.i2c_port = i2c
        self.addr = 0x5a
        self.joystick_start_addr = 0x10
        self.button_start_addr = 0x20

    def readXY(self):
        data = list(self.i2c_port.mem_read(
            2, self.addr, self.joystick_start_addr))
        return (data[0], data[1])

    def readButton(self, btn='J'):
        btn_dic = {'J': 0, 'C': 1, 'A': 2, 'B': 3, 'D': 4}
        data = list(self.i2c_port.mem_read(
            5, self.addr, self.button_start_addr))
        return (True if data[btn_dic[btn]] == 0 else False)

if __name__ == '__main__':
    from machine import I2C
    import utime as time
    i2c = I2C(0,I2C.MASTER,baudrate =400000)
    JS = JoyStick(i2c)

    while True:
        x,y = JS.readXY()
        btnA = JS.readButton('A')
        btnB = JS.readButton('B')
        btnC = JS.readButton('C')
        btnD = JS.readButton('D')
        btnJ = JS.readButton('J')

        print (x,y)
        print (btnA,btnB,btnC,btnC,btnD,btnJ)

        time.sleep(0.5)