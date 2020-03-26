import smbus
import time
from MCP23017 import MCP23017

bus = smbus.SMBus(1)
mcp = MCP23017(bus)

# set pin 0 (A0) to High
mcp.set_pin(0, 1)
time.sleep(1)

# set pin 8 (B0) to High
mcp.set_pin(8, 1)
time.sleep(1)

# set A0 and A2 to High
mcp.set_a_values(0b00000101)
time.sleep(1)

# set B0 - B7 to Low
mcp.set_a_values(0b00000000)
time.sleep(1)