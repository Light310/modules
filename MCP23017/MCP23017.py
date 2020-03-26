import time
import datetime
import math
import threading

def set_bit(value, bit):
    return value | (1<<bit)

def clear_bit(value, bit):
    return value & ~(1<<bit)

def change_bit(binary_number, bit, value):
    if value == 0:
        return binary_number & ~(1<<bit)
    else:
        return binary_number | (1<<bit) 


_MCP23017_IODIRA = 0x00
_MCP23017_IODIRB = 0x01
# _MCP23017_IPOLA = const(0x02)
# _MCP23017_GPINTENA = const(0x04)
# _MCP23017_DEFVALA = const(0x06)
# _MCP23017_INTCONA = const(0x08)
# _MCP23017_IOCON = const(0x0A)
# _MCP23017_GPPUA = const(0x0C)
# _MCP23017_GPPUB = const(0x0D)
_MCP23017_GPIOA = 0x12
_MCP23017_GPIOB = 0x13
# _MCP23017_INTFA = const(0x0E)
# _MCP23017_INTFB = const(0x0F)
# _MCP23017_INTCAPA = const(0x10)
# _MCP23017_INTCAPB = const(0x11)
_MCP23017_OLATA = 0x14
_MCP23017_OLATB = 0x15


class MCP23017:
    def __init__(self, bus, address=0x20):
        self.address = address
        self.bus = bus
        
        # Set all GPA and GPB pins as outputs by setting
        # all bits of IODIRA and IODIRB register to 0  
        self.bus.write_byte_data(self.address, _MCP23017_IODIRA, 0x00)
        self.bus.write_byte_data(self.address, _MCP23017_IODIRB, 0x00)
 
        # Set output all output bits to 0        
        self.set_values(0)
    
    def set_a_values(self, binary_values=None):
        if binary_values is not None:
            self.a_values = binary_values
        self.bus.write_byte_data(self.address, _MCP23017_OLATA, self.a_values)
    
    def set_b_values(self, binary_values=None):
        if binary_values is not None:
            self.b_values = binary_values
        self.bus.write_byte_data(self.address, _MCP23017_OLATB, self.b_values)

    def set_values(self, binary_values):
        self.set_a_values(binary_values >> 8)
        self.set_b_values(binary_values & 0b11111111)
    
    def set_pin(self, pin_number, binary_value):
        """
        pin_number   : 0 to 7 means A, 8-15 means B (0-7)
        binary_value : 0 | 1
        """
        if pin_number < 8:
            self.a_values = change_bit(self.a_values, pin_number, binary_value)
            self.set_a_values()
        else:
            self.b_values = change_bit(self.b_values, pin_number - 8, binary_value)
            self.set_b_values()
 
    def __del__(self):
        self.bus.write_byte_data(self.address, _MCP23017_OLATA, 0)
        self.bus.write_byte_data(self.address, _MCP23017_OLATB, 0)


class MCP23017_pwm(threading.Thread):
    """
    !!! WARNING : it cannot be used for some accurate actions, like controlling servos. Made only for LED PWM !!!

    This is not working good at low duty cycle values (lesser than 0.1), cuz python is slow (or my code is bad) =/
    start() starts a thread, which sends values from a_pwm_values and b_pwm_values to mcp, imitating pwm
    duty_cycle 0.2 with frequency 100 means pin will be HIGH for 0.002 sec and LOW for 0.008 sec (or at least
    close to this values)
    """
    def __init__(self, mcp, frequency=100):
        self.mcp = mcp
        self.frequency = frequency
        self.cycle_time = 1.0 / frequency
        self.terminated = False
        self.toTerminate = False
        self.a_pwm_values = [0 for x in range(8)]
        self.b_pwm_values = [0 for x in range(8)]

    def start(self):
        self.thread = threading.Thread(None, self.run, None, (), {})
        self.thread.start()

    def change_duty_cycle_b(self, values_array):
        self.b_pwm_values = [min(1.0, x) for x in values_array]

    def change_duty_cycle_a(self, values_array):
        self.a_pwm_values = [min(1.0, x) for x in values_array]

    def change_pin_duty_cycle(self, pin_number, new_cycle):
        new_cycle = min(new_cycle, 1.0)
        if pin_number > 7:
            self.b_pwm_values[pin_number] = new_cycle
        else:
            self.a_pwm_values[pin_number] = new_cycle

    def run(self):
        while self.toTerminate == False:    
            # cycle start time used for calculatation of real required sleep time
            initial_time = datetime.datetime.now()
                     
            binary_registers = list(reversed(self.a_pwm_values)) + list(reversed(self.b_pwm_values))

            # find threshold where signal binary mask changes
            distinct = [x for x in sorted(list(set(self.a_pwm_values + self.b_pwm_values))) if x > 0 and x < 1]

            # turn on all leds with duty cycle > 0            
            binary = eval('0b'+''.join(['1' if x > 0 else '0' for x in binary_registers]))     
            self.mcp.set_values(binary)

            for threshold in distinct:                
                binary = eval('0b'+''.join(['1' if 0 < x < threshold else '0' for x in binary_registers]))
                target_time = initial_time + datetime.timedelta(seconds=threshold * self.cycle_time)

                # sleep until we hit next threshold. Or don't sleep if we're already late                
                td = (target_time - datetime.datetime.now()).total_seconds()
                if td > 0:
                    time.sleep(td)

                self.mcp.set_values(binary)                

            # sleep till the end of the cycle
            target_time = initial_time + datetime.timedelta(seconds=self.cycle_time)
            td = (target_time - datetime.datetime.now()).total_seconds()
            if td > 0:
                time.sleep(td)

        self.terminated = True

    def stop(self):
        # Stops PWM output.
        self.toTerminate = True
        while self.terminated == False:
            # wait for termination
            time.sleep(0.01)

        # turn off all signals
        self.mcp.set_values(0)
    
    def __del__(self):
        self.stop()