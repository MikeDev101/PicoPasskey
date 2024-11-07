import time
import board
import busio
import digitalio

class EZ_Uart:
    def __init__(self, on_start, on_msg, on_close):
        self.uart = None
        self.running = False
        self.power = digitalio.DigitalInOut(board.GP7)
        self.power.direction = digitalio.Direction.OUTPUT

        # Specify callbacks
        self.on_start = on_start
        self.on_msg = on_msg
        self.on_close = on_close
        
        # Define timeouts
        self.power_delay = 1
        self.max_timeout = 0.1
        
        # Count number of failed init attempts, and reboot into debug mode if = 3
        self.failed_attempts = 0
        
    def clean(self, payload, allow_garbage=False):
        if payload is None:
            return ""
        
        # Convert to string (built-in .decode() doesn't have an option to ignore decode errors)
        decoded = ''.join(map(lambda x: chr(x), payload))
        
        if not allow_garbage:
            # Filter out non-readable characters
            printable = set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r\x0b\x0c")
            decoded = "".join(filter(lambda x: x in printable, decoded))
        
        decoded = decoded.rstrip("\r\n")
        
        return decoded
        
    def failed(self, reason):
        print("FAILED "+reason)
        self.failed_attempts += 1
        self.close()

    def start(self, baud):
        self.running = True

        # Initialize the UART interface
        self.uart = busio.UART(
            tx = board.GP0,
            rx = board.GP1,
            baudrate = baud,
            bits=8,
            timeout=self.max_timeout
        )
        
        # Initialize power control
        self.power.value = True
        print("POWER ON")
        time.sleep(self.power_delay)
        
        # Run a quick diagnostic check
        self.tx("AT")
        print("SELF TEST... ", end="")
        
        result = self.rx(False)
        
        if "OK" not in result:
            self.failed("NOT OK ("+ result + ")")
            return False
        else:
            print("PASSED")
        
        # Run startup script
        if self.on_start is not None:
            self.on_start()
            
        return True

    def close(self):
        if self.running:
            # Shutdown UART interface
            self.uart.deinit()
            self.uart = None
            self.running = False
            
            # Power down
            print("POWER OFF")
            self.power.value = False
            time.sleep(self.power_delay)
            
            # Run close script
            if self.on_close is not None:
                self.on_close()

    def rx(self, eventful=False, allow_garbage=False):
        full_msg = ""
        if self.running:
            
            # Wait a bit
            if self.uart.in_waiting == 0:
                time.sleep(self.max_timeout)
            
            # Read all lines
            while True:
                
                # Repeat reading all lines
                if self.uart.in_waiting > 0:
                   full_msg += self.clean(self.uart.readline(), allow_garbage)
                
                # Stop if there is nothing left in the buffer to read
                if self.uart.in_waiting == 0:
                   break

            if eventful:
                # Run message script
                if self.on_msg is not None:
                    self.on_msg(full_msg, self)
            else:
                return full_msg
        else:
            return None

    def tx(self, msg):
        if self.running:
            self.uart.write(msg)