import RPi.GPIO as GPIO
import boto3
from botocore.exceptions import ClientError
from botocore.exceptions import EndpointConnectionError
import time
import sys
time.sleep(60)
import io
import os
import logging
import device_config as cfg
import water_level as wl
GPIO.setmode(GPIO.BOARD)
GPIO.setup(23,GPIO.OUT) #Red LED
GPIO.setup(33,GPIO.OUT) #Relay 1
GPIO.setup(40,GPIO.OUT) #Relay 2
GPIO.setup(22,GPIO.OUT) #Amber LED

GPIO.output(33,True) #resetting relay
GPIO.output(40,True) #resetting relay

sqs = boto3.resource(service_name='sqs',region_name=cfg.region_name,endpoint_url=cfg.endpoint_url,aws_access_key_id=cfg.key_id,aws_secret_access_key=cfg.secret_key)
sqs_resp = boto3.resource(service_name='sqs',region_name=cfg.region_name,endpoint_url=cfg.resp_endpoint_url,aws_access_key_id=cfg.key_id,aws_secret_access_key=cfg.secret_key)

logging.basicConfig(filename='msg.log',level=logging.DEBUG)
print('before main loop..')
counter = 0

while (counter >= -5):
	try:
		queue = sqs.get_queue_by_name(QueueName=cfg.q_name)
		queue_resp = sqs.get_queue_by_name(QueueName=cfg.resp_q_name)
		GPIO.output(22,True) #set amber to indicate msg receiver is polling
		sleep_t = cfg.stop_poll_freq
		sleep_t_fast=cfg.start_poll_freq
		sleep_time = sleep_t
		while True:
			messages = queue.receive_messages(MessageAttributeNames=['DeviceID'])
			if (messages.__len__() == 0):
				logging.info('no message..')
				print('no msg..')
			else:
				for message in messages:
					if message.message_attributes is not None:
						deviceId = message.message_attributes.get('DeviceID').get('StringValue')
						if(deviceId == cfg.device_id):
							sig=message.body
							logging.info(sig)
							message.delete()
							try:
								if(sig == 'START'):
									print('inside start..')
									GPIO.output(23,True) #Red LED
									GPIO.output(33,False) # Relay 1 on
									print('started..')
									queue_resp.send_message(MessageBody='STARTED', MessageAttributes={
									'DeviceID': {
									'StringValue': '1111',
									'DataType': 'String'
									}
									})
									time.sleep(3) #stop after 15 seconds.. even w/o waiting for stop signal..
									GPIO.output(23,False)
									GPIO.output(33,True)
									sleep_time = sleep_t_fast
								if(sig == 'STOP'):
									GPIO.output(23,False)
									GPIO.output(33,True)
									GPIO.output(40,True) #switch off relay 2 as well if it was turned on with checklevel signal..
									queue_resp.send_message(MessageBody='STOPPED', MessageAttributes={
									'DeviceID': {
									'StringValue': '1111',
									'DataType': 'String'
									}
									})
									sleep_time = sleep_t
								'''if(sig == 'CHKLVL'):
									level = wl.level()
									level_str = 'LEVEL: ' + str(level)
									queue_resp.send_message(MessageBody=level_str, MessageAttributes={
									'DeviceID': {
									'StringValue': '1111',
									'DataType': 'String'
									}
									})
									sleep_time = sleep_t '''
								if(sig == 'CHKLVL'):
									GPIO.output(40,False) #switch on relay 2..
									level = 1
									level_str = 'LEVEL: ' + str(level)
									queue_resp.send_message(MessageBody=level_str, MessageAttributes={
									'DeviceID': {
									'StringValue': '1111',
									'DataType': 'String'
									}
									})
									sleep_time = sleep_t
							except KeyboardInterrupt:
								logging.info('exiting')
								GPIO.cleanup()
			time.sleep(sleep_time)		
		
	except ClientError:
		logging.exception('client error.. continuing again for couple of more times..')
		print('client error..')
		time.sleep(15)
		counter -= 1
	except ConnectionError:
		logging.exception('connection exception... retrying')
		print('conn error..')
		time.sleep(15)
		counter -= 1
	except EndpointConnectionError:
		print('endpoint error..')
		logging.exception('network unavailable... retrying without changing counter..')
		time.sleep(15)
	except Exception:
		print('serious error..')
		logging.exception("Some unknown exception. Exiting...")
		exit	
logging.debug('counter exceeded for retries. exiting..')
