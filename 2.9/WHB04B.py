#!/usr/bin/python3
"""
    XHC-WHB04B-4 HAL Component

    Copyright 2020 Mit Zot
    Updated for Python3 to work with LinuxCNC 2.9+ by Len Shelton @ PROBOTIX

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
import sys, usb, time, hal
import ctypes as ctypes
import threading
import linuxcnc


h=hal.component("whb04b")
h.newpin("mpg_cnt", hal.HAL_S32, hal.HAL_OUT)
h.newpin("sel_x", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("sel_y", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("sel_z", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("sel_a", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("inc", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("foverride", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("reset", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("stop", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("start", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("fn", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("step", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("cont", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("macro1", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("macro2", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("macro3", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("macro4", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("macro5", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("macro6", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("macro7", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("macro8", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("macro9", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("macro10", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("feedplus", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("feedminus", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("spindleplus", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("spindleminus", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("machinehome", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("safez", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("workhome", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("spindletog", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("probez", hal.HAL_BIT, hal.HAL_OUT)
h.ready()


stat = linuxcnc.stat()
command = linuxcnc.command()

class Whb04b_struct(ctypes.Structure):
    buff_old = 'buff_old'
    _fields_ = [
                   #/* header of our packet */
                   ("header", ctypes.c_uint16, ),
                   ("seed", ctypes.c_uint8),
                   ("flags", ctypes.c_uint8),
                   #/* work pos */
                   ("x_wc_int", ctypes.c_uint16),
                   ("x_wc_frac", ctypes.c_uint16),
                   ("y_wc_int", ctypes.c_uint16),
                   ("y_wc_frac", ctypes.c_uint16),
                   ("z_wc_int", ctypes.c_uint16),
                   ("z_wc_frac", ctypes.c_uint16),
                   #/* speed */
                   ("feedrate", ctypes.c_uint16),
                   ("sspeed", ctypes.c_uint16),
                   ("padding", ctypes.c_uint8 * 8) ]
                   
                   
p = Whb04b_struct()          
data = None 
showRotary = False
data_old = 0
pendant_is_on = False
def whb_send_display():
    try:
        time.sleep(0.1)
        stat.poll()
        x = round(stat.position[0] - stat.g5x_offset[0] - stat.tool_offset[0], 4)
        y = round(stat.position[1] - stat.g5x_offset[1] - stat.tool_offset[1], 4)
        if stat.rotation_xy != 0:
            t = math.radians(-stat.rotation_xy)
            x = round( x * math.cos(t) - y * math.sin(t), 4)
            y = round( x * math.sin(t) + y * math.cos(t), 4)
        z = round(stat.position[2] - stat.g5x_offset[2] - stat.tool_offset[2], 4)
        a = round(stat.position[3] - stat.g5x_offset[3] - stat.tool_offset[3], 4)
        b = round(stat.position[4] - stat.g5x_offset[4] - stat.tool_offset[4], 4)
        c = round(stat.position[5] - stat.g5x_offset[5] - stat.tool_offset[5], 4)
        if a < 0 : a = 360 + a
        if b < 0 : b = 360 + b
        if c < 0 : c = 360 + c

        p.header = 0xFDFE
        p.seed = 0xFE
        p.flags = 0x01  # 0x00 CON, 0x01 STP, 0x02 empty
            # Displays "CON: <xxx>%" according to feed rotary button position:
            # CON:2%, CON:5%, CON:10%, CON:30%, CON:60%, CON:100%.
            # CON = 0x00,
            # Displays "STP: <x.xxxx>" according to feed rotary button position:
            # STP:0.001, STP:0.01, STP:0.1, STP:1.0.
            # On 60%, 100% or Lead still displays "STP: 1.0" (firmware bug).
            # STEP = 0x01,
            # Displays "MPG: <xxx>%" according to feed rotary button position:
            # MPG:2%, MPG:5%, MPG:10%, MPG:30%, MPG:60%, MPG:100%
            # MPG = 0x02,
            # Displays <xxx%> according to feed rotary button position:
            # 2%, 5%, 10%, 30%, 60%, 100%.
            # PERCENT = 0x03
        if not showRotary:
            p.x_wc_int = int(abs(x))
            p.y_wc_int = int(abs(y))   
            p.z_wc_int = int(abs(z))
            if stat.linear_units == 1:
                p.x_wc_frac = int(round((abs(x) % 1)*10000, -1))
                p.y_wc_frac = int(round((abs(y) % 1)*10000, -1))
                p.z_wc_frac = int(round((abs(z) % 1)*10000, -1))
            else:
                p.x_wc_frac = int((abs(x) % 1)*10000)
                p.y_wc_frac = int((abs(y) % 1)*10000)
                p.z_wc_frac = int((abs(z) % 1)*10000)
            if x < 0 : p.x_wc_frac = p.x_wc_frac | 0x8000
            if y < 0 : p.y_wc_frac = p.y_wc_frac | 0x8000
            if z < 0 : p.z_wc_frac = p.z_wc_frac | 0x8000
        else:
            p.x_wc_int = int(abs(a))
            p.y_wc_int = int(abs(b))   
            p.z_wc_int = int(abs(c))
            p.x_wc_frac = int(round((abs(a) % 1)*10000, -1))
            p.y_wc_frac = int(round((abs(b) % 1)*10000, -1))
            p.z_wc_frac = int(round((abs(c) % 1)*10000, -1))
        p.feedrate = int(stat.feedrate*100.0)
        #p.sspeed = int(stat.spindlerate*100.0)    
        p.sspeed = int(25) 

        buff = ctypes.cast(ctypes.byref(p), ctypes.POINTER(ctypes.c_char * ctypes.sizeof(p)))
        #print(buff.contents.raw)
        if buff.contents.raw != p.buff_old and pendant_is_on:
            #print(" ".join(hex(ord(c)) for c in buff.contents.raw))
            dev.ctrl_transfer(0x21, 0x09, 0x306, 0x00, bytes(chr(0x06), 'utf-8') + buff.contents.raw[0:7])
            dev.ctrl_transfer(0x21, 0x09, 0x306, 0x00, bytes(chr(0x06), 'utf-8') + buff.contents.raw[7:14])
            dev.ctrl_transfer(0x21, 0x09, 0x306, 0x00, bytes(chr(0x06), 'utf-8') + buff.contents.raw[14:21])
            #dev.ctrl_transfer(0x21, 0x09, 0x306, 0x00, chr(0x06) + buff.contents.raw[21:28])
            #dev.ctrl_transfer(0x21, 0x09, 0x306, 0x00, chr(0x06) + buff.contents.raw[28:35])
            p.buff_old = buff.contents.raw

    except Exception as e:
        print(str(e))
        print("XHC-WHB04: Error writing data!") 
                
                
def mdi_macro(m, axis, fn):
    if m:
        command.mode( linuxcnc.MODE_MDI )
        command.mdi("O<whb_macro_%i> call [%i] [%i]" %(m, axis, fn)  )
        print('XHC-WHB04: executing MDI "O<whb_macro_%i> call [%i] [%i]"' %(m, axis, fn))
                
try:
    while 1:
        dev = None
        print('XHC-WHB04: searching for device...')
        while dev == None:
            dev = usb.core.find(idVendor=0x10ce, idProduct=0xeb93)
            time.sleep(1)

        try:
            if dev.is_kernel_driver_active(0) is True:
                dev.detach_kernel_driver(0)
        except usb.core.USBError as e:
            print("XHC-WHB04: Kernel driver won't give up control over device: %s" % str(e))

        try:
            dev.set_configuration()
            dev.reset()
        except usb.core.USBError as e:
            print("XHC-WHB04: Cannot set configuration: %s" % str(e))

        endpoint = dev[0][(0,0)][0]
        print('XHC-WHB04: Device connected!')

        thread_update_display = threading.Thread(target=whb_send_display, args=())
        thread_mdi_command = threading.Thread(target=mdi_macro, args=(0, 0, 0))
        while 1:    
         try:  
            if not thread_update_display.is_alive():
                thread_update_display = threading.Thread(target=whb_send_display, args=())
                thread_update_display.start()               

            data = dev.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize, timeout=5000)
            #print(data)

            if stat.interp_state == linuxcnc.INTERP_IDLE  and stat.task_mode != linuxcnc.MODE_MANUAL:
                command.mode( linuxcnc.MODE_MANUAL )
            
            # data[5] is axis selector
            h.sel_x = data[5] == 17
            h.sel_y = data[5] == 18
            h.sel_z = data[5] == 19
            h.sel_a = data[5] == 20
            showRotary = data[5] > 19
            pendant_is_on = data[5] > 16
            
            # data[4] is the incerment knob
            if data[4] == 13:   h.inc = 0.001
            elif data[4] == 14: h.inc = 0.01
            elif data[4] == 15: h.inc = 0.1
            elif data[4] == 16: h.inc = 1.0     # 1.0
            else:               h.inc = 0.0

            if data[4] == 13:   h.foverride = 2
            elif data[4] == 14: h.foverride = 5
            elif data[4] == 15: h.foverride = 10
            elif data[4] == 16: h.foverride = 30     # 1.0
            elif data[4] == 26: h.foverride = 60     # 60%
            elif data[4] == 27: h.foverride = 100    # 100%
            elif data[4] == 155: h.foverride = 0     # Lead
            else:               h.inc = 0.0

            #$print str(data[4])
            # inches = 0.0393700787402
            # mm = 1.0
            #if stat.linear_units != 1: h.inc = h.inc / 10.0 
            
            if data[2] == 12 or data[3] == 12: #function
                h.feedplus      = data[2] == 4 or data[3] == 4
                h.feedminus     = data[2] == 5 or data[3] == 5
                h.spindleplus   = data[2] == 6 or data[3] == 6
                h.spindleminus  = data[2] == 7 or data[3] == 7 
                h.machinehome   = data[2] == 8 or data[3] == 8  
                h.safez         = data[2] == 9 or data[3] == 9 
                h.workhome      = data[2] == 10 or data[3] == 10  
                h.spindletog    = data[2] == 11 or data[3] == 11  
                h.probez        = data[2] == 13 or data[3] == 13     
            else:
                h.reset         = data[2] == 1 or data[3] == 1
                h.stop          = data[2] == 2 or data[3] == 2
                h.start         = data[2] == 3 or data[3] == 3
                h.fn            = data[2] == 12 or data[3] == 12           
                h.step          = data[2] == 15 or data[3] == 15
                h.cont          = data[2] == 14 or data[3] == 14
                h.macro1        = data[2] == 4 or data[3] == 4
                h.macro2        = data[2] == 5 or data[3] == 5
                h.macro3        = data[2] == 6 or data[3] == 6
                h.macro4        = data[2] == 7 or data[3] == 7
                h.macro5        = data[2] == 8 or data[3] == 8
                h.macro6        = data[2] == 9 or data[3] == 9
                h.macro7        = data[2] == 10 or data[3] == 10
                h.macro8        = data[2] == 11 or data[3] == 11
                h.macro9        = data[2] == 13 or data[3] == 13
                h.macro10       = data[2] == 16 or data[3] == 16
            
            # data[6] is the encoder  
            # 1-127 is positive, 255-128 is negative        
            if data[6] > 127: h.mpg_cnt = h.mpg_cnt-(256 - data[6])
            else:             h.mpg_cnt = h.mpg_cnt+data[6]
            
            # cool that this works, but should probably be done in HAL
            # if h.reset: command.abort()
            
            if data[2] + data[3] != data_old:
                data_old = data[2] + data[3]
                if not thread_mdi_command.is_alive() and stat.interp_state == linuxcnc.INTERP_IDLE:
                    thread_mdi_command = threading.Thread(target=mdi_macro, args=(0,0,0))
                    if h.macro1: thread_mdi_command = threading.Thread(target=mdi_macro, args=(1, data[5], h.fn))
                    if h.macro2: thread_mdi_command = threading.Thread(target=mdi_macro, args=(2, data[5], h.fn))
                    if h.macro3: thread_mdi_command = threading.Thread(target=mdi_macro, args=(3, data[5], h.fn))
                    if h.macro4: thread_mdi_command = threading.Thread(target=mdi_macro, args=(4, data[5], h.fn))
                    if h.macro5: thread_mdi_command = threading.Thread(target=mdi_macro, args=(5, data[5], h.fn))
                    if h.macro6: thread_mdi_command = threading.Thread(target=mdi_macro, args=(6, data[5], h.fn))
                    if h.macro7: thread_mdi_command = threading.Thread(target=mdi_macro, args=(7, data[5], h.fn))
                    if h.macro8: thread_mdi_command = threading.Thread(target=mdi_macro, args=(8, data[5], h.fn))
                    if h.macro9: thread_mdi_command = threading.Thread(target=mdi_macro, args=(9, data[5], h.fn))
                    if h.macro10: thread_mdi_command = threading.Thread(target=mdi_macro, args=(10, data[5], h.fn))
                    thread_mdi_command.start()

         except usb.core.USBError as e:
            h.sel_x = 0
            h.sel_y = 0
            h.sel_z = 0
            h.sel_a = 0
            h.inc = 0.0
            h.reset = 0
            h.stop = 0
            h.start = 0
            h.fn = 0
            h.step = 0
            h.cont = 0
            h.macro1 = 0
            h.macro2 = 0
            h.macro3 = 0
            h.macro4 = 0
            h.macro5 = 0
            h.macro6 = 0
            h.macro7 = 0
            h.macro8 = 0
            h.macro9 = 0
            h.macro10 = 0
            h.feedplus = 0
            h.feedminus = 0
            h.spindleplus = 0
            h.spindleminus = 0
            h.machinehome = 0
            h.safez = 0
            h.workhome = 0
            h.spindletog = 0
            h.probez = 0
            if e.errno != 110: # 110 is a timeout.
             print ("XHC-WHB04: Error readin data: %s" % str(e))
             usb.util.dispose_resources(dev)
             time.sleep(1)
             break


except KeyboardInterrupt:
    usb.util.dispose_resources(dev)
    raise SystemExit
