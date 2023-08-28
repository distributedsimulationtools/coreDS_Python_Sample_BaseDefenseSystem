'''
This sample create an flying object an move around in circle with 
coordinate centered over Quebec City, QUebec, Canada
Units are lat/long/alt and are converted to geocentric using coreDS builtin Lua scripts
Incoming coordinates are not converted since we work direclty with them as geocentric coordinates
The outgoing tank position is converted from LLA to geocentric using a lua script.
The outgoing missile position is not converted since already in geocentric
'''

import math
from math import pi
import pathlib
import time
import coreDSPython #Import the coreDS library

def points_on_circumference(center=(0, 0), r=50, n=100):
    return [
        (
            center[0]+(math.cos(2 * pi / n * x) * r),  # x
            center[1] + (math.sin(2 * pi / n * x) * r)  # y

        ) for x in range(0, n + 1)]

def calculateDistance(x1, x2, y1,y2, z1, z2):
    return math.sqrt((x1-x2)**2 + (y1-y2)**2 + (z1-z2)**2)
    
## This is the second way to get information back from the simulation framework, 
## using a callable object it is possible to manage each kind of object inside it's own manager
class AircraftManager:
    def __init__(self, localUniqueObjectIdentifier=None, objectType=None, values=None):
        if values is None :
            self.aircraftList = {}
    
    def __call__(self, localUniqueObjectIdentifier, objectType, values):
        ## Add the latest values to the discovered aircraft list   
        self.aircraftList[localUniqueObjectIdentifier] = {}
            
        self.aircraftList[localUniqueObjectIdentifier]['name'] = objectType
        self.aircraftList[localUniqueObjectIdentifier]['value'] = coreDSPython.CVariant(values) #copy values
                       
centerLatitude = 46.8563684
centerLongitude =  -71.3416925
elevation = 100
r = 0.5

pts = points_on_circumference(center=(centerLatitude,centerLongitude),r=r)

# My main coreDS Object
coreDSInstance = coreDSPython.cCoreDS()

#First we have to register the local object and properties known by this federate
# From this system to the simulation framework
# Objects are persistent in time
ObjectOut = coreDSPython.cCoreDSMapping()
ObjectOut.add("TankObject", "TankObjectX")
ObjectOut.add("TankObject", "TankObjectY")
ObjectOut.add("TankObject", "TankObjectZ")

ObjectOut.add("MissileObject", "MissileObjectX")
ObjectOut.add("MissileObject", "MissileObjectY")
ObjectOut.add("MissileObject", "MissileObjectZ")

ObjectIn = coreDSPython.cCoreDSMapping()
ObjectIn.add("FlyingObject", "FlyingObjectX")
ObjectIn.add("FlyingObject", "FlyingObjectY")
ObjectIn.add("FlyingObject", "FlyingObjectZ")
ObjectIn.add("FlyingObject", "ObjectID")

#Message 
# This will be mapped to DIS MunitionDetonation
MessageOut = coreDSPython.cCoreDSMapping()
MessageOut.add("Explosion", "ExplosionX")
MessageOut.add("Explosion", "ExplosionY")
MessageOut.add("Explosion", "ExplosionZ")
MessageOut.add("Explosion", "TargetObjectID")

ioconfig = coreDSPython.CVariant()

# Set the script locations
# For this sample, we assume the scripts are located in the current folder
# But the scripts are also provided at the module level so you could use them instead
# os.path.dirname(coreDSPython.__file__) + "/Script"
ioconfig["ScriptFolderLocation.Private"] = str(pathlib.Path(__file__).parent.resolve().absolute()) + "\\Script_Priv"
ioconfig["ScriptFolderLocation.Public"] = str(pathlib.Path(__file__).parent.resolve().absolute()) + "\\Script"

#Set the configuration files location
ioconfig["ConfigFolderLocation"] = str(pathlib.Path(__file__).parent.resolve().absolute())

#We show the configuration UI
coreDSInstance.showConfigHelper(ioconfig, ObjectIn, ObjectOut, coreDSPython.cCoreDSMapping(), MessageOut)

if (ioconfig.exists("ConfigFile") and ioconfig["ConfigFile"].toString() != ""): #A configuration has been activated
    
    ##Create a local instance of our AIrcraft Manager
    aircraftManagerObj = AircraftManager()
    
    ## When an object if type "FlyingObject" is updated, call the "AircraftManager" object
    coreDSInstance.registerObjectUpdateHandler( "FlyingObject", aircraftManagerObj)

    #Initialize the connection with HLA or DIS
    coreDSInstance.initAndConnect(ioconfig)

    i=0
    waitActivated = False
    remainingTime = 10
    waitTimerDelay = 1
    stopEverything = False

    #Geocentric coordinates
    currentMissileX = 1397880.8754448488
    currentMissileY = -4139778.091169467
    currentMissileZ = 4630933.356152983

    ident = 0
    launched = False

    #Tank doesn't move
    outputTankCoordinates = coreDSPython.CVariant()
    outputTankCoordinates["TankObjectX"] = centerLongitude
    outputTankCoordinates["TankObjectY"] = centerLatitude
    outputTankCoordinates["TankObjectZ"] = elevation

    while stopEverything==False:
        #Create our tank
        coreDSInstance.updateObject("Tank", "TankObject", outputTankCoordinates) 

        if (aircraftManagerObj.aircraftList != {}):
            if (ident == 0):
                ident = list(aircraftManagerObj.aircraftList.keys())[0]
            
            # At least one aircraft as been found
            # Activate wait for 10 seconds
            waitActivated = True
            
            remainingTime = remainingTime - waitTimerDelay
  
            if (remainingTime <= 0):
                distance = calculateDistance(aircraftManagerObj.aircraftList[ident]['value']["FlyingObjectX"].toDouble(),
                    currentMissileX, aircraftManagerObj.aircraftList[ident]['value']["FlyingObjectY"].toDouble(),
                    currentMissileY, aircraftManagerObj.aircraftList[ident]['value']["FlyingObjectZ"].toDouble(), currentMissileZ)
                    
                print ("Distance before impact " + str(distance))
                
                #Missile is near the aircraft
                if (distance <= 3000):
                    
                    #Destroy our missile
                    coreDSInstance.deleteObject("Missile")
                    
                    #Emit MunitionDetotation message
                    outputvals = coreDSPython.CVariant()
                    outputvals["ExplosionX"] = currentMissileX
                    outputvals["ExplosionY"] = currentMissileY
                    outputvals["ExplosionZ"] = currentMissileZ
                    outputvals["TargetObjectID"] = aircraftManagerObj.aircraftList[ident]['value']["ObjectID"].toInt()

                    coreDSInstance.sendMessage("Explosion", outputvals)

                    #Job done, stop everything
                    stopEverything = True
                else:
                    dx, dy, dz = (aircraftManagerObj.aircraftList[ident]['value']["FlyingObjectX"].toDouble()-currentMissileX,
                         aircraftManagerObj.aircraftList[ident]['value']["FlyingObjectY"].toDouble() - currentMissileY,
                        aircraftManagerObj.aircraftList[ident]['value']["FlyingObjectZ"].toDouble() - currentMissileZ)
   
                    currentMissileX = currentMissileX + (dx/10) 
                    currentMissileY = currentMissileY + (dy/10)
                    currentMissileZ = currentMissileZ + (dz/10)
                    
                    #create the missile and update it's position
                    outputvals = coreDSPython.CVariant()
                    outputvals["MissileObjectX"] = currentMissileX
                    outputvals["MissileObjectY"] = currentMissileY
                    outputvals["MissileObjectZ"] = currentMissileZ
                    coreDSInstance.updateObject("Missile", "MissileObject", outputvals) 
                    
                if (launched == False):
                    #Emit WeaponFire message
                    outputvals = coreDSPython.CVariant()
                    outputvals["ExplosionX"] = currentMissileX
                    outputvals["ExplosionX"] = currentMissileY
                    outputvals["ExplosionX"] = currentMissileZ
                    coreDSInstance.sendMessage("Explosion", outputvals)
                    launched = True
                
        coreDSInstance.step() # Check for new data from the simulation backend
        time.sleep(waitTimerDelay) # sleep, no need to flood the network
        
        if (aircraftManagerObj.aircraftList != {} and remainingTime > -1):
            print ("Aircraft found, launching in " + str(remainingTime))
        
else:
    print("No coreDS configuration has been loaded - Distributed simulation has been disabled")


#we are done, disconnect and clean up
coreDSInstance.deinit()

print("Completed")
