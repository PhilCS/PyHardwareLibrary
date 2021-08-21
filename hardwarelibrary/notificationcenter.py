from enum import Enum

# You must define notification names like this for simplicity:
# class DeviceNotification(NotificationName):
#    willMove       = "willMove"
#    didMove        = "didMove"
#    didGetPosition = "didGetPosition"

class Notification:
    class Name(Enum):
        pass

    def __init__(self, name, object=None, userInfo=None):
        if not isinstance(name, Notification.Name):
            raise ValueError("You must use an enum-subclass of Notification.Name, not a string for the notification name")

        self.name = name
        self.object = object
        self.userInfo = userInfo

class ObserverInfo:
    def __init__(self, observer, method=None, notificationName=None, observedObject=None):
        self.observer = observer
        self.method = method
        self.observedObject = observedObject
        self.notificationName = notificationName

    def matches(self, otherObserver) -> bool:
        if self.notificationName is not None and otherObserver.notificationName is not None and self.notificationName != otherObserver.notificationName:
            return False
        elif self.observedObject is not None and otherObserver.observedObject is not None and self.observedObject != otherObserver.observedObject:
            return False
        elif self.observer != otherObserver.observer:
            return False
        return True

    def __eq__(self, rhs):
        return self.matches(rhs)

class NotificationCenter:
    _instance = None
    def __init__(self):
        if not hasattr(self, 'observers'):
            self.observers = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    def addObserver(self, observer, method, notificationName=None, observedObject=None):
        if notificationName is not None and not isinstance(notificationName, Notification.Name):
            raise ValueError("You must use an enum-subclass of Notification.Name, not a string for the notificationName")

        observerInfo = ObserverInfo(observer=observer, method=method, notificationName=notificationName, observedObject=observedObject)

        if notificationName not in self.observers.keys():
            self.observers[notificationName.name] = [observerInfo]
        else:
            if observerInfo not in self.observers[notificationName.name]:
                self.observers[notificationName.name].append(observerInfo)

    def removeObserver(self, observer, notificationName=None, observedObject=None):
        if notificationName is not None and not isinstance(notificationName, Notification.Name):
            raise ValueError("You must use an enum-subclass of Notification.Name, not a string for the notificationName")

        observerToRemove = ObserverInfo(observer=observer, notificationName=notificationName, observedObject=observedObject)

        if notificationName is not None:
            self.observers[notificationName.name] = [currentObserver for currentObserver in self.observers[notificationName.name] if not currentObserver.matches(observerToRemove) ]
        else:
            for name in self.observers.keys():
                self.observers[name] = [observer for observer in self.observers[name] if not observer.matches(observerToRemove) ]        

    def postNotification(self, notificationName, notifyingObject, userInfo=None):
        if not isinstance(notificationName, Notification.Name):
            raise ValueError("You must use an enum-subclass of Notification.Name, not a string for the notificationName")

        if notificationName.name in self.observers.keys():
            notification = Notification(notificationName, notifyingObject, userInfo)
            for observerInfo in self.observers[notificationName.name]:
                if observerInfo.observedObject is None or observerInfo.observedObject == notifyingObject:
                    observerInfo.method(notification)

    def observersCount(self):
        count = 0
        for name in self.observers.keys():
            count += len(self.observers[name])
        return count

    def clear(self):
        self.observers = {}
