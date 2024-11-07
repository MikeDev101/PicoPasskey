import usb_midi
import usb_hid
import usb_cdc
import storage
from microcontroller import nvm

# Disable MIDI interface.
usb_midi.disable()

# Only enable HID Keyboard emulation.
usb_hid.enable((usb_hid.Device.KEYBOARD,))
usb_hid.set_interface_name("PicoPasskey")

# Reset NVRAM if this pico has been freshly programmed

# Enable debug by default
if nvm[0] not in [1, 0]:
    nvm[0] = 1 
    
# Reset emergency boot flag by default
if nvm[1] not in [1, 0]:
    nvm[1] = 0 

# Read flags
debug = nvm[0] == 1
emergency = nvm[1] == 1

# Turn on REPL interface if debug or emergency mode
if debug or emergency:
    usb_cdc.enable(console=True, data=False)
else:
    usb_cdc.enable(console=False, data=False)

# Only enable storage interface if debug is turned on
if debug:
    storage.enable_usb_drive()
else:
    storage.disable_usb_drive()