from PyDAQmx import *
from ctypes import *
import numpy as np
from datetime import datetime
from sys import argv
import queue
import threading

data_queue = queue.Queue(maxsize=32)

# number of samples to average over when taking voltage reading
voltage_averaging = 10

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
    vRead = int32()

    threading.Thread(target=threaded_logging, args=(logfile,), daemon=True).start()

    try:
        # DAQmx Configure Code
        DAQmxCreateTask("",byref(vTaskHandle))
        DAQmxCreateTask("",byref(aTaskHandle))
        
        DAQmxCreateAIVoltageChan(vTaskHandle,b"Dev1/ai0","",DAQmx_Val_Cfg_Default,-10,10.0,DAQmx_Val_Volts,None)
        DAQmxCreateAICurrentChan(aTaskHandle,b"Dev1/dmm","",DAQmx_Val_Cfg_Default,-2.0,2.0,DAQmx_Val_Amps,DAQmx_Val_Internal, 1, None)

        # data to read in voltage values
        vdata = np.zeros(voltage_averaging, dtype=np.float64)
        current = float64()

        # DAQmx Start Code
        DAQmxStartTask(vTaskHandle)
        DAQmxStartTask(aTaskHandle)

        for _ in range(num_samples) :

            # Read voltage values
            DAQmxStopTask(vTaskHandle)
            DAQmxCfgSampClkTiming(vTaskHandle,"OnboardClock",1.25e6,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,voltage_averaging)
            DAQmxStartTask(vTaskHandle)
            DAQmxReadAnalogF64(vTaskHandle,-1,1.0,DAQmx_Val_GroupByChannel,vdata,voltage_averaging,byref(vRead),None)
            
            # Read single current value
            DAQmxReadAnalogScalarF64(aTaskHandle, timeout=2, value=byref(current), reserved=None)
            
            avg_V = np.average(vdata)
            print(f"V={avg_V:.3g}V, I={current.value:.3g}A")
            data_queue.put((datetime.now(), avg_V, current.value))

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