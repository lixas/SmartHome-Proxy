import ubluetooth, network, time, ubinascii, machine, gc, esp, json
from micropython import const
from lib.mqtt import MQTTClient
esp.osdebug(None)

with open('settings.json', 'r') as f:
    global_settings = json.loads(f.read())

# I've added led so I could see BLE scanning works
led = machine.Pin(2, machine.Pin.OUT, value=1)

sta_if = network.WLAN(network.STA_IF)
if not sta_if.isconnected():
    print("Connecting to WiFi...")
    sta_if.active(True)
    sta_if.connect(global_settings["wifi"]["ssid"], global_settings["wifi"]["pass"])
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.3)
print(".")
print("Connected")

led.off()

sensor_mac_list = []
for sens in global_settings["sensors"]:
    sensor_mac_list.append(sens['mac'])


c = MQTTClient("BLE-To-HTTP", global_settings["mqtt"]["broker"])
c.connect()


def bt_irq(event, data):
    global led
    led.value(not led.value())
    if event == const(6):       # _IRQ_SCAN_DONE
        print("Complete BLE scanning")
        # ble.gap_scan(None)
    elif event == const(5):     # _IRQ_SCAN_RESULT:
        # addr_type, addr, adv_type, rssi, adv_data = data

        if ubinascii.hexlify(data[1]).decode("utf-8") in sensor_mac_list:
            # print('type:{} addr:{} rssi:{} data:{}'.format(addr_type, ubinascii.hexlify(addr), rssi, ubinascii.hexlify(adv_data)))
            try:
                c.publish(global_settings["mqtt"]["base"] + ubinascii.hexlify(data[1]).decode('utf-8'),
                    """{{"rssi":{}, "payload":"{}"}}""".format(data[3], ubinascii.hexlify(data[4]).decode('utf-8'))
                )
            except:
                machine.reset()
            # del addr_type, addr, adv_type, rssi, adv_data, data
            gc.collect()
    else:
        print("Terminated")


ble = ubluetooth.BLE()
ble.active(True)
ble.irq(handler=bt_irq)
ble.gap_scan(0, 30000, 30000)