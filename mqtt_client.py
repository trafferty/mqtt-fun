from threading import Thread, Lock

import paho.mqtt.client as mqtt
import ssl

class MqttClient(object):
    """
    MQTT client used to connect and subscribe to certain topics
    """

    def __init__(self, config, logger):                
        self.logger = logger
        self.config = config
        self.mutex = Lock()
        self.msg_lst = []
        self.client = None
        
        self.name = config["name"] if len(config["name"]) > 0 else "MqttClient"

    # setting callbacks for different events to see if it works, print the message etc.
    def on_connect(self, client, userdata, flags, rc, properties=None):
        self.logger.info(f"[on_connect] CONNACK received with code {rc}")
        if len(flags) > 0:
            self.logger.info(f"[on_connect] flags: {flags}")
        if properties != None:
            self.logger.info(f"[on_connect] props: {properties}")
        
        qos = self.config["subscribe_qos"]
        # subscribe to some topics
        for topic in self.config["topic_list"]:
            self.logger.info(f"[on_connect] subscribing to topic: {topic}")
            client.subscribe(topic, qos=1)
            
    # print which topic was subscribed to
    def on_subscribe(self, client, userdata, mid, granted_qos, properties=None):
        self.logger.info(f"[on_subscribe] Subscribed: {str(mid)}, QOS: {str(granted_qos)}")
        if properties != None:
            self.logger.info(f"[on_subscribe] props: {properties}")
        if userdata != None:
            self.logger.info(f"[on_subscribe] userdate: {userdata}")

    def on_unsubscribe(self, client, userdata, mid, reason_code_list, properties=None):
        self.logger.info(f"[on_unsubscribe] Subscribed: {str(mid)}")
        if properties != None:
            self.logger.info(f"[on_unsubscribe] props: {properties}")
        for reason_code in reason_code_list:
            self.logger.info(f"[on_unsubscribe] reason_code: {reason_code}")

    def on_message(self, client, userdata, msg):
        self.logger.info("[on_message] " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload.decode('UTF-8')))
        with self.mutex:
            self.msg_lst.append(msg)

    def setup(self):
        self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, 
                                  client_id=self.config["client_id"], 
                                  userdata=None, protocol=mqtt.MQTTv5)
        self.mqttc.enable_logger(self.logger)

        self.mqttc.on_connect     = self.on_connect
        self.mqttc.on_subscribe   = self.on_subscribe
        self.mqttc.on_unsubscribe = self.on_unsubscribe
        self.mqttc.on_message     = self.on_message

        # enable TLS for secure connection
        self.mqttc.tls_set(tls_version=ssl.PROTOCOL_TLS)
        # set username and password
        self.mqttc.username_pw_set(self.config["client_username"], self.config["client_pw"])
    
    def connect(self):
        self.mqttc.connect(self.config["hivemq_url"], self.config["hivemq_port"], 
                           clean_start=self.config["clean_start"])

    def start(self):
        self.mqttc.loop_start()
                
    def stop(self):
        self.mqttc.loop_stop()
                
    def disconnect(self):
        self.mqttc.disconnect()
                
    def get_msgs(self, msg_truncate_value=None):
        with self.mutex:
            if msg_truncate_value != None:
                self.msg_lst = self.msg_lst[-msg_truncate_value:]
            msgs = [f"{msg.topic}: {str(msg.payload.decode('UTF-8'))}" for msg in self.msg_lst]
        return msgs
