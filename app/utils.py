
import json
import socket

class CommonUtils(object):

    def __init__(self) -> None:
        """ Initialize CommonUtils """
    
    def getserial(self):
        cpuserial = "0000000000000000"
        try:
            f = open('/proc/cpuinfo','r')
            for line in f:
                if line[0:6]=='Serial':
                    cpuserial = line[10:26]
                f.close()
        except:
            # cpuserial = "darwin"
            cpuserial = "10000000f0d61812" 
        
        return cpuserial

    def is_connected(self):
        try:
            sock = socket.create_connection(("www.google.com", 80))
            if sock is not None:
                sock.close
            return True
        except OSError:
            pass
        return False


