from sys import argv
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

times = []
voltages = []
currents = []

fig, host = plt.subplots()
par1 = host.twinx()
par2 = host.twinx()

host.set_xlabel("Time (s)")
host.set_ylabel("Power (W)")
par1.set_ylabel("Voltage (V)")
par2.set_ylabel("Current (A)")

try :
    targetFile = argv[1]
except IndexError as e :
    print(f"Usage: python {argv[0]} <file_to_analyse>")
    exit()

with open(targetFile, "r") as f :
    f.readline()    # skip heading

    first_line = f.readline()[:-1].split('\t')      # trim newline
    start_time = datetime.fromisoformat(first_line[0])

    times.append(0)
    voltages.append(float(first_line[1]))
    currents.append(float(first_line[2]))

    for line in f.readlines() :
        line = line[:-1].split('\t')
        times.append( (datetime.fromisoformat(line[0])-start_time).total_seconds() )
        voltages.append( float(line[1]) )
        currents.append( float(line[2]) )

voltage = np.asarray(voltages)
current = np.asarray(currents)
power = voltage*current

print(f"Average power: {np.average(power):.3g}W")
print(f"Peak power: {np.max(power):.3g}W")

p1, = host.plot(times, power, label="Power", color="Red")
p2, = par1.plot(times, voltage, label="Voltage", color="Blue")
p3, = par2.plot(times, current, label="Current", color="Green")

host.legend(handles=[p1,p2,p3], loc='best')
par2.spines['right'].set_position(('outward', 60))

host.yaxis.label.set_color(p1.get_color())
par1.yaxis.label.set_color(p2.get_color())
par2.yaxis.label.set_color(p3.get_color())

fig.tight_layout()

# plt.legend()
# plt.xlabel("Time (s)")
# plt.ylabel("Power (W)")
plt.show()