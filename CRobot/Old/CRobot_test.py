import os
import sys
import socket
import time
import pyaudio
import wave
import multiprocessing as mp
import logging


class CRobotManager:
    
    def __init__(self, logging, s, ActionQ, actioning, waiting, stopAction, stopWait, saying):
        self.logging = logging
        self.s = s
        self.ActionQ = ActionQ
        self.actioning = actioning
        self.waiting = waiting
        self.stopAction = stopAction
        self.stopWait = stopWait
        self.saying = saying

        
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
            self.logging.info("clear command:" + category)
            
        elif category == "clearAction":
            self.clearAction()
            self.logging.info("clear command:" + category)
            
        elif category == "clearWait":
            self.clearWait()
            self.logging.info("clear command:" + category)
            
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
        msg = cmd.split(":")[0]
        print(msg)
        
        
        #filename = (cmd + ".wav").replace("\n", "")
        #self.openWave(filename)


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
    
    #IP Address
    ipAddress_client = "163.221.38.219"
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
    
    #Flags define
    actioning = mp.Manager().Value('i', -1)
    waiting = mp.Manager().Value('i', -1)
    stopAction = mp.Manager().Value('i', -1)
    stopWait = mp.Manager().Value('i', -1)
    saying = mp.Manager().Value('i', -1)
    
    #Class
    CR = CRobotManager(logging, s, ActionQ, actioning, waiting, stopAction, stopWait, saying)
    
    #Multiprocessing
    process = mp.Process(
        target = CR.actionManager,
        args = ())
    process.start()
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

