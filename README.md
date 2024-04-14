# whb04b
Whb04b python driver for LinuxCNC

Installation:
- sudo apt-get update
- sudo apt-get install pip
- sudo pip install pyusb
- chmod +x ./whb/whb04b
- Create file /etc/udev/rules.d/90-xhc.rules and add a line in it:
        SUBSYSTEM=="usb", ATTR{idVendor}=="10ce", ATTR{idProduct}=="eb93", MODE="666" 
- sudo udevadm trigger


Updated for LinuxCNC 2.9+ & Python3
- Added secondary function key signals

Installation on LinuxCNC 2.9+:
- install python usb module "sudo apt-get install python3-usb"
- shouldn't need to change udev rules
- place WHB04B.hal WHB04B.py in config folder
- change full path to WHB04B.py in the WHB04B.hal file
- add "HALFILE = WHB04B.hal" in [HAL] section of your ini file

