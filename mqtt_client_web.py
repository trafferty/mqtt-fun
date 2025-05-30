import paho.mqtt.client as mqtt
import ssl
import time
import signal
from threading import Thread, Lock

mutex = Lock()
doWork = True
msg_lst = []

log_file = "mqtt_client.log"

def doLog(log_msg):
    global log_file
    msg = f"{time.strftime('[%Y_%d_%m (%a) - %H:%M:%S]', time.localtime())}: {log_msg}"
    print (msg)
    with open(log_file, "a") as file:
        file.write(f"[{msg}\n")

# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    doLog("[on_connect] CONNACK received with code %s." % rc)
    if len(flags) > 0:
        doLog(f"[on_connect] Flags: {flags}")
    if properties != None:
        doLog(f"[on_connect] Props: {properties}")
        
# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    doLog("[on_subscribe] Subscribed: " + str(mid) + " " + str(granted_qos))

# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
    doLog("[on_message] " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload.decode('UTF-8')))
    with mutex:
        msg_lst.append(msg)

def main():
    global doWork, mutex
    signal.signal(signal.SIGINT, signal_handler)
    
    # using MQTT version 5 here, for 3.1.1: MQTTv311, 3.1: MQTTv31
    # userdata is user defined data of any type, updated by user_data_set()
    # client_id is the given name of the client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="jesse", userdata=None, protocol=mqtt.MQTTv5)
    client.on_connect = on_connect
    # setting callbacks, use separate functions like above for better visibility
    client.on_subscribe = on_subscribe
    client.on_message = on_message

    # enable TLS for secure connection
    client.tls_set(tls_version=ssl.PROTOCOL_TLS)
    # set username and password
    client.username_pw_set("scoober", "honeyPOT357")
    # connect to HiveMQ Cloud on port 8883 (default for MQTT)
    client.connect("1c1f5db0298f41a98023dbac15ffd0ed.s1.eu.hivemq.cloud", 8883, clean_start=False)

    # # subscribe to all topics of encyclopedia by using the wildcard "#"
    client.subscribe("pickle-ip/#", qos=1)

    #t = Thread(target = worker)
    #t.start()
    
    #doLog(f"Received the following message: {client.user_data_get()}")

    # loop_forever for simplicity, here you need to stop the loop manually
    # you can also use loop_start and loop_stop
    doLog("Starting client loop")
    client.loop_start()
    
    sleep_time_s = 10
    while doWork:
        handle_msgs()
        for _ in range(sleep_time_s * 2):
            if not doWork: break
            time.sleep((1 / 2))

    doLog("Stopping client loop and disconnecting")
    client.loop_stop()
    client.disconnect()

def signal_handler(sig, frame):
    global doWork
    doWork = False    
    doLog("Caught ctrl-c...")

def worker():
    global doWork
    doLog("Starting worker...")
    sleep_time_s = 10
    while doWork:
        handle_msgs()
        for _ in range(sleep_time_s * 2):
            if not doWork: break
            time.sleep((1 / 2))
    doLog("Exiting worker...")

def handle_msgs():
    global msg_lst, mutex
    with mutex:
        msg_lst = msg_lst[-15:]
        ip_lst = [f"{msg.topic}: {str(msg.payload.decode('UTF-8'))}" for msg in msg_lst]
        html = create_html(ip_lst)
        save_html_file("index.html", html)

def create_html(ip_lst):
    html_start = '''
        <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" /><title>Pickle System Ip Addresses</title><style>
        body {margin: 0;padding: 0;height: 100vh;display: flex;align-items: center;justify-content: center;background: linear-gradient(to right, #f0f2f5, #e0e7ff);font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;}
        select {width: 80ch;font-size: 1rem;padding: 10px;border-radius: 8px;border: 1px solid #ccc;box-shadow: 0 2px 5px rgba(0,0,0,0.1);background-color: white;}</style></head><body><select size="15">'''

    html_mid = ""
    for ip in ip_lst:
        html_mid += f"<option>{ip}</option>"

    html_end = "</select></body></html>\n"
    
    return html_start + html_mid + html_end

def save_html_file(fname, html):
    with open(fname, "w") as file:
        file.write(html)

if __name__ == '__main__':
    main()