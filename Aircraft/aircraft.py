'''
This sample creates "n" flying objects moving in concentric circle on top of Quebec City, Quebec, Canada
Units are lat/long/alt and are converted to geocentric using coreDS builtin Lua scripts
'''

import pathlib
import math
from math import pi
import time #Required for sleep

def points_on_circumference(center=(0, 0), r=50, n=10000):
    return [
        (
            center[0]+(math.cos(2 * pi / n * x) * r),  # x
            center[1] + (math.sin(2 * pi / n * x) * r)  # y

        ) for x in range(0, n + 1)]

def logMessageReceivedFromcoreDS(message, level):
    print(message)

import coreDSPython #Import the coreDS library

centerLatitude = 46.9
centerLongitude =  -71.4

numberOfAircraft = 10

elevation = 1000
r = 0.5

pts = dict()

for number in range(0,numberOfAircraft):
    pts[number] = points_on_circumference(center=(centerLatitude+0.1*number,centerLongitude+0.1*number),r=0.1 * number * r)

# My main coreDS Object
coreDSInstance = coreDSPython.cCoreDS()

#First we have to register the local object and properties known by this federate
# From this system to the simulation framework
# Objects are persistent in time
ObjectOut = coreDSPython.cCoreDSMapping()
ObjectOut.add("FlyingObject", "FlyingObjectX")
ObjectOut.add("FlyingObject", "FlyingObjectY")
ObjectOut.add("FlyingObject", "FlyingObjectZ")
ObjectOut.add("FlyingObject", "Name")

MessageIn = coreDSPython.cCoreDSMapping()
MessageIn.add("Explosion", "TargetObjectID")
MessageIn.add("Fire", "TargetObjectID")

ioconfig = coreDSPython.CVariant()

# Set the script locations
# For this sample, we assume the scripts are located in the current folder
# But the scripts are also provided at the module level so you could use them instead
# os.path.dirname(coreDSPython.__file__) + "/Script"
ioconfig["ScriptFolderLocation.Private"] = str(pathlib.Path(__file__).parent.resolve().absolute()) + "\\Script_Priv"
ioconfig["ScriptFolderLocation.Public"] = str(pathlib.Path(__file__).parent.resolve().absolute()) + "\\Script"

#Set the configuration files location
ioconfig["ConfigFolderLocation"] = str(pathlib.Path(__file__).parent.resolve().absolute())

#Setup logging, logging to SDTOutput is disabled in favor of the Error Callabck
ioconfig["LogToStdOutput.Format"] = "[%TimeStamp%]: %Message%";
ioconfig["LogToStdOutput.Filter"] = "%Severity% >= error";
ioconfig["LogToStdOutput.AutoFlush"] = True
ioconfig["LogToStdOutput.Enabled"] = False

# This will pipe all the logging to the logMessageReceivedFromcoreDS function
ioconfig["LogToInternal.Format"] = "[%TimeStamp%]: %Message%";
ioconfig["LogToInternal.Filter"] = "%Severity% >= error";
ioconfig["LogToInternal.Enabled"] = True

#MaxVerbose will make the to export the verbose level to all coreDS Submodules
# Even if some loggers use a different verbose level
ioconfig["MaxVerbose"] = "%Severity% >= error";

coreDSInstance.registerErrorHandler(logMessageReceivedFromcoreDS)

## Function handler. This is the second way to receive information from the simulation framework
## You can either register a function call back of a callable object with coreDS
## This function will be called whenever a GroundVehicule is updated (based on the current mapping)
def explosionReceived(messagename, values):
    # This function is called when new values are available for the given "object type"
    # This is a sample - you will have to add more code to support
    # multiple instance or multiple object type
    print("Boom received at location explosionReceived", values) 
   

coreDSInstance.registerMessageReceivedHandler("Explosion", explosionReceived)
coreDSInstance.registerMessageReceivedHandler("Fire", explosionReceived)

#We show the configuration UI
coreDSInstance.showConfigHelper(ioconfig, coreDSPython.cCoreDSMapping(), ObjectOut, MessageIn, coreDSPython.cCoreDSMapping())

if (ioconfig.exists("ConfigFile") and ioconfig["ConfigFile"].toString() != ""): #A configuration has been activated

    coreDSInstance.initAndConnect(ioconfig) 
    i=0
    while True:
        for number in range(0,numberOfAircraft):
            outputvals = coreDSPython.CVariant()
            outputvals["FlyingObjectX"] = pts[number][i%len(pts[number])][1]
            outputvals["FlyingObjectY"] = pts[number][i%len(pts[number])][0]
            outputvals["FlyingObjectZ"] = elevation
            outputvals["Name"] = "PythonAir" + str(number)

            #Send the object data back to the simulation network (either DIS or HLA, depending on the configuration)
            coreDSInstance.updateObject("MyLocalInstance" + str(number), "FlyingObject", outputvals)
           
            print("Airplane ", "PythonAir" + str(number), "at location sent at location ", outputvals)

            i=i+1
            if (i > len(pts[0])) : #all object have the same number of points
                i = 0

        coreDSInstance.step() # Check for new data from the simulation backend
        time.sleep(0.1) # sleep, no need to flood the network

else:
    print("No coreDS configuration has been loaded - Distributed simulation has been disabled")

#we are done, disconnect and clean up
coreDSInstance.deinit()
