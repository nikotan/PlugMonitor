#!/usr/bin/python3
# -*- coding: utf-8 -*-
import myconfig
import urllib.request, json, os, sys
from pyHS100 import SmartPlug
import paho.mqtt.client as mqtt
import logging
from logging.handlers import TimedRotatingFileHandler


# setup logger
logger = logging.getLogger()
formatter = logging.Formatter('[%(levelname)s] %(asctime)s %(filename)s %(funcName)s(%(lineno)d) : %(message)s')
handler = TimedRotatingFileHandler(
    filename="log/log.log",
    when="D",
    interval=1,
    backupCount=31,
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


# on_connect triggered by MQTT client
def on_connect(client, userdata, flags, respons_code):
    logger.info('MQTT status: {0}'.format(respons_code))
    mqtt_topic = myconfig.get('mqtt', 'topic')
    client.subscribe(mqtt_topic)
    logger.info('MQTT subscribed: {}'.format(mqtt_topic))

# on_message triggered by MQTT client
def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode("utf-8"))
    logger.info('MQTT published payload: {}'.format(payload))

    if 'data' in payload and 'target' in payload['data'][0]:
        target = payload['data'][0]['target']
        if myconfig.has_option('plug', target):
            plug_host = myconfig.get('plug', target)
            plug = SmartPlug(plug_host)
            logger.info("Current state: %s" % plug.state)

            ifttt_url_format = myconfig.get('ifttt', 'url_format')
            ifttt_event = myconfig.get('ifttt', 'event')
            ifttt_key = myconfig.get('ifttt', 'key')
            ifttt_url = ifttt_url_format.format(ifttt_event, ifttt_key)
            ifttt_on = myconfig.get('ifttt', 'state_on')
            ifttt_off = myconfig.get('ifttt', 'state_off')
            sendIftttEvent(ifttt_url, plug.state, ifttt_on, ifttt_off)

# send IFTTT webhook event
def sendIftttEvent(url, state, state_on, state_off):
    state_str = state_on
    if state == 'OFF':
        state_str = state_off
    obj = {"value1" : state_str}
    json_data = json.dumps(obj).encode("utf-8")
    method = "POST"
    headers = {"Content-Type" : "application/json"}
    request = urllib.request.Request(url, data=json_data, method=method, headers=headers)
    with urllib.request.urlopen(request) as response:
        response_body = response.read().decode("utf-8")
        logger.info('IFTTT response: {}'.format(response_body))


if __name__ == '__main__':
    mqtt_host = myconfig.get('mqtt', 'host')
    mqtt_port = int(myconfig.get('mqtt', 'port'))
    mqtt_ca_certs = myconfig.get('mqtt', 'ca_certs')
    mqtt_token = myconfig.get('mqtt', 'token')

    # setup MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set('token:{}'.format(mqtt_token))
    client.tls_set(mqtt_ca_certs)
    client.connect(mqtt_host, mqtt_port)
    client.loop_forever()
