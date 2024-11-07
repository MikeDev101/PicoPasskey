![PicoPasskey_Icon](https://github.com/user-attachments/assets/07adf39a-e3f2-4170-a7e4-e9de58ac6ea7)

# PicoPasskey
A Raspberry Pi Pico-based bluetooth password typer.

This is a project that I made a long time ago. I put it here for archival purposes. If you feel like continuing development of this incredibly cursed device, go for it.

**This is by no means secure!** It's more of a convenience tool than it is a security device. See my note below.

**You will need an HC-06 Bluetooth Serial Adapter for this to work.** I didn't have a Raspberry Pi Pico W when making this.

# What is this?
You've probably heard of those fancy schmancy USB Rubber Duckies that can autotype things and do all sorts of nasty stuff. 

Now, imagine if you can take advantage of a password manager's autofill feature and type in your login credentials for you (or on machines that you can't install a password manager on, i.e. a work PC).

Combine that with a Raspberry Pi Pico and a Bluetooth serial adapter, and you've got a PicoPasskey.

# Cool. How do I...
* **Flash the firmware** - Install a copy of MicroPython, then copy the files in the `fw` folder to the exposed drive interface. Reboot the device once, then follow further instructions below.
* **Wire things up** - See provided schematics.
* **Autofill my credentials** - Install the provided PicoPasskey.apk app, or use a Bluetooth Serial Terminal app with the instructions provided below.

# What's this PicoPasskey.apk file in the releases?
That's an app I made using Kodular to take advantage of the autofill feature in nearly every password manager you can find. The source code can be found in the `app` folder in this repo.

# How secure is this?
That's the neat part - It isn't. If I actually cared enough about this thing, I would've implemented some form of encryption. I trust that you use this in environments that aren't mission critical. If you feel up to the task, I challenge you to implement some form of encryption on the device!

# Command Set
The PicoPasskey uses a protocol very similar to the Hayes Command Set used in old school dialup modems. Note that the PicoPasskey uses `\r\n` to signify the end of a command/reply.

### Attention
Basically used to check if everything's in working order.

Opcode: `AT`  

Response: `OK`


### Get Debugging Mode State
If `1`, the flash drive interface and debugging serial port is enabled on the Pico (This will be the default mode when you first flash the firmware). Otherwise, the Pico will disable all peripherals and operates in HID Keyboard only mode.

Opcode: `AT+GETDEBUG`  

Response: `1` or `0`

### Emergency Mode
If for any reason the Pico fails to talk to the Bluetooth Serial Adapter 3 times, it will turn on emergency mode, which will set the debugging mode flags and allow you to safely recover your Pico.

Opcode: `AT+GETDEBUG`  

Response: `OK` and a reboot

### Set Debugging Mode
If you feel like tinkering around, use this command to show/hide the flash drive and debugging serial interfaces.

Opcode: `AT+SETDEBUG 1` or `AT+SETDEBUG 0`  

Response: `OK` and a reboot

### Autofill
Here's the good part. You can ask it to "just type this thing", "type it and tab to the next input field" or "type it and submit". 

Opcodes:

> Just fill data:  
> `AT+FILL 0 (credential)`

> Fill with tab:  
> `AT+FILL 1 (credential)` 

> Fill with return:  
> `AT+FILL 2 (credential)`

Response: `OK` 

### Get Firmware Version
Mainly a convenience feature.

Opcode: `AT+VERSION`

Response: `PicoPasskey Firmware v0.1.2`
