from __future__ import division
from __future__ import print_function
import os
import sys
import socket
import time
import pyaudio
import wave
import multiprocessing as mp
import logging
import select
import Adafruit_PCA9685

class CRobotManager:
    
    def __init__(self, logging, s, ActionQ, MotionQ,
                 actioning, waiting, stopAction, stopWait, saying, motioning, stopMotion,
                 pwm, leftPos, rightPos):
        self.logging = logging
        self.s = s
        self.ActionQ = ActionQ
        self.MotionQ = MotionQ
        self.actioning = actioning
        self.waiting = waiting
        self.stopAction = stopAction
        self.stopWait = stopWait
        self.motioning = motioning
        self.stopMotion = stopMotion
        self.pwm = pwm
        self.leftPos = leftPos
        self.rightPos = rightPos
        

        
    def actionManager(self):
        while True:
            if not self.ActionQ.empty():
                self.actioning.value = 1
                self.stopAction.value = -1
                action = self.getAction()
                self.doAction(action)
        return


    def doAction(self, actionCmd):
        category = actionCmd.split(":")[0]
        remainCmd = actionCmd.replace(category + ":", "")
        
        if category == "say":
            self.say(remainCmd)
            self.logging.info(actionCmd)
            
        elif category == "wait":
            self.waitLoop(remainCmd)
            self.logging.info(actionCmd)
            
        elif category == "print":
            self.Testprint(remainCmd)
            self.logging.info(actionCmd)
            
        elif category == "requestMessage":
            sendMsg = remainCmd.replace(remainCmd.split(":")[0] + ":", "")
            self.requestMessage(sendMsg)
            self.logging.info(actionCmd)
            
        elif category == "scenarioInit":
            self.clearAction()
            self.clearWait()
            self.stopVoice()
            self.logging.info("clear command:" + category)
            
        elif category == "clearAction":
            self.clearAction()
            self.logging.info("clear command:" + category)
            
        elif category == "clearWait":
            self.clearWait()
            self.logging.info("clear command:" + category)

        elif category == "Move":
            self.doMotion(remainCmd)
            self.logging.info("Motion:" + category)
            
        else:
            self.logging.warning("unknown command:" + actionCmd)
            return None


    def manageActionQ(self, Cmd, action):
        if Cmd == "DEQ":
            gotAction = self.ActionQ.get()
            return gotAction
        
        elif Cmd == "ENQ":
            self.ActionQ.put(action)
            return None
        
        elif Cmd == "ALLDELETE":
            while not self.ActionQ.empty():
                self.ActionQ.get()
            self.actioning.value = -1
            return None
        
        else:
            self.logging.warning("unknown Queue command:" + Cmd)
            return None


    def addAction(self, action):
        self.manageActionQ("ENQ", action)


    def getAction(self):
        return self.manageActionQ("DEQ", None)


    def Testprint(self, cmd):
        print(cmd + "\n")


    def say(self, cmd):
        filename = (cmd + ".wav").replace("\n", "")
        self.openWave(filename)


    def openWave(self, name):
        self.actioning.value = 1
        self.stopAction.value = -1
        
        try:
            wf = wave.open(name, "rb")
        except:
            self.logging.error("No such file:" + name)
        
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)
        chunk = 2048
        wf.rewind()
        data = wf.readframes(chunk)
        
        while data != b'':
            if self.stopAction.value == 1:
                break
            stream.write(data)
            data = wf.readframes(chunk)
            
        self.actioning.value = -1
        
        stream.close()
        p.terminate()


    def waitLoop(self, Msg):
        self.waiting.value = 1
        self.stopWait.value = -1
        
        waitTime = int(Msg) / 1000
        startTime = time.time()
        nowTime = time.time()
        
        while (delta := nowTime - startTime) < waitTime:
            if self.stopWait.value == 1:
                break
            nowTime = time.time()
            
        self.waiting.value = -1


    def clearWait(self):
        while self.waiting.value == 1:
            self.stopWait.value = 1


    def clearAction(self):
        self.manageActionQ("ALLDELETE", None)
        while self.actioning.value == 1:
            self.stopAction.value = 1


    def requestMessage(self, Msg):
        Msg += "\n"
        self.s.send(Msg.encode())
    
#####Motion################################
    def motionManager(self):
        while True:
            if not self.MotionQ.empty():
                self.motioning.value = 1
                self.stopMotion.value = -1
                motion = self.getMotion()
                self.doMotion(motion)
        return

    def doMotion(self, motionCmd):
        category = motionCmd.split(":")[0]
        remainCmd = motionCmd.replace(category + ":", "")
        
        if category == "home":
            self.home()
            self.logging.info(motionCmd)
            
        elif category == "armclose":
            self.armclose()
            self.logging.info(motionCmd)
            
        elif category == "armopen":
            self.armopen()
            self.logging.info(motionCmd)
            
        elif category == "patting":
            self.patting()
            self.logging.info(motionCmd)
            
        else:
            self.logging.warning("unknown command:" + motionCmd)
            return None


    def manageMotionQ(self, Cmd, motion):
        if Cmd == "DEQ":
            gotMotion = self.MotionQ.get()
            return gotMotion
        
        elif Cmd == "ENQ":
            self.MotionQ.put(motion)
            return None
        
        elif Cmd == "ALLDELETE":
            while not self.MotionQ.empty():
                self.MotionQ.get()
            self.motioning.value = -1
            return None
        
        else:
            self.logging.warning("unknown Queue command:" + Cmd)
            return None


    def addMotion(self, motion):
        self.manageMotionQ("ENQ", motion)


    def getMotion(self):
        return self.manageMotionQ("DEQ", None)
    
    
    def home(self):
        self.motioning.value = 1
        self.stopMotion.value = -1
        
        self.leftPos = 550
        self.rightPos = 250
        self.pwm.set_pwm(0, 0, self.leftPos)#left
        self.pwm.set_pwm(1, 0, self.rightPos)#right
        time.sleep(2)
        
        self.motioning.value = -1

    def armclose(self):
        self.motioning.value = 1
        self.stopMotion.value = -1
        
        i=0.0
        for i in range(0,50):
            self.leftPos -= 1
            self.rightPos += 1

            if(self.leftPos < 150):
                self.leftPos = 150
            if(self.rightPos > 850):
                self.rightPos = 850

            self.pwm.set_pwm(0, 0, self.leftPos)#left
            self.pwm.set_pwm(1, 0, self.rightPos)#right
            self.time.sleep(0.01)
        print("leftPos: " + str(self.leftPos) + ", rightPos: " + str(self.rightPos))
        
        self.motioning.value = -1
    
    def armopen(self):
        self.motioning.value = 1
        self.stopMotion.value = -1
        
        i=0.0
        for i in range(0,50):
            self.leftPos += 1
            self.rightPos -= 1

            if(self.leftPos > 850):
                self.leftPos = 850
            if(self.rightPos < 150):
                self.rightPos = 150

            self.pwm.set_pwm(0, 0, self.leftPos)#left
            self.pwm.set_pwm(1, 0, self.rightPos)#right
            time.sleep(0.01)
        print("leftPos: " + str(self.leftPos) + ", rightPos: " + str(self.rightPos))
        
        self.motioning.value = -1

    def patting(self):
        self.motioning.value = 1
        self.stopMotion.value = -1
        
        i=0.0
        for i in range(0,150):
            self.leftPos += 1
            self.rightPos -= 1

            if(self.leftPos > 550):
                self.leftPos = 550
            if(self.rightPos < 250):
                self.rightPos = 250
            self.pwm.set_pwm(0, 0, self.leftPos)#left
            self.pwm.set_pwm(1, 0, self.rightPos)#right
            time.sleep(0.0001)
        print("leftPos: " + str(self.leftPos) + ", rightPos: " + str(self.rightPos))
        
        for i in range(0,150):
            self.leftPos -= 1
            self.rightPos += 1

            if(self.leftPos < 250):
                self.leftPos = 250
            if(self.rightPos > 550):
                self.rightPos = 550
            self.pwm.set_pwm(0, 0, self.leftPos)#left
            self.pwm.set_pwm(1, 0, self.rightPos)#right
            time.sleep(0.0001)
        print("leftPos: " + str(self.leftPos) + ", rightPos: " + str(self.rightPos))
        
        self.motioning.value = -1




###########################################

def main():
    #Log
    formatter = '%(asctime)s:%(message)s'
    LogCount = 0
    
    while True:
        LogFile = "log/CRlog" + str(LogCount) +".log"
        if not os.path.exists(LogFile):
            logging.basicConfig(format=formatter, filename=LogFile, level=logging.DEBUG)
            break
        LogCount += 1
        
    logging.info("Logging Start!")
    
    #Initialise the PCA9685 using the default address (0x40).
    pwm = Adafruit_PCA9685.PCA9685()
    pwm.set_pwm_freq(60)
    #print('Moving servo on channel 0, press Ctrl-C to quit...')
    
    leftPos = 600
    rightPos = 150
    pwm.set_pwm(0,0,leftPos)#left
    pwm.set_pwm(1,0,rightPos)#right
    time.sleep(2)
    
    #IP Address
    ipAddress_client = "163.221.125.34"
    portNum_client = 11000

    #Socket Connection
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ipAddress_client, portNum_client))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    logging.info("Socket Connection Succeeded!")

    buffer_size = 1024

    #Register
    name = "sota"
    init_message = "name;" + name + "\n"
    s.send(init_message.encode())
    logging.info("Name Register Succeeded!")

    #Action_Queue define
    ActionQ = mp.Queue()
    MotionQ = mp.Queue()
    
    #Flags define
    actioning = mp.Manager().Value('i', -1)
    waiting = mp.Manager().Value('i', -1)
    stopAction = mp.Manager().Value('i', -1)
    stopWait = mp.Manager().Value('i', -1)
    saying = mp.Manager().Value('i', -1)
    motioning = mp.Manager().Value('i', -1)
    stopMotion = mp.Manager().Value('i', -1)
    
    #Class
    CR = CRobotManager(
        logging, s, ActionQ, MotionQ,
        actioning, waiting, stopAction, stopWait, saying, motioning, stopMotion,
        pwm, leftPos, rightPos)
    
    #Multiprocessing
    process1 = mp.Process(
        target = CR.actionManager,
        args = ())
    process2 = mp.Process(
        target = CR.motionManager,
        args = ())
    
    process1.start()
    process2.start()
    logging.info("Multiprocessing Start!")
    
    #Receive messages
    while True:
        Msgs = s.recv(buffer_size).decode("utf-8").splitlines()
        
        for Msg in Msgs:
            if Msg.split(":")[0] == "addAction":
                remainMsg = Msg.replace(Msg.split(":")[0] + ":", "")
                CR.addAction(remainMsg)
                
            else:
                CR.doAction(Msg)
    
    s.close()
    logging.info("Socket Connection Closed!")
    
    return

if __name__ == "__main__":
    main()

