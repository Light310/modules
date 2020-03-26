import smbus
import time
from MCP23017 import MCP23017, MCP23017_pwm

bus = smbus.SMBus(1)
mcp = MCP23017(bus)
# don't use PWM unless you really need to
mcp_pwm = MCP23017_pwm(mcp)

# starting PWM
mcp_pwm.start()

a = 0
# set pin A1 from 0 to 100 brightness and back
for i in range(100):
    mcp_pwm.change_pin_duty_cycle(1, a)
    a += 0.01
    time.sleep(0.01)

for i in range(100):
    mcp_pwm.change_pin_duty_cycle(1, a)
    a -= 0.01
    time.sleep(0.01)

# set all pins from 0 to 100 brightness and back 2 times
for j in range(2):
    for i in range(100):
        a += 0.01
        
        mcp_pwm.change_duty_cycle_a([a for _ in range(8)])
        mcp_pwm.change_duty_cycle_b([a for _ in range(8)])
        time.sleep(0.01)

    for i in range(100):
        a -= 0.01    
        mcp_pwm.change_duty_cycle_a([a for _ in range(8)])
        mcp_pwm.change_duty_cycle_b([a for _ in range(8)])
        time.sleep(0.01)

mcp_pwm.stop()
