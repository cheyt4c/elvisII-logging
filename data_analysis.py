from sys import argv
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

from scipy.integrate import simps

# power must be above this value to be considered in calculations
power_cutoff = 0.005    # W

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

# Read the file
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
time = np.asarray(times)
power = voltage*current

filtered_power = power[power > power_cutoff]
filtered_voltage = voltage[power > power_cutoff]
filtered_current = current[power > power_cutoff]
filtered_time = time[power > power_cutoff]

print(f"Avg, peak power:\t{np.average(filtered_power):.3g}, {np.max(abs(power)):.3g} W")
print(f"Avg, peak voltage:\t{np.average(filtered_voltage):.3g}, {np.max(abs(voltage)):.3g} V")
print(f"Avg, peak current:\t{np.average(filtered_current):.3g}, {np.max(abs(current)):.3g} A")
print(f"Total energy:\t{simps(filtered_power, filtered_time):.3g}Ws")

# Finish doing the plot
p1, = host.plot(time, power, "-x", label="Power", color="Blue")
p2, = par1.plot(time, voltage, "-x", label="Voltage", color="Red")
p3, = par2.plot(time, current, "-x", label="Current", color="Green")

host.legend(handles=[p1,p2,p3], loc='best')
par2.spines['right'].set_position(('outward', 60))

host.yaxis.label.set_color(p1.get_color())
par1.yaxis.label.set_color(p2.get_color())
par2.yaxis.label.set_color(p3.get_color())

fig.tight_layout()

plt.show()