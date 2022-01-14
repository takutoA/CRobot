# 2servo slow in bear
# slow hug -> 10s stay -> stop hug

# Simple demo of of the PCA9685 PWM servo/LED controller library.
# This will move channel 0 from min to max position repeatedly.
# Author: Tony DiCola
# License: Public Domain
from __future__ import division
from __future__ import print_function
import socket
import select
import time
#import pygame.mixer

# Import the PCA9685 module.
import Adafruit_PCA9685

# Uncomment to enable debug output.
#import logging
#logging.basicConfig(level=logging.DEBUG)

# Initialise the PCA9685 using the default address (0x40).
pwm = Adafruit_PCA9685.PCA9685()

# Alternatively specify a different address and/or bus:
#pwm = Adafruit_PCA9685.PCA9685(address=0x41, busnum=2)

# Configure min and max servo pulse lengths
#servo_min = 200  # Min pulse length out of 4096//90do
#servo_max = 350  # Max pulse length out of 4096
servo_center = 450

# Helper function to make setting a servo pulse width simpler.
def set_servo_pulse(channel, pulse):
    pulse_length = 1000000    # 1,000,000 us per second
    pulse_length //= 60       # 60 Hz
    print('{0}us per period'.format(pulse_length))
    pulse_length //= 4096     # 12 bits of resolution
    print('{0}us per bit'.format(pulse_length))
    pulse *= 1000
    pulse //= pulse_length

    #print '%d pulse' % pulse #tuketashi

    pwm.set_pwm(channel, 0, pulse)

def main():
    pwm.set_pwm_freq(60)
    print('Moving servo on channel 0, press Ctrl-C to quit...')

    host = '163.221.38.220'
    port = 11000
    backlog = 10
    bufsize = 4096

    leftPos = 600
    rightPos = 150
    pwm.set_pwm(0,0,leftPos)#left
    pwm.set_pwm(1,0,rightPos)#right
    time.sleep(2)

    #pygame.mixer.init()

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    readfds = set([server_sock])
    try:
        server_sock.bind((host, port))
        server_sock.listen(backlog)

        while True:
            rready, wready, xready = select.select(readfds, [], [])
            for sock in rready:
                if sock is server_sock:
                    conn, address = server_sock.accept()
                    readfds.add(conn)
                    print("new connection")

                else:
                    msg = sock.recv(bufsize).decode("utf-8").strip()
                    print(msg)
                    if len(msg) == 0:
                        sock.close()
                        readfds.remove(sock)
                        print("connectoin removed")

                    else:
                        if msg.split(",")[0] == 'MOVE':
                            tmpCommand = msg.split(",")[1].strip()
                            print("move command: " + tmpCommand)                        
                            if tmpCommand == 'home':
                                leftPos = 550
                                rightPos = 250
                                pwm.set_pwm(0,0,leftPos)#left
                                pwm.set_pwm(1,0,rightPos)#right
                                time.sleep(2)
                            elif tmpCommand == 'armclose':
                                i=0.0
                                for i in range(0,50):
                                    leftPos -= 1
                                    rightPos += 1

                                    if(leftPos < 150):
                                        leftPos = 150
                                    if(rightPos > 850):
                                        rightPos = 850

                                    pwm.set_pwm(0, 0,leftPos)#left
                                    pwm.set_pwm(1, 0,rightPos)#right
                                    time.sleep(0.01)
                                print("leftPos: " + str(leftPos) + ", rightPos: " + str(rightPos))                        
                            elif tmpCommand == 'armopen':
                                i=0.0
                                for i in range(0,50):
                                    leftPos += 1
                                    rightPos -= 1

                                    if(leftPos > 850):
                                        leftPos = 850
                                    if(rightPos < 150):
                                        rightPos = 150

                                    pwm.set_pwm(0, 0,leftPos)#left
                                    pwm.set_pwm(1, 0,rightPos)#right
                                    time.sleep(0.01)
                                print("leftPos: " + str(leftPos) + ", rightPos: " + str(rightPos))                        

                            elif tmpCommand == 'patting':
                                i=0.0
                                for i in range(0,150):
                                    leftPos += 1
                                    rightPos -= 1

                                    if(leftPos > 550):
                                        leftPos = 550
                                    if(rightPos < 250):
                                        rightPos = 250
                                    pwm.set_pwm(0, 0,leftPos)#left
                                    pwm.set_pwm(1, 0,rightPos)#right
                                    time.sleep(0.0001)
                                print("leftPos: " + str(leftPos) + ", rightPos: " + str(rightPos))
                                for i in range(0,150):
                                    leftPos -= 1
                                    rightPos += 1

                                    if(leftPos < 250):
                                        leftPos = 250
                                    if(rightPos > 550):
                                        rightPos = 550
                                    pwm.set_pwm(0, 0,leftPos)#left
                                    pwm.set_pwm(1, 0,rightPos)#right
                                    time.sleep(0.0001)
                                print("leftPos: " + str(leftPos) + ", rightPos: " + str(rightPos))


                        #elif msg.split(",")[0] == 'SAY':
                        #    print("say command: " + msg.split(",")[1])
                        #    tmpCommand = msg.split(",")[1].strip()
                        #    pygame.mixer.music.load("sound/" + tmpCommand)
                        #    pygame.mixer.music.play()
                        #sock.send(msg)

                        elif msg.split(",")[0] == 'EXIT':
                            sock.close()
                            readfds.remove(sock)
                            print("connectoin removed")

    finally:
        for sock in readfds:
            sock.close()
    return

if __name__ == '__main__':
    main()

