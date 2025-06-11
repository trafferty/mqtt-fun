import sys
import time
import json
import argparse
import logging, logging.config
import signal

from mqtt_client import MqttClient

def checkConfig(config, required_keys):
    return all(k in config for k in required_keys)
      
def create_html(ip_lst):
    html_start = '''
        <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" /><title>Pickle System Ip Addresses</title><style>
        body {margin: 0;padding: 0;height: 100vh;display: flex;align-items: center;justify-content: center;background: linear-gradient(to right, #f0f2f5, #e0e7ff);font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;}
        select {width: 80ch;font-size: 1rem;padding: 10px;border-radius: 8px;border: 1px solid #ccc;box-shadow: 0 2px 5px rgba(0,0,0,0.1);background-color: white;}</style></head><body>'''

    entry_cnt = len(ip_lst) if len(ip_lst) >= 1 and len(ip_lst) <= 30 else 10 
    html_mid = f'<select size="{entry_cnt}">'
    for ip in ip_lst:
        html_mid += f"<option>{ip}</option>"
    html_mid += "</select>"

    html_end = "</body></html>\n"
    
    return html_start + html_mid + html_end

def save_html_file(fname, html):
    with open(fname, "w") as file:
        file.write(html)
  
if __name__ == "__main__":
    done = False
    def sigint_handler(signal, frame):
        global done
        print( "\nShutting down...")
        done = True
    signal.signal(signal.SIGINT, sigint_handler)
    
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
                     "clean_start","topic_list","subscribe_qos","sleep_time_s")        
    if not checkConfig(config, required_keys):
        logger.error(f"Config file ({args.config_file_path}) does not contain correct attributes")
        sys.exit()
        
    sleep_time_s   = config["sleep_time_s"] if "sleep_time_s" in config else 10
    html_file_name = config["html_file_name"] if "html_file_name" in config else "index.html"
    msg_truncate_value = config["msg_truncate_value"] if "msg_truncate_value" in config else 20
    log_file_name = config["log_file_name"] if "log_file_name" in config else "ip_client.log"
    
    fileHandler = logging.FileHandler(log_file_name)
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)
    
    logger.info("*** Starting IP Address Message Utility. ***")
    logger.info(f"  Listening for IP address MQTT msgs for these topics: {config['topic_list']}")
    logger.info(f"  Writing HTML file with addresses: {html_file_name}\n")
    
    logger.info("Creating MQTT Client")
    mqtt_client = MqttClient(config, logger)

    logger.info("Setting up and connecting")
    mqtt_client.setup()
    mqtt_client.connect()
        
    logger.info("Starting process loop...")
    mqtt_client.start()
    while not done:
        ip_lst = mqtt_client.get_msgs(msg_truncate_value)
        html   = create_html(ip_lst)
        save_html_file(html_file_name, html)

        for _ in range(sleep_time_s * 2):
            if done: break
            time.sleep((1 / 2))

    logger.info("Stopping client loop and disconnecting")
    mqtt_client.stop()
    mqtt_client.disconnect()
