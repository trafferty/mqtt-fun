import socket
import fcntl
import struct
import sys
import argparse
import logging, logging.config
import json
from datetime import datetime

from mqtt_publisher import MqttPublisher

def checkConfig(config, required_keys):
    return all(k in config for k in required_keys)
      
def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode('utf-8'))
    )[20:24])

def main():
    parser = argparse.ArgumentParser(description='MQTT Client')
    parser.add_argument('-c', '--config_file_path', action="store", default='mqtt_client_config.json', help='path to config file')
    args = parser.parse_args()

    logFormatter = logging.Formatter("%(asctime)s [%(name)s] (%(levelname)s): %(message)s")
    logger = logging.getLogger("mqtt_client")
    logger.setLevel(logging.DEBUG)
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)
    
    try:
        with open(args.config_file_path) as config_file:
            try:
                config = json.load(config_file)
            except ValueError:
                logger.error("Error parsing config file: %s" % (args.config_file_path))
                raise
                sys.exit()
    except FileNotFoundError:
        logger.error("Error! Config file not found: %s" % (args.config_file_path))
        sys.exit()

    required_keys = ("client_id","client_username","client_pw","hivemq_url","hivemq_port",
                     "topic_list","publish_qos","ifname")        
    if not checkConfig(config, required_keys):
        logger.error(f"Config file ({args.config_file_path}) does not contain correct attributes")
        sys.exit()

    log_file_name = config["log_file_name"] if "log_file_name" in config else "ip_publisher.log"
    ifname = config["ifname"]
    pub_topic_list = config["topic_list"]
    
    fileHandler = logging.FileHandler(log_file_name)
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)

    logger.info("*** Starting IP Address Publisher Utility. ***")
    logger.info(f"  Looking for IP adress for this interface: {ifname}")
    logger.info(f"  Publishing to this topic list: {pub_topic_list}\n")

    ip_address = get_ip_address(ifname)
    logger.info(f"IP address of {ifname} is {ip_address}")
    
    logger.info("Creating MQTT Publisher")
    mqtt_client = MqttPublisher(config, logger)

    logger.info("Setting up and connecting")
    mqtt_client.setup()
    mqtt_client.connect()
    logger.info("Starting process loop...")
    mqtt_client.start()

    message = json.dumps({"timestamp": f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                          "ip_address":ip_address})
    logger.info(f"Message to publish: {message}")
    
    for pub_topic in pub_topic_list:
        logger.info(f"Publishing to topic: {pub_topic}")
        mqtt_client.publish(pub_topic, message)
    
    mqtt_client.stop()
    mqtt_client.disconnect()

if __name__ == '__main__':
    main()