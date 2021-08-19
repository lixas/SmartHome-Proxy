# best version to use
# C:\Users\lixas\Workspace\Firmware\Micropython_ESP32\esp32-idf4-20200902-v1.13.bin

import ubluetooth, network, ubinascii, machine, gc, esp, json, time
from micropython import const
from lib.mqtt import MQTTClient
esp.osdebug(None)

with open('settings.json', 'r') as f:
    global_settings = json.loads(f.read())

# I've added led so I could see BLE scanning works
led = machine.Pin(2, machine.Pin.OUT, value=1)

sta_if = network.WLAN(network.STA_IF)
if not sta_if.isconnected():
    sta_if.active(True)
    sta_if.connect(global_settings["wifi"]["ssid"], global_settings["wifi"]["pass"])
    while not sta_if.isconnected():
        pass

led.off()

sensor_mac_list = []
for sens in global_settings["sensors"]:
    sensor_mac_list.append(sens['mac'])

c = MQTTClient("BLE-To-HTTP_{}".format(ubinascii.hexlify(machine.unique_id())), global_settings["mqtt"]["broker"])
try:
    c.connect()
except:
    #sleep for 60 seconds (60000 milliseconds)
    print("Can not connect. Deep sleep 1 minute then restart")
    machine.deepsleep(60000)



def bt_irq(event, data):
    global led, dog
    dog.feed()
    led.value(not led.value())
    if event == const(6):       # _IRQ_SCAN_DONE
        print("Complete BLE scanning")
        ble.gap_scan(None)
    elif event == const(5):     # _IRQ_SCAN_RESULT:
        # addr_type, addr, adv_type, rssi, adv_data = data
        # print('type:{} addr:{} rssi:{} data:{}'.format(addr_type, ubinascii.hexlify(addr), rssi, ubinascii.hexlify(adv_data)))
        if ubinascii.hexlify(data[1]).decode("utf-8") in sensor_mac_list:
            try:
                c.publish("{}{}".format(global_settings["mqtt"]["base"], ubinascii.hexlify(data[1]).decode('utf-8')),
                    """{{"rssi":{}, "payload":"{}"}}""".format(data[3], ubinascii.hexlify(data[4]).decode('utf-8'))
                )
            except:
                machine.reset()
            gc.collect()
    else:
        print("Terminated")


ble = ubluetooth.BLE()
ble.active(True)
ble.irq(handler=bt_irq)
dog = machine.WDT(timeout=30000)    # 30 sec
ble.gap_scan(0, 30000, 30000)
