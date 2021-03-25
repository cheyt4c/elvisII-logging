from PyDAQmx import *
from ctypes import *
import numpy as np
from datetime import datetime
from sys import argv
import queue
import threading

data_queue = queue.Queue(maxsize=32)

# how many analog input samples to average over when reading current from the shunt
current_averaging = 10

# resistance of the shunt (ohms)
shunt_resistance = 0.0495

# voltage range to use for DMM
dmm_voltage_range = 10

# voltage range to use for current sensing
shunt_voltage_range = 1.0

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

    num_samples = int(duration*3.48)      # samples occur at roughly 3.48Hz
    print(f"Taking {num_samples} samples")

    # Declaration of variable passed by reference
    vTaskHandle = TaskHandle()
    aTaskHandle = TaskHandle()
    aRead = int32()

    threading.Thread(target=threaded_logging, args=(logfile,), daemon=True).start()

    try:
        # DAQmx Configure Code
        DAQmxCreateTask("",byref(vTaskHandle))
        DAQmxCreateTask("",byref(aTaskHandle))
        
        DAQmxCreateAIVoltageChan(vTaskHandle,b"Dev1/dmm","",DAQmx_Val_Cfg_Default,
                                -dmm_voltage_range,dmm_voltage_range,DAQmx_Val_Volts,None)
        DAQmxCreateAIVoltageChan(aTaskHandle,b"Dev1/ai0","",DAQmx_Val_Cfg_Default,
                                -shunt_voltage_range,shunt_voltage_range,DAQmx_Val_Volts,None)

        # array to store raw current data
        adata = np.zeros(current_averaging, dtype=np.float64)
        voltage = float64()

        # DAQmx Start Code
        DAQmxStartTask(vTaskHandle)
        DAQmxStartTask(aTaskHandle)

        print("--- Starting data capture ---")
        for _ in range(num_samples) :

            # Read current values
            DAQmxStopTask(aTaskHandle)
            DAQmxCfgSampClkTiming(aTaskHandle,"OnboardClock",1.25e6,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,current_averaging)
            DAQmxStartTask(aTaskHandle)
            DAQmxReadAnalogF64(aTaskHandle,-1,1.0,DAQmx_Val_GroupByChannel,adata,current_averaging,byref(aRead),None)
            
            # Read single voltage value
            DAQmxReadAnalogScalarF64(vTaskHandle, timeout=2, value=byref(voltage), reserved=None)
            
            avg_I = np.average(adata)/shunt_resistance
            print(f"V={voltage.value:.3g}V, I={avg_I:.3g}A")
            data_queue.put((datetime.now(), voltage.value, avg_I))

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