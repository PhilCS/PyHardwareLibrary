from enum import Enum, IntEnum
import typing
import numpy as np
from hardwarelibrary.notificationcenter import NotificationCenter, Notification

class DeviceState(IntEnum):
    Unconfigured = 0 # Dont know anything
    Ready = 1        # Connected and initialized
    Recognized = 2   # Initialization has succeeded, but currently shutdown
    Unrecognized = 3 # Initialization failed

class PhysicalDeviceNotification(Notification.Name):
    willInitializeDevice       = "willInitializeDevice"
    didInitializeDevice        = "didInitializeDevice"
    willShutdownDevice         = "willShutdownDevice"
    didShutdownDevice          = "didShutdownDevice"

class PhysicalDevice:
    class UnableToInitialize(Exception):
        pass
    class UnableToShutdown(Exception):
        pass

    def __init__(self, serialNumber:str, productId:np.uint32, vendorId:np.uint32):
        self.vendorId = vendorId
        self.productId = productId
        self.serialNumber = serialNumber
        self.state = DeviceState.Unconfigured

    def initializeDevice(self):
        if self.state != DeviceState.Ready:
            try:
                NotificationCenter().postNotification(PhysicalDeviceNotification.willInitializeDevice, notifyingObject=self)
                self.doInitializeDevice()
                self.state = DeviceState.Ready
                NotificationCenter().postNotification(PhysicalDeviceNotification.didInitializeDevice, notifyingObject=self)
            except Exception as error:
                self.state = DeviceState.Unrecognized
                NotificationCenter().postNotification(PhysicalDeviceNotification.didInitializeDevice, notifyingObject=self, userInfo=error)
                raise PhysicalDevice.UnableToInitialize(error)

    def doInitializeDevice(self):
        raise NotImplementedError("Base class must override doInitializeDevice()")

    def shutdownDevice(self):
        if self.state == DeviceState.Ready:
            try:
                NotificationCenter().postNotification(PhysicalDeviceNotification.willShutdownDevice, notifyingObject=self)
                self.doShutdownDevice()
                NotificationCenter().postNotification(PhysicalDeviceNotification.didShutdownDevice, notifyingObject=self)
            except Exception as error:
                NotificationCenter().postNotification(PhysicalDeviceNotification.didShutdownDevice, notifyingObject=self, userInfo=error)
                raise PhysicalDevice.UnableToShutdown(error)
            finally:
                self.state = DeviceState.Recognized

    def doShutdownDevice(self):
        raise NotImplementedError("Base class must override doShutdownDevice()")
