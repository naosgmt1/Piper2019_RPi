#!/usr/bin/env python3

import paho.mqtt.client as mqtt


###### Edit variables to your environment #######
broker_address = "192.168.0.31"     #MQTT broker_address
Topic = "Miho-MQTT"
Msg = "Greetings from RPi !!!"

# publish MQTT
print("creating new instance")
client = mqtt.Client("pub2") #create new instance

print("connecting to broker: %s" % broker_address)
client.connect(broker_address) #connect to broker

print("Publishing message: %s to topic: %s" % (Msg, Topic))
client.publish(Topic,Msg)

#################
## Alternatively you can send a single message without creating an instance
##print "sending now"
##mqtt.single(Topic, Msg, hostname=broker_address)
