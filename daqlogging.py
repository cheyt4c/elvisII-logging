from PyDAQmx import *
from ctypes import *
import numpy
from datetime import datetime

num_samples = 10
logfile = f"V+I {datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.txt"

# Declaration of variable passed by reference
vTaskHandle = TaskHandle()
aTaskHandle = TaskHandle()
vRead = int32()
aRead = int32()

dataPoints = []     # list of tuples of (datetime, voltage, current)

try:
    # DAQmx Configure Code
    DAQmxCreateTask("",byref(vTaskHandle))
    DAQmxCreateTask("",byref(aTaskHandle))
    
    DAQmxCreateAIVoltageChan(vTaskHandle,"Dev1/ai0","",DAQmx_Val_Cfg_Default,0.0,20.0,DAQmx_Val_Volts,None)
    DAQmxCreateAICurrentChan(aTaskHandle,"Dev1/dmm","",DAQmx_Val_Cfg_Default,-2.0,2.0,DAQmx_Val_Amps,DAQmx_Val_Internal, 1, None)

    voltage = float64()
    current = float64()

    # DAQmx Start Code
    DAQmxStartTask(vTaskHandle)
    DAQmxStartTask(aTaskHandle)

    for _ in range(num_samples) :

        # Read single voltage value
        #DAQmxReadAnalogF64(vTaskHandle,1,10.0,DAQmx_Val_GroupByChannel,vdata,1000,byref(vRead),None)
        DAQmxReadAnalogScalarF64(vTaskHandle, timeout=2, value=byref(voltage), reserved=None)
        
        # Read single current value
        #DAQmxReadAnalogF64(aTaskHandle,1,10.0,DAQmx_Val_GroupByChannel,adata,1000,byref(aRead),None)
        DAQmxReadAnalogScalarF64(aTaskHandle, timeout=2, value=byref(current), reserved=None)

        print(f"V={voltage.value:.2f}V, I={current.value:.5f}A")
        dataPoints.append((datetime.now(), voltage.value, current.value))

    DAQmxStopTask(vTaskHandle)
    DAQmxStopTask(aTaskHandle)
    DAQmxClearTask(vTaskHandle)
    DAQmxClearTask(aTaskHandle)

except DAQError as err:
    print("DAQmx Error: %s"%err)
    if vTaskHandle:
        # DAQmx Stop Code
        DAQmxStopTask(vTaskHandle)
        DAQmxClearTask(vTaskHandle)

    if aTaskHandle:
        # DAQmx Stop Code
        DAQmxStopTask(aTaskHandle)
        DAQmxClearTask(aTaskHandle)
    
    raise err

with open(logfile, "w+") as f:
    f.write("Time\tVoltage (V)\tCurrent (A)\n")
    for line in dataPoints :
        f.write(f"{line[0].isoformat()}\t{line[1]}\t{line[2]}\n")
