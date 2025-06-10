import paho.mqtt.client as mqtt
#from mqtt import mqtt
import ssl


# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    print("[on_connect] CONNACK received with code %s." % rc)
    if len(flags) > 0:
        print(f"[on_connect] Flags: {flags}")
    if properties != None:
        print(f"[on_connect] Props: {properties}")
        
# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("[on_subscribe] Subscribed: " + str(mid) + " " + str(granted_qos))

# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
    print("[on_message] " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload.decode('UTF-8')))

def main():
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

    #print(f"Received the following message: {client.user_data_get()}")

    # loop_forever for simplicity, here you need to stop the loop manually
    # you can also use loop_start and loop_stop
    client.loop_forever()

if __name__ == '__main__':
    main()