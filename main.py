import usocket as socket
import network
import time
from machine import Pin, ADC, RTC, I2C, SPI
import ssd1306
import urequests
import ujson


def settoone(p):
    global countC, start, count, test
    test = True
    start = True
    count = 0
    countC = 1
    print("start :%s, count :%d", start, count)


def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(False)
    if not sta_if.isconnected():
        sta_if.active(True)
        sta_if.connect('ASUS_40_2G', 'athlete_3942')
        while not sta_if.isconnected():
            print("Fail!")
            pass
    print(sta_if.ifconfig()[0])


def main():
    global countC
    modeName = ("Board date&time",
                "Set hour",
                "Set minute",
                "Set second",
                "Set year",
                "Set month",
                "Set day",
                "Set Alarm",
                "Alarm is Set!"
                )
    InitDatetime = (2018, 10, 1, 1, 5, 20, 0, 0)
    ec2 = "http://18.208.184.238"
    tw = False
    alarm = False
    mode = 0
    alarm_second = 0
    alarm_s = 0
    alarm_m = 0
    rtc = RTC()
    rtc.datetime(InitDatetime)
    i2c = I2C(-1, Pin(5), Pin(4))
    oled = ssd1306.SSD1306_I2C(128, 32, i2c)
    oled.invert(True)
    lightsensor = ADC(0)
    p2 = Pin(2, Pin.OUT)
    C = Pin(0, Pin.IN, Pin.PULL_UP)
    C.irq(trigger=Pin.IRQ_RISING, handler=settoone)
    spi = SPI(1, baudrate=5000000, polarity=1, phase=1)
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
    do_connect()
    addr = socket.getaddrinfo('192.168.50.66', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    s.settimeout(1)
    command = "time"
    while True:
        light = lightsensor.read()
        bright = 260 - int(light / 4)
        oled.contrast(bright)
        p2.on()
        try:
            cl, addr = s.accept()
            cl_file = cl.makefile('rwb', 0)
            while True:
                line = cl_file.readline()
                if not line or line == b'\r\n':
                    break
            data = cl.recv(30)
            text = bytes.decode(data)
            command = ""
            for letter in text:
                if letter == "+":
                    command += " "
                elif letter != "=":
                    command += letter
            cl.close()
            alarm = False
        except OSError:
            pass

        if tw and (command != 'Twitter'):
            #twtdata = ujson.dumps(command)
            urequests.get(url=ec2, data=command, headers={})
            tw = False
        if command == 'turn off':
            oled.fill(1)
            oled.show()
        elif command == 'weather':
            response = urequests.post(url='https://www.googleapis.com/geolocation/v1/geolocate?key=AIzaSyASz3-6YEoJgIHCLo9D7MrWL3t2xVbCtGU', json={}, headers={})
            coord = response.json()['location']
            lon = coord['lng']
            lat = coord['lat']
            openWeatherAPI = 'https://api.openweathermap.org/data/2.5/weather?lat=%s&lon=%s&APPID=485773e6e6cf15297361b56c1f2c2dc4' % (lat, lon)
            response = urequests.post(url=openWeatherAPI, json={}, headers={})
            weather = response.json()['weather']
            name = response.json()['name']
            maininfo = response.json()['main']
            oled.fill(0)
            oled.text("%s" % name, 5, 0)
            oled.text("Dscrp: %s" % weather[0]['main'], 5, 8)
            oled.text("Temp: %.02f" % (maininfo['temp'] - 273.15) + 'C', 5, 16)
            oled.show()
        elif command == 'time':
            year, month, day, weekday, hour, minute, second, tzinfo = rtc.datetime()
            if alarm or (alarm_s == int(second) and alarm_m == minute):
                alarm = True
                oled.fill(0)
                oled.text("TIME IS OUT!", 10, 8)
                oled.show()
                p2.off()
            if mode == 1:
                hour += countC
                hour = hour % 24
            elif mode == 2:
                minute += countC
                minute = minute % 60
            elif mode == 3:
                second += countC
                second = second % 60
            elif mode == 4:
                year += countC
            elif mode == 5:
                month += countC
                if month > 12:
                    month -= 12
            elif mode == 6:
                day += countC
                if day > 30:
                    day -= 30
            elif mode == 7:
                alarm_second += countC
                if alarm_second < 0:
                    alarm_second = 0
                oled.fill(0)
                oled.text(modeName[mode], 10, 0)
                oled.text("After %d s" % alarm_second, 10, 8)
                oled.show()
            elif mode == 8 and alarm_second != 0:
                alarm_s = second + alarm_second
                alarm_second = 0
                alarm_m = minute + int(alarm_s / 60)
                alarm_s = int(alarm_s % 60)
            if mode != 7:
                rtc.datetime((year, month, day, weekday, hour, minute, second, tzinfo))
                oled.fill(0)
                oled.text(modeName[mode], 10, 0)
                oled.text("%d:%d:%02d " % (hour, minute, second), 10, 8)
                oled.text("%d/%d/%d" % (month, day, year), 10, 16)
                oled.show()
            countC = 0
        elif command == 'next':
            mode += 1
            command = 'time'
        elif command == 'alarm':
            mode = 7
            command = 'time'
        elif command == 'return':
            mode = 0
            command = 'time'
        elif command == 'Twitter':
            tw=True
            oled.fill(0)
            oled.text("Say something...", 5, 8)
            oled.show()
        elif command == 'columbia':
            oled.fill(0)
            oled.text("Ready for move!", 10, 8)
            oled.show()
            if start:
                time.sleep(1)
                data = []
                count = 0
                while count < 50:
                    cs.value(0)
                    spi.write(b'\xb2')
                    datax0 = spi.read(1)
                    cs.value(1)
                    cs.value(0)
                    spi.write(b'\xb3')
                    datax1 = spi.read(1)
                    cs.value(1)
                    datax = datax0[0] + (datax1[0] << 8)
                    if datax > 32767:
                        datax = datax - 65535
                    print("x: ", datax)
                    cs.value(0)
                    spi.write(b'\xb4')
                    datay0 = spi.read(1)
                    cs.value(1)
                    cs.value(0)
                    spi.write(b'\xb5')
                    datay1 = spi.read(1)
                    cs.value(1)
                    datay = datay0[0] + (datay1[0] << 8)
                    if datay > 32767:
                        datay = datay - 65535
                    print("y: ", datay)
                    data.append(datax)
                    data.append(datay)
                    count += 1
                    time.sleep_ms(10)
                jsondata = ujson.dumps(data)
                if test:
                    response = urequests.post(url=ec2, data=jsondata, headers={})
                    oled.fill(0)
                    oled.text(response.text, 5, 8)
                    oled.show()
                start = False
            time.sleep_ms(200)
        else:
            oled.fill(0)
            oled.text(command, 10, 8)
            oled.show()


if __name__ == "__main__":
    main()