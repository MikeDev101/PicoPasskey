import time
import board
import digitalio
import usb_hid
import json
import microcontroller as uc

from ez_uart import EZ_Uart

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS

version = "PicoPasskey Firmware v0.1.2"
emergency_mode = uc.nvm[1]
poweroff = False

# Configure keyboard layout
kbd = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(kbd)

# Diagnostic CPU LED
cpu_led = digitalio.DigitalInOut(board.GP25)
cpu_led.direction = digitalio.Direction.OUTPUT

def blink(n, ms_on, ms_off=None):
    for x in range(n):
        
        cpu_led.value = True
        
        if ms_off is None:
            time.sleep((ms_on/1000)/2)
        else:
            time.sleep(ms_on/1000)
        
        cpu_led.value = False
        
        if ms_off is None:
            time.sleep((ms_on/1000)/2)
        else:
            time.sleep(ms_off/1000)

def get_debug(data):
    blink(5, 20)
    uart.tx(str(uc.nvm[0]) + "\r\n")

def get_version(data):
    uart.tx(version + "\r\n")

def set_debug(data):
    value = data.split("AT+SETDEBUG ", 1)
    
    if len(value) != 2:
        uart.tx("ERROR: Missing argument\r\n")
        return
    
    value = value[1]
    
    # Validate input
    temp = None
    try:
        temp = bool(int(value))
    except Exception as e:
        uart.tx("ERROR: Wrong datatype\r\n")
        return
    
    # Update NVRAM
    uc.nvm[0] = temp
    
    # Reboot
    uart.tx("OK\r\n")
    blink(5, 250)
    uc.reset()
    
def force_emergency(data):
    
    # Update NVRAM
    uc.nvm[0] = 1 # Enable debug mode
    uc.nvm[1] = 1 # Set emergency mode flag
    
    # Reboot
    uart.tx("OK\r\n")
    blink(5, 250)
    uc.reset()

def hello():
    blink(5, 20)
    uart.tx("OK\r\n")
    
def quick_reboot(data):
    # Reboot
    uart.tx("OK\r\n")
    blink(5, 250)
    uc.reset()

def send(data):
    
    # read autofill mode
    mode = data.split("AT+FILL ", 1)
    if len(mode) != 2:
        uart.tx("ERROR: Missing arguments")
        return
    
    temp = mode[1].split(" ", 1)
    payload = temp[1]
    mode = temp[0]
    
    # Validate input
    try:
        mode = int(mode)
    except Exception as e:
        uart.tx("ERROR: Wrong mode datatype")
        return
    
    cpu_led.value = True
    
    # mode 0  (or any) - type in the data with no tab or return
    layout.write(payload)
    
    # mode 1 - type with tab
    if mode == 1:
        layout.write("\x09")
    
    # mode 2 - type with return
    elif mode == 2:
        layout.write("\x0a")
    
    blink(3, 100)
    uart.tx("OK\r\n")
    
def shutdown(data):
    global poweroff
    
    # Turn off radio
    uart.tx("OK\r\n")
    blink(3, 100)
    uart.close()
    
    # Turn off CPU led
    cpu_led.value = False
    poweroff = True

def on_msg(msg, uart):
    if len(msg) == 0:
        return
    
    try:
        # dictionary-based switch case
        options = {
            "GETDEBUG": get_debug, # Read debug mode state
            "SETDEBUG": set_debug, # Set debug mode state
            "EMERGENCY": force_emergency, # Force enable emergency mode
            "FILL": send, # Type the data provided as keyboard input
            "VERSION": get_version, # Get version
            "REBOOT": quick_reboot, # Quickly reboot the device
            "OFF": shutdown, # Turn off the device
        }
        
        cmd = msg.split("+", 1)
        
        if len(cmd) == 1:
            if cmd[0] == "AT":
                hello()
            else:
                uart.tx("ERROR: Unknown command")
        else:
            if len(cmd) > 1:
                cmd_noargs = cmd[1].split(" ", 1)[0]
                
                if cmd_noargs in options:
                    options[cmd_noargs](msg)
                else:
                    uart.tx("ERROR: Unknown command")

    except Exception as e:
        uart.tx("ERROR: " + str(e) + "\n")

def on_start():
    print("UART READY")
    cpu_led.value = True
    
    if emergency_mode:
        print("BOOTED IN EMERGENCY MODE")
        print("To reboot the device, use \"reboot\".")
        print("To exit emergency mode and switch to normal debugging mode, use \"exit\".")
        print("To resume normal operation of the device, use \"reset\".")
        print("Otherwise, this prompt will passthrough HC-05/06 AT commands to the radio.")
        blink(5, 1000, 100)
    else:
        print("READY FOR COMMANDS")

def on_close():
    print("UART OFF")
    blink(5, 100, 200)

# Serial bus (HC-05/6)
if __name__ == "__main__":
    print("START")
    uart = EZ_Uart(on_start, on_msg, on_close)
    while not poweroff:
        if uart.start(1200): # AT+BAUD1
            while uart.running:
                
                if emergency_mode:
                    
                    command = input("$: ")
                    
                    if "reset" in command:
                        print("Resuming normal mode...")
                        
                        # Set debug mode off
                        uc.nvm[0] = 0
                        
                        # Unset emergency boot flag
                        uc.nvm[1] = 0
                        
                        # Reboot
                        blink(5, 250)
                        uc.reset()
                        
                    elif "exit" in command:
                        print("Switching to debug mode...")
                        
                        # Unset emergency boot flag
                        uc.nvm[1] = 0
                        
                        # Reboot
                        blink(5, 250)
                        uc.reset()
                        
                    elif "reboot" in command:
                        print("Rebooting...")
                        
                        # Reboot
                        blink(5, 250)
                        uc.reset()
                        
                    else:
                        uart.tx(command)
                        print(uart.rx(False))
                
                else:
                    uart.rx(True, True)
        else:
            if uart.failed_attempts == 3:
                
                # Enable debug mode as an emergency feature
                if not emergency_mode:
                    print("EMERGENCY DEBUG MODE ENABLED")
                    
                    # Set debug mode on
                    uc.nvm[0] = 1
                    
                    # Set emergency boot flag
                    uc.nvm[1] = 1
                    
                    # Reboot
                    blink(5, 250)
                    uc.reset()
