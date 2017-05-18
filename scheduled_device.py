import RPi.GPIO as GPIO
import logging
import time

GPIO.setmode(GPIO.BOARD)
GPIO.setup(23,GPIO.OUT) #Red LED
GPIO.setup(33,GPIO.OUT) #Relay 1d

try:
	GPIO.output(33,True) #resetting relay

	logging.basicConfig(filename='scheduled_msg.log',level=logging.DEBUG)

	GPIO.output(23,True)
	GPIO.output(33,False)
		
	time.sleep(3) # run the device for 50 and stop
	
	GPIO.output(23,False)
	GPIO.output(33,True)
	
	#GPIO.cleanup()
	
except Exception:
	logging.exception("Some unknown exception. Exiting...")
	#GPIO.cleanup()
	exit	
