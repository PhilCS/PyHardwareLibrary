import usb.core
import usb.util
from communicationport import *
import re
import time
import random
from threading import Thread, RLock
import array

class USBPort(CommunicationPort):
    """USBPort class with basic application-level protocol 
    functions to write strings and read strings, and abstract away
    the details of the communication.
    """
    @classmethod
    def allDevices(cls, verbose=False):
        for bus in usb.busses():
            for device in bus.devices:
                if device != None:
                    usbDevice = usb.core.find(idVendor=device.idVendor, idProduct=device.idProduct)
                    print("{2}, {3} ({0:04x}, {1:04x})".format(usbDevice.idVendor, usbDevice.idProduct, usbDevice.manufacturer, usbDevice.product))
                    for conf in usbDevice:
                        print("  conf #:{0}, num of interfaces: {1}".format(conf.bConfigurationValue, conf.bNumInterfaces))                        
                        for intf in conf:
                            print("    #int:{0} #endpoints: {1}".format(intf.bInterfaceNumber, intf.bNumEndpoints))

        if verbose:
            for bus in usb.busses():
                for device in bus.devices:
                    if device != None:
                        usbDevice = usb.core.find(idVendor=device.idVendor, idProduct=device.idProduct)
                        print(usbDevice)

    def __init__(self, idVendor=None, idProduct=None, interfaceNumber=0, defaultEndPoints=(0, 1)):
        CommunicationPort.__init__(self)

        self.device = usb.core.find(idVendor=idVendor)
        if self.device is None:
            raise IOError("Can't find device")

        self.device.set_configuration()
        self.configuration = self.device.get_active_configuration()

        self.interface = self.configuration[(interfaceNumber,0)]
        
        self.defaultOutputEndPoint = self.interface[defaultEndPoints[0]]
        self.defaultInputEndPoint = self.interface[defaultEndPoints[1]]

        self.portLock = RLock()
        self.transactionLock = RLock()

    @property
    def isOpen(self):
        if self.mainOutputEP is None:
            return False    
        else:
            return True    

    def open(self):
        return

    def close(self):
        return

    def bytesAvailable(self) -> int:
        return 0

    def flush(self):
        return

    def readData(self, length, endPoint=None) -> bytearray:
        if endPoint is None:
            inputEndPoint = self.defaultInputEndPoint
        else:
            inputEndPoint = self.interface[endPoint]

        with self.portLock:
            maxPacket = inputEndPoint.wMaxPacketSize
            data = array.array('B',[0]*maxPacket)
            nBytesRead = inputEndPoint.read(size_or_buffer=data)
            return bytearray(data[:nBytesRead])

    def writeData(self, data, endPoint=None) -> int:
        if endPoint is None:
            outputEndPoint = self.defaultOutputEndPoint
        else:
            outputEndPoint = self.interface[endPoint]

        with self.portLock:
            nBytesWritten = outputEndPoint.write(data)
            if nBytesWritten != len(data):
                raise IOError("Not all bytes written to port")

        return nBytesWritten

    def readString(self, endPoint=None) -> str:      
        if endPoint is None:
            inputEndPoint = self.defaultInputEndPoint
        else:
            inputEndPoint = self.interface[endPoint]

        while True:
            maxPacket = inputEndPoint.wMaxPacketSize
            data = self.readData(length=maxPacket, endPoint=endPoint)
            if data[-1] != 10: # How to write?
                raise ValueError("Not a string {0}, {1}".format(data, data[-1]))
        
            return data.decode(encoding='utf-8')

class DebugEchoCommunicationPort(CommunicationPort):
    def __init__(self, delay=0):
        self.buffer = bytearray()
        self.delay = delay
        self._isOpen = False
        super(DebugEchoCommunicationPort, self).__init__()

    @property
    def isOpen(self):
        return self._isOpen    

    def open(self):
        if self._isOpen:
            raise Exception()

        self._isOpen = True
        return

    def close(self):
        self._isOpen = False
        return

    def bytesAvailable(self):
        return len(self.buffer)

    def flush(self):
        self.buffer = bytearray()

    def readData(self, length):
        with self.portLock:
            time.sleep(self.delay*random.random())
            data = bytearray()
            for i in range(0, length):
                if len(self.buffer) > 0:
                    byte = self.buffer.pop(0)
                    data.append(byte)
                else:
                    raise CommunicationReadTimeout("Unable to read data")

        return data

    def writeData(self, data):
        with self.portLock:
            self.buffer.extend(data)

        return len(data)
