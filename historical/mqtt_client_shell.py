#!/usr/bin/python

import sys
import socket
import random
import binascii
import paho.mqtt.client as mqtt

input = getattr(__builtins__, 'raw_input', input)

log_enabled = True

def on_connect(mqttc, obj, flags, rc):
    print("on_connect(): result code = {} ({})".format(rc, mqtt.connack_string(rc)))

def on_disconnect(mqttc, obj, rc):
    print("on_disconnect(): result code = {}".format(rc))

def on_message(mqttc, obj, msg):
    print("on_message(): message received: Topic: {}, QoS: {}, Payload Length: {}".format(msg.topic, msg.qos, len(msg.payload)))
    print("                                Payload (str): {}".format(str(msg.payload)))
    print("                                Payload (hex): {}".format(binascii.hexlify(msg.payload)))

def on_publish(mqttc, obj, mid):
    print("on_publish(): message published: msg id = {}".format(mid))

def on_subscribe(mqttc, obj, mid, granted_qos):
    print("on_subscribe(): subscribed: msg id = {}, granted_qos = {}".format(mid, granted_qos))

def on_unsubscribe(mqttc, obj, mid):
    print("on_unsubscribe(): unsubscribed: msg id = {}".format(mid))

def on_log(mqttc, obj, level, string):
    global log_enabled
    if log_enabled: print("on_log(): level={} - {}".format(level, string))


default_client_id = ("paho-" + str(random.randrange(1000, 10000)) + "-" + socket.gethostname())[:23]
client_id = input("\nClient ID to use for the connection (<Enter> for '{}'): ".format(default_client_id)).strip() or default_client_id
print("\nUsing client_id: {}".format(client_id))

mqttc = mqtt.Client(client_id=client_id, clean_session=True)

mqttc.on_connect = on_connect
mqttc.on_disconnect = on_disconnect
mqttc.on_message = on_message
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe
mqttc.on_unsubscribe = on_unsubscribe
mqttc.on_log = on_log

host = "localhost"
port = 1883
username = None
password = None
sub_topic = "#"
pub_topic = "test"
pub_msg_template = "Test message {}"
pub_msg_subst = "0"

connected = False

k = None

while True:
    k = input("\n===== {}onnect P)ublish S)ubscribe U)nsubscribe L)og[{}] Q)uit =====\n".format("D)isc" if connected else "C)", log_enabled)).upper()

    if k == "C":
        host = input("Host (<Enter> for '{}'): ".format(host)).strip() or host
        port = int(input("Port (<Enter> for {}): ".format(port)).strip() or port)
        username = input("Username (<Enter> for {}): ".format(username)).strip() or username
        if username:
            password = input("Password (<Enter> for {}): ".format(password)).strip() or password
            mqttc.username_pw_set(username, password)
        print("...connecting to {}:{} (client_id={}, keepalive=60, clean_session=True)".format(host, port, client_id))
        try:
            rc = mqttc.connect(host, port, keepalive=60)
            connected = (rc == mqtt.MQTT_ERR_SUCCESS)
        except socket.error as e:
            print(e)
        mqttc.loop_start()

    elif k == "D":
        mqttc.disconnect()
        connected = False
        mqttc.loop_stop()

    elif k == "P":
        pub_topic = input("Publish to topic (<Enter> for '{}'): ".format(pub_topic)).strip() or pub_topic
        pub_msg_template = input("Publish message template ({{}} replaced with next input) (<Enter> for '{}'): ".format(pub_msg_template)).strip() or pub_msg_template
        payld = pub_msg_template
        if '{}' in pub_msg_template:
            pub_msg_subst = str(1 + int(pub_msg_subst)) if pub_msg_subst.isdigit() else pub_msg_subst 
            pub_msg_subst = input("{{}} substitution (<Enter> for {}): ".format(pub_msg_subst)).strip() or pub_msg_subst
            payld = pub_msg_template.format(pub_msg_subst)
        print("...publishing message '{}' to topic '{}'  (qos=0, retain=False)".format(payld, pub_topic))
        (result, msg_id) = mqttc.publish(pub_topic, payload=payld, qos=0, retain=False)
        print("...msg_id={!r}, result={} ({})".format(msg_id, result, mqtt.error_string(result)))
	
    elif k == "S":
        sub_topic = input("Subscribe to topic (<Enter> for '{}'): ".format(sub_topic)).strip() or sub_topic
        print("...subscribing to topic: {}  (qos=0)".format(sub_topic))
        mqttc.subscribe(sub_topic, qos=0)

    elif k == "U":
        sub_topic = input("Unsubscribe from topic (<Enter> for '{}'): ".format(sub_topic)).strip() or sub_topic
        print("...unsubscribing from topic: " + sub_topic)
        mqttc.unsubscribe(sub_topic)

    elif k == "L":
        log_enabled = not log_enabled

    elif k == "Q":
        break

    else:
        print("Command not recognized")

