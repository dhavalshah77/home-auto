import time
#time.sleep(60)
import RPi.GPIO as GPIO
import bluetooth
import os
import io
import logging
GPIO.setmode(GPIO.BOARD)
GPIO.setup(26,GPIO.OUT) #Red LED
GPIO.setup(22,GPIO.OUT) #Amber LED
GPIO.output(26,True) #briefly indicating bt is ready
time.sleep(5)
GPIO.output(26,False)
GPIO.output(22,False) #resetting LED if already on..
logging.basicConfig(filename='btserver.log',level=logging.DEBUG)
logging.info("started")
sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
sock.bind(("",1))
logging.info("bound..listening..")
sock.listen(1)
uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
bluetooth.advertise_service(sock, "WaterPiService", service_id = uuid,service_classes = [ uuid, bluetooth.SERIAL_PORT_CLASS ],profiles = [ bluetooth.SERIAL_PORT_PROFILE ] )
while True:
	client_sock,address = sock.accept()
	logging.info("Accepted connection from ")
	logging.info(address[0])
	time.sleep(0.01)
	data = client_sock.recv(512)
	command = data.decode('utf-8')
	time.sleep(0.01)
	if(command == "shutdown" ): # some command
		GPIO.output(26,True) #indicating shutdown
		time.sleep(5)
		GPIO.output(26,False)
		logging.info("system is shutting down..")
		os.system("sudo shutdown")
	elif(command == "reboot" ): # some command
		GPIO.output(26,True) #indicating shutdown
		time.sleep(5)
		GPIO.output(26,False)
		logging.info("system is rebooting..")
		os.system("sudo reboot")
	elif(command == "startpoll" ): # some command
		logging.info("device is polling..")
		os.system("python3 -u /home/pi/iot/msg_receiver.py > msg_receiver.log &")
		time.sleep(2)
		GPIO.output(22,True) #indicating startpoll
	elif(command == "stoppoll" ): # some command
		logging.info("device stopped polling..")
		os.system("sudo kill -9 $(ps -ef|grep \"python3 -u /home/pi/iot/msg_receiver.py > msg_receiver.log\"|grep -v \"grep\"|awk '{print $2}')")
		time.sleep(2)
		os.system("sudo kill -9 $(ps -ef|grep \"python3 -u /home/pi/iot/msg_receiver.py\"|grep -v \"grep\"|awk '{print $2}')")		
		GPIO.output(22,False) #indicating shutdown
	else: # case for wifi setup
		credstr = command
		logging.info("received [%s]" % credstr)
		creds = credstr.split(':')
		ssid = creds[0]
		pwd = creds[1]
		os.system("sudo cp /etc/wpa_supplicant/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf_orig")
		os.system("sudo chmod 755 /etc/wpa_supplicant/wpa_supplicant.conf")
		try:
			f1 = open("/etc/wpa_supplicant/wpa_supplicant.conf","r+")
			lines = f1.readlines()
			logging.info("original lines")
			logging.info(lines)
			flag = 0
			for i in range(0,len(lines)):
				line = lines[i]
				logging.info("individual lines : " + line)
				if(line.find(ssid)>=0):
					lines[i+1] = "        psk=\"" + pwd + "\"\n"
					logging.info("modified lines")
					logging.info(lines)
					f1.close()
					f2 = open("/etc/wpa_supplicant/wpa_supplicant.conf","w")
					f2.writelines(lines)
					f2.close()
					flag = 1
					GPIO.output(26,True) #indicating existing ssid is modified
					time.sleep(5)
					GPIO.output(26,False)
					break
			if(flag == 0):
				f1.close()
				f3 = open("/etc/wpa_supplicant/wpa_supplicant.conf","a")
				f3.write("\nnetwork={\n")
				f3.write("        ssid=\"" + ssid + "\"\n")
				f3.write("        psk=\"" + pwd + "\"\n")
				f3.write("        key_mgmt=WPA-PSK\n")
				f3.write("}")
				f3.close()
				GPIO.output(26,True) #indicating new wifi ssid is setup
				time.sleep(5)
				GPIO.output(26,False)
		except Exception:
			logging.exception("exceptoin occurred")
	client_sock.close()
sock.close()

