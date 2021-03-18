from PyDAQmx import *
from ctypes import *
import numpy as np
from datetime import datetime
from sys import argv
from time import sleep
import queue
import threading

print("Do not use this script. Use Vdmm_shunt instead.")
exit()

data_queue = queue.Queue(maxsize=300)

# resistance of the shunt resistor across ai7, from the LCR reading
shunt_resistance = 0.0490   # ohms
sample_averaging = 10

sample_freq = 6 # Hz

def threaded_logging(logfile) :

    print("Logger started")

    with open(logfile, "w+") as f:
        f.write("Time\tVoltage (V)\tCurrent (A)\n")

    while True :
        data = data_queue.get()
        with open(logfile, "a") as f:
            f.write(f"{data[0].isoformat()}\t{data[1]:.3g}\t{data[2]:.3g}\n")

def main() :
    
    try :
        logfile = argv[1]
        duration = int(argv[2])
    except Exception :
        print(f"Usage: python {argv[0]} <name of logfile> <number of seconds to test (integer)>")
        exit(0)

    num_samples = int(duration*sample_freq)      # samples occur at roughly 3.48Hz
    print(f"Taking {num_samples} samples")

    # Declaration of variable passed by reference
    vTaskHandle = TaskHandle()
    aTaskHandle = TaskHandle()
    vRead = int32()
    aRead = int32()

    threading.Thread(target=threaded_logging, args=(logfile,), daemon=True).start()

    try:
        # DAQmx Configure Code
        DAQmxCreateTask("",byref(vTaskHandle))
        DAQmxCreateTask("",byref(aTaskHandle))
        
        DAQmxCreateAIVoltageChan(vTaskHandle,b"Dev1/ai0","",DAQmx_Val_Cfg_Default,-10,10.0,DAQmx_Val_Volts,None)
        DAQmxCreateAIVoltageChan(aTaskHandle,b"Dev1/ai7","",DAQmx_Val_Cfg_Default,-2,2,DAQmx_Val_Volts,None)

        vdata = np.zeros(sample_averaging, dtype=np.float64)
        adata = np.zeros(sample_averaging, dtype=np.float64)

        for _ in range(num_samples) :

            # Read single voltage value
            DAQmxCfgSampClkTiming(vTaskHandle,"OnboardClock",1.25e6,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,sample_averaging)
            DAQmxStartTask(vTaskHandle)
            DAQmxReadAnalogF64(vTaskHandle,-1,1.0,DAQmx_Val_GroupByChannel,vdata,sample_averaging,byref(vRead),None)
            DAQmxStopTask(vTaskHandle)

            # Read single current value
            DAQmxCfgSampClkTiming(aTaskHandle,"OnboardClock",1.25e6,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,sample_averaging)
            DAQmxStartTask(aTaskHandle)
            DAQmxReadAnalogF64(aTaskHandle,-1,1.0,DAQmx_Val_GroupByChannel,adata,sample_averaging,byref(aRead),None)
            DAQmxStopTask(aTaskHandle)

            avg_V = np.average(vdata)
            avg_I = np.average(adata)/shunt_resistance

            print(f"V={avg_V:.3g}V, I={avg_I:.3g}A")
            data_queue.put((datetime.now(), avg_V, avg_I))

            sleep(1/sample_freq)

    except DAQError as err:
        print("DAQmx Error: %s"%err)
        
        raise err

    finally :

        DAQmxStopTask(vTaskHandle)
        DAQmxStopTask(aTaskHandle)
        DAQmxClearTask(vTaskHandle)
        DAQmxClearTask(aTaskHandle)

if __name__ == "__main__" :
    main()