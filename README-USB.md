# Understanding the Universal Serial Bus (USB)

You are here because you have an interest in programming hardware devices, and the communication with many of them is through the Universal Serial Bus, or USB. The USB standard is daunting to non-expert for many reasons: it was created to solve problems related to the original serial port RS-232, and if you have not worked with old serial ports, some of the problems USB solves will not be apparent to you or even necessary.  In addition, because it is so general (universal), it needs to provide a solution to many, many different types of devices from mouse pointers to all-in-one printers, USB hubs, ethernet adaptors, etc. Therefore, when you are just trying to understand serial communications for your problem ("I just want to send a command to my XYZ stage!"), all this complexity becomes paralyzing. I hope to help you understand better from the perspective of a non-expert.

Let's start by exploring with Python and PyUSB.

## Installing PyUSB and libusb

I wish we could dive right in.  I really do. If you just want to see what I do, skip and go to the exploration part (First Steps).  But if you want to explore on your computer too, then you need to install PyUSB and libusb.

This should be simple: `pip install pyusb`. But then, you need to install `libusb`, which is the actual engine that talks to the USB port on your computer, and PyUSB needs to know where it is.  Libusb is an open source library that has been adopted by many developers because it is complete, bug-free and cross-platform, and without it, PyUSB will not work. You can also use Zadig on Windows to install it or brew on macOS. It may already be installed on your computer.

```
pip install pyusb
```

On macOS and Linux:

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install libusb
```

On Windows, get [Zadig](https://zadig.akeo.ie) and keep for fingers crossed. Worse comes to worst, the simplest solution is to [download](https://libusb.info) it and keep `libusb-1.0.x.dll` in the directory where you expect to work (for now). Don't get me started on DLLs on Windows.

## First steps

Your computer has a USB bus, that is, a main entry point through which all USB devices that you connect will communicate. When you plug in a device, it will automatically provide basic information to identify itself. That information is hardcoded into the device and informs the computer what it is and what it can do. So the first thing we want is to list all devices currently connected to your computer through your USB bus (or busses, some computers have more than one):

```python
import usb.core
import usb.util

for bus in usb.busses():
    for device in bus.devices:
        if device != None:
            usbDevice = usb.core.find(idVendor=device.idVendor, 
                                      idProduct=device.idProduct)
            print(usbDevice)
```

I connected a Kensington Wireless presenter and Laser pointer.  I get the following **USBDescriptor**, which I commented for clarity:

```python
DEVICE ID 047d:2012 on Bus 020 Address 001 =================
 bLength                :   0x12 (18 bytes)              # The length in bytes of this description
 bDescriptorType        :    0x1 Device                  # This is a USB Device Descriptor
 bcdUSB                 :  0x200 USB 2.0                 # What USB standard it complies to
 bDeviceClass           :    0x0 Specified at interface  # A class of device (here, not known yet)
 bDeviceSubClass        :    0x0                         # A subclass of device (here, not known yet)
 bDeviceProtocol        :    0x0                         # A device protocol (here, not known yet)
 bMaxPacketSize0        :    0x8 (8 bytes)               # The size of packets that will be transmitted
 idVendor               : 0x047d                         # The USB Vendor ID.  This is Kensington.
 idProduct              : 0x2012                         # The USB Product ID.  This pointer device.
 bcdDevice              :    0x6 Device 0.06              
 iManufacturer          :    0x1 Kensington              # The text description of the manufacturer
 iProduct               :    0x3 Wireless Presenter with Laser Pointer # Text name of product
 iSerialNumber          :    0x0                         # The text description of the serial number 
 bNumConfigurations     :    0x1                         # The number of USB configurations

```

Let's highlight what is important:

1. First: numbers written 0x12, 0x01 etc... are hexadecimal numbers, or numbers in base 16. Each "digit" can take one of 16 values: 0-9, then a to f representing 10 to 15. Therefore,  0x12 is 1 x 16 + 2 = 18 dec.  Lowercase or uppercase are irrelevant.  Up to 9, decimal and hexadecimal are the same.
2. The **vendor id** is unique to the vendor of this device.  This value is registered with the USB consortium for a small cost. We can use this later to get "all devices from Kensington".
3. The **product id** is unique to a product, from Kensington.  The vendor manages their product ids as they wish.
4. The **bNumConfigurations** is the number of possible configurations this USB device can take. It will generally be 1 with scientific equipment, but it can be more than that. We will simply assume it is always 1 for the rest of the present discussion, this is not a vital part for us.
5. Don't worry about the letters (b, i, bcd) in front of the descriptors: they simply indicate without ambiguity how they are stored in the USB descriptor: a `b` represents a *byte* value, an `i` represents a *2-byte integer*, and a `bcd` is also a 2-byte integer, but interpreted in decimal (binary-coded-decimal). `bcdUSB`= 0x200 means 2.0.0.

Right after connecting, the device is in an "unconfigured mode". Someone, somewhere needs to take responsibility for this device and do something.  Again, we need to separate general user devices (mouse, printers etc...) from scientific hardware.  With user devices, the device class, subclass, vendor id, product id, and protocol are sufficient for the computer to determine whether or not it can manage it. If the computer has the driver for this device, it will "own" it and manage it.  For instance, the printer is recognized and then the operating system can do what it needs to do with it.  However, scientific equipement will often appear as "General Device", and the computer will likely not know what to do.  This is when we come in.

## Configuring the USB device

We need to set the device into one of its configurations.  As described before, this is most likely just setting the device in its only possible configuration. So we get the USB device using the `usb.core.find` function of PyUSB, which will just relay the request to libusb and return any device that matches the parameters we want. In our case, we specify the idVendor and the idProduct, so the only device that can match is the one we want.

```python
import usb.core
import usb.util

device = usb.core.find(idVendor=0x047d, idProduct=0x2012)  # For a Kensington pointer. Choose yours.
if device is None:
	raise IOError("Can't find device")

device.set_configuration()                        # Use the first configuration
configuration = device.get_active_configuration() # Then get a reference to it
print(configuration)
```

This will print the following **USBConfiguration**, which I am also commenting:

```python
  CONFIGURATION 1: 100 mA ==================================
   bLength              :    0x9 (9 bytes)
   bDescriptorType      :    0x2 Configuration        # This is a USB Configuration descriptor
   wTotalLength         :   0x22 (34 bytes)
   bNumInterfaces       :    0x1                      # It has one "USB interface" (discussed below)
   bConfigurationValue  :    0x1                      # It is configuration number 1 (there is no 0).
   iConfiguration       :    0x0 
   bmAttributes         :   0xa0 Bus Powered, Remote Wakeup
   bMaxPower            :   0x32 (100 mA)
[... more stuff related to interfaces and endpoints ... ]
```

Again, the important aspects.

1. It has a configuration value of 1, which happens to be the only one.
2. It says it has one **USB Interface.**  This is discussed below.
3. The configuration has some technical details, such as the fact it does not need extra power and will require 100 mA or less when connected.

## Choosing a USB interface

The best way to understand **USB interfaces** is to use an example everyone knows: all-in-one printers.  These printers-scanners can act like a printer or a scanner, yet they have a single USB cable. Sometimes they will act like a printer, sometimes they will act like a scanner, and nothing says they can't do both at the same time. The **USB Interface** is the front face or appearance of the device to the computer: the device offers a "printer interface" and a "scanner interface" and depending on what you want to do, you will choose the one you need. So this device has a single interface, let's look at it.  The above code also prints information about the interfaces of the configuration, but I had removed them for simplicity. Here it is:

```python
    INTERFACE 0: Human Interface Device ====================
     bLength            :    0x9 (9 bytes)
     bDescriptorType    :    0x4 Interface              # This is a USB Interface Descriptor
     bInterfaceNumber   :    0x0                        # It has interface number 0. It starts at 0 not 1
     bAlternateSetting  :    0x0
     bNumEndpoints      :    0x1                        # It has a single user-endpoint (will be number 1)
     bInterfaceClass    :    0x3 Human Interface Device # It is a type of Human Device (i.e. manipulatable)
     bInterfaceSubClass :    0x1                        # Can be available on boot
     bInterfaceProtocol :    0x1                        # 1: keyboard, 2: mouse
     iInterface         :    0x0 
[ ... more stuff about endpoints ....]
```

In this particular situation (a Kensington laser pointer), there is a single interface: 

1. The **bInterfaceClass** (0x03) says that if you choose interface #0, then you will be speaking to a Human Interface Device, which typically means keyboard, mouse, etc...  The **bInterfaceSubClass** and protocol are sufficient for the computer to determine whether or not it can manage it.  In this case, the **bInterfaceProtocol** says it acts like a keyboard.  
2. We don't need to dig deeper in Human Interface Devices at this point, but the computer will communicate with the device with accepted protocols on endpoint 0.

## Input and output endpoints

Finally, each USB interface has communication channels, or **endpoints**, that it decides to define for its purpose. An end point is a one-way communication either to the device (OUT) or into the computer (IN).  This Kensington Pointer has a single input enpoint, which means we cannot "talk" to it, we can only "read" from it.  Its description is the following:

```python
      ENDPOINT 0x81: Interrupt IN ==========================
       bLength          :    0x7 (7 bytes)
       bDescriptorType  :    0x5 Endpoint     # This is a USB Endpoint Descriptor
       bEndpointAddress :   0x81 IN           # Input (because of the 0x80) and number 1.
       bmAttributes     :    0x3 Interrupt    # It is an interrupt endpoint
       wMaxPacketSize   :    0x8 (8 bytes)    # Transmists 8 bytes at a time
       bInterval        :    0xa              # Describes how fast the data will come in.

```

The important take home points are:

1. The interface will define user-endpoints (that is, endpoints that the programmer can use to talk to the device).  There are also two implicit (hidden) endpoints called endpoint #0, or the Control Endpoints. These are used to communicate "control" and USB information to the device and for our purpose (we are not making the USB chips that communicates with the device, we only want to talk to the device), then we won't need to worry about it.  We just need to know it's there.  For this reason, endpoints are numbered starting at #1.

2. The endpoints can communicate information in various ways, and most of the time we do not care so much. Here we have an **INTERRUPT** endpoint that will spit out information to the computer whenever needed. That is because it is a keyboard/mouse, so we want to be responsive: it will typically refresh the position or the keys at 100 Hz.

3. My Logitech mouse has a very similar USB Descriptor with very similar parameters, aside from the fact that it delivers only 4 bytes of information:

   ```python
   DEVICE ID 046d:c077 on Bus 020 Address 002 =================
    bLength                :   0x12 (18 bytes)
    bDescriptorType        :    0x1 Device
    bcdUSB                 :  0x200 USB 2.0
    [...]
    idVendor               : 0x046d                 # Logitech 
    idProduct              : 0xc077                 # An old optical mouse
    bcdDevice              : 0x7200 Device 114.0
   [ ... ]
     bNumConfigurations     :    0x1
     CONFIGURATION 1: 100 mA ==================================
      bLength              :    0x9 (9 bytes)
      bDescriptorType      :    0x2 Configuration
   [ ... ]
      bNumInterfaces       :    0x1
      bConfigurationValue  :    0x1
   [ ... ]
       INTERFACE 0: Human Interface Device ====================
        bInterfaceNumber   :    0x0
        bNumEndpoints      :    0x1
        bInterfaceClass    :    0x3 Human Interface Device
        bInterfaceSubClass :    0x1                 # Available on boot
        bInterfaceProtocol :    0x2                 # This is a mouse, not a keyboard
         ENDPOINT 0x81: Interrupt IN ==========================
          bLength          :    0x7 (7 bytes)
          bDescriptorType  :    0x5 Endpoint
          bEndpointAddress :   0x81 IN
          bmAttributes     :    0x3 Interrupt
          wMaxPacketSize   :    0x4 (4 bytes)       # Only 4 bytes are delivered each time
          bInterval        :    0xa
   ```

   

Finally, here is the complete **USBDescriptor** for my HP Envy all-in-one printer.

```python
DEVICE ID 03f0:c511 on Bus 020 Address 001 =================
 bLength                :   0x12 (18 bytes)
 bDescriptorType        :    0x1 Device
 bcdUSB                 :  0x200 USB 2.0
 bDeviceClass           :    0x0 Specified at interface     # The class depends on the interface selected
 bDeviceSubClass        :    0x0
 bDeviceProtocol        :    0x0
 bMaxPacketSize0        :   0x40 (64 bytes)
 idVendor               : 0x03f0
 idProduct              : 0xc511
 bcdDevice              :  0x100 Device 1.0
 iManufacturer          :    0x1 HP
 iProduct               :    0x2 ENVY 4500 series
 iSerialNumber          :    0x3 CN47Q1329D05X4
 bNumConfigurations     :    0x1
  CONFIGURATION 1: 2 mA ====================================
   bLength              :    0x9 (9 bytes)
   bDescriptorType      :    0x2 Configuration
   wTotalLength         :   0x9a (154 bytes)
   bNumInterfaces       :    0x3
   bConfigurationValue  :    0x1
   iConfiguration       :    0x0 
   bmAttributes         :   0xc0 Self Powered
   bMaxPower            :    0x1 (2 mA)
    INTERFACE 0: Vendor Specific ===========================
     bLength            :    0x9 (9 bytes)
     bDescriptorType    :    0x4 Interface
     bInterfaceNumber   :    0x0
     bAlternateSetting  :    0x0
     bNumEndpoints      :    0x3
     bInterfaceClass    :   0xff Vendor Specific               # The vendor is using its own protocol
     bInterfaceSubClass :   0xcc                               # which you may know or not. I am guessing
     bInterfaceProtocol :    0x0                               # this is the scanner part
     iInterface         :    0x0 
      ENDPOINT 0x1: Bulk OUT ===============================   # 3 endpoints: bulk in/out and interrupt
       bLength          :    0x7 (7 bytes)
       bDescriptorType  :    0x5 Endpoint
       bEndpointAddress :    0x1 OUT
       bmAttributes     :    0x2 Bulk
       wMaxPacketSize   :  0x200 (512 bytes)
       bInterval        :    0x0
      ENDPOINT 0x82: Bulk IN ===============================
       bLength          :    0x7 (7 bytes)
       bDescriptorType  :    0x5 Endpoint
       bEndpointAddress :   0x82 IN
       bmAttributes     :    0x2 Bulk
       wMaxPacketSize   :  0x200 (512 bytes)
       bInterval        :    0x0
      ENDPOINT 0x83: Interrupt IN ==========================
       bLength          :    0x7 (7 bytes)
       bDescriptorType  :    0x5 Endpoint
       bEndpointAddress :   0x83 IN
       bmAttributes     :    0x3 Interrupt
       wMaxPacketSize   :   0x40 (64 bytes)
       bInterval        :    0x7
[ ... ]
    INTERFACE 1: Printer ===================================   
     bLength            :    0x9 (9 bytes)
     bDescriptorType    :    0x4 Interface
     bInterfaceNumber   :    0x1
     bAlternateSetting  :    0x0
     bNumEndpoints      :    0x2                               # Two endpoints
     bInterfaceClass    :    0x7 Printer                       # This is a printer interface
     bInterfaceSubClass :    0x1                               
     bInterfaceProtocol :    0x2
     iInterface         :    0x0 
      ENDPOINT 0x8: Bulk OUT ===============================   # Endpoint number 8 OUT to the printer
       bLength          :    0x7 (7 bytes)
       bDescriptorType  :    0x5 Endpoint
       bEndpointAddress :    0x8 OUT
       bmAttributes     :    0x2 Bulk                          # This is a BULK endpoint
       wMaxPacketSize   :  0x200 (512 bytes)                   # Large 512 bytes each packet
       bInterval        :    0x0
      ENDPOINT 0x89: Bulk IN ===============================   # Endpoint number 9 IN from the printer
       bLength          :    0x7 (7 bytes)
       bDescriptorType  :    0x5 Endpoint
       bEndpointAddress :   0x89 IN
       bmAttributes     :    0x2 Bulk
       wMaxPacketSize   :  0x200 (512 bytes)                   # Large 512 bytes each packet
       bInterval        :    0x0
[ ... ]
    INTERFACE 2: Vendor Specific ===========================   # Yet another interface
     bLength            :    0x9 (9 bytes)
     bDescriptorType    :    0x4 Interface
     bInterfaceNumber   :    0x2
     bAlternateSetting  :    0x0
     bNumEndpoints      :    0x2
     bInterfaceClass    :   0xff Vendor Specific               # Vendor uses its own protocol. Could
     bInterfaceSubClass :    0x4                               # be the scanner or something else.
     bInterfaceProtocol :    0x1
     iInterface         :    0x0 
      ENDPOINT 0xA: Bulk OUT ===============================   # Endpoint #10 (0xa) OUT to the device
       bLength          :    0x7 (7 bytes)
       bDescriptorType  :    0x5 Endpoint
       bEndpointAddress :    0xa OUT
       bmAttributes     :    0x2 Bulk
       wMaxPacketSize   :  0x200 (512 bytes)
       bInterval        :    0x0
      ENDPOINT 0x8B: Bulk IN ===============================   # Endpoint #11 (0xb) IN from the device
       bLength          :    0x7 (7 bytes)
       bDescriptorType  :    0x5 Endpoint
       bEndpointAddress :   0x8b IN
       bmAttributes     :    0x2 Bulk
       wMaxPacketSize   :  0x200 (512 bytes)
       bInterval        :    0x0
[ ... ]
```

Important highlights:

1. As you can see, some USB devices can provide several interfaces and options with many endpoints.  I picked this example to highlight that the USB standard offers a really general solution for device communication, and this is why it was designed and was widely accepted. 
2. There are different types of endpoints: INTERRUPT, BULK, ISOCHRONOUS. Bulk is what we could call a "standard" communication channel for us, experimentalists trying to make things work.  For the most part, we don't really need to worry about it.





## References

I have found various web sites over the years that may help you understand better, even though everything I wrote above is from experience accumulated over the years. Many web sites are either too detailed or too superficial. It is hard to find reasonable information, but I like the following:

1. https://www.beyondlogic.org/usbnutshell/usb1.shtml
