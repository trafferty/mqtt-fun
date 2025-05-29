import socket
import fcntl
import struct
import sys
import time
import json
from datetime import datetime

import paho.mqtt.client as mqtt
import ssl

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode('utf-8'))
    )[20:24])

# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)

# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, reason_code, properties):
    print("[on_publish] mid: " + str(mid))

# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload).decode('UTF-8'))

def main():
    if len(sys.argv) <= 2:
        print("Error: Must pass name of interface, ie eno1, and topic, ie pickle-ip/ipcs")
        exit()
    ifname = sys.argv[1]
    topic = sys.argv[2]

    ip_address = get_ip_address(sys.argv[1])
    print(f"IP address of {ifname} is {ip_address}")
    
    # using MQTT version 5 here, for 3.1.1: MQTTv311, 3.1: MQTTv31
    # userdata is user defined data of any type, updated by user_data_set()
    # client_id is the given name of the client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="cnt-ipcs-provider", userdata=None, protocol=mqtt.MQTTv5)
    client.on_connect = on_connect

    # enable TLS for secure connection
    client.tls_set(tls_version=ssl.PROTOCOL_TLS)
    # set username and password
    client.username_pw_set("scoober", "honeyPOT357")
    # connect to HiveMQ Cloud on port 8883 (default for MQTT)
    client.connect("1c1f5db0298f41a98023dbac15ffd0ed.s1.eu.hivemq.cloud", 8883)

    # setting callbacks, use separate functions like above for better visibility
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    client.on_publish = on_publish

    client.loop_start()
    
    message = {"timestamp": f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
               "ip_address":ip_address}

    client.publish(topic, payload=json.dumps(message), qos=1)

    fname = "mqtt_pub.log"
    with open(fname, "a") as file:
        file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Send msg: {message}\n")

    # loop_forever for simplicity, here you need to stop the loop manually
    # you can also use loop_start and loop_stop
    client.loop_stop()
    client.disconnect()

if __name__ == '__main__':
    main()