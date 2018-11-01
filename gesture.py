# @Author      : 'Savvy'
# @Created_date: 2018/9/26 下午2:53

from machine import Pin, I2C, SPI
import time
import ssd1306
import network
import urequests
import ujson


def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...\n')
        sta_if.active(True)
        sta_if.connect('Columbia University', '')
        while not sta_if.isconnected():
            print("Fail to connect!")
            pass
    print('network config:', sta_if.ifconfig())
    print('connect info', sta_if.isconnected())


def recordTrainingData(p):
    global start, count, train
    train = True
    start = True
    count = 0
    print("start is %s, count is %d", start, count)


def recordTestingData(p):
    global start, count, test
    test = True
    start = True
    count = 0
    print("start is %s, count is %d", start, count)


def bytes_to_int(bytes):
    result = 0
    for b in bytes:
        result = result * 256 + int(b)
    return result


def readFromAccelerometer(spi):
    pass


def main():
    do_connect()

    global start, count, train, test
    start = False
    count = 0
    train = False
    test = False
    ec2mongodb = "http://18.208.184.238"
    C = Pin(0, Pin.IN, Pin.PULL_UP)
    C.irq(trigger=Pin.IRQ_RISING, handler=recordTestingData)
    spi = SPI(1, baudrate=5000000, polarity=1, phase=1)
    i2c = I2C(-1, Pin(5), Pin(4))
    oled = ssd1306.SSD1306_I2C(128, 32, i2c)
    cs = Pin(15, Pin.OUT)
    cs.value(0)
    spi.write(b'\x31')
    spi.write(b'\x08')
    cs.value(1)
    cs.value(0)
    spi.write(b'\x2D')
    spi.write(b'\x08')
    cs.value(1)
    cs.value(0)
    spi.write(b'\x2E')
    spi.write(b'\x80')
    cs.value(1)
    while True:
        print("COUNT = ", count)
        if start:
            time.sleep(1)
            data = []
            count = 0
            while count < 50:
                cs.value(0)
                spi.write(b'\xb2')
                datax0 = spi.read(1)
                cs.value(1)
                #print("datax0: ", datax0[0])
                cs.value(0)
                spi.write(b'\xb3')
                datax1 = spi.read(1)
                cs.value(1)
                #print("datax1: ", datax1[0])
                datax = datax0[0] + (datax1[0] << 8)
                if datax > 32767:
                    datax = datax-65535
                print("datax: ", datax)
                cs.value(0)
                spi.write(b'\xb4')
                datay0 = spi.read(1)
                cs.value(1)
                #print("datay0: ", datay0[0])
                cs.value(0)
                spi.write(b'\xb5')
                datay1 = spi.read(1)
                cs.value(1)
                #print("datay1: ", datay1[0])
                datay = datay0[0] + (datay1[0] << 8)
                if datay > 32767:
                    datay = datay-65535
                print("datay: ", datay)
                data.append(datax)
                data.append(datay)
                count += 1
                time.sleep_ms(10)
            print("data is of size ", len(data))
            jsondata = ujson.dumps(data)
            if train:
                response = urequests.put(url=ec2mongodb, data=jsondata, headers={})
                print(response.text)
            elif test:
                response = urequests.post(url=ec2mongodb, data=jsondata, headers={})
                print(response.text)
                oled.fill(0)
                oled.text(response.text, 5, 8)
                oled.show()
            else:
                pass
            start = False
        time.sleep_ms(200)


if __name__ == "__main__":
    main()



