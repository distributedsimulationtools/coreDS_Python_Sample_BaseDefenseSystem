
import logging
import pathlib
import threading
import time
import pyproj
import numpy as np
from matplotlib import animation
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

import sys
sys.path.append('C:\Program Files\ds.tools\coreDS Python')

import coreDSPython

# Will be updated with first object update
CENTER_LAT = 0
CENTER_LON = 0
SEARCH_RADIUS = 2500  # Search radius in meters

bFirstUpdateReceived = False

fig, ax = plt.subplots()
ax = plt.axes(projection=ccrs.PlateCarree())
ax.stock_img()

# Adding text on the plot.
ax.text(0.05, 0.05, 'Press q to quit', transform=ax.transAxes, style='italic', bbox={
        'facecolor': 'green', 'alpha': 0.5, 'pad': 10})

nodeList = {}

stopEverything = False

# My main coreDS Object
coreDSInstance = coreDSPython.cCoreDS()

#Initialize coreDS defaults
ioconfig = coreDSPython.CVariant()

# Set the script locations
# For this sample, we assume the scripts are located in the current folder
# But the scripts are also provided at the module level so you could use them instead
# os.path.dirname(coreDSPython.__file__) + "/Script"
ioconfig["ScriptFolderLocation.Private"] = str(pathlib.Path(__file__).parent.resolve().absolute()) + "\\Script_Priv"
ioconfig["ScriptFolderLocation.Public"] = str(pathlib.Path(__file__).parent.resolve().absolute()) + "\\Script"

#Set the configuration files location
ioconfig["ConfigFolderLocation"] = str(pathlib.Path(__file__).parent.resolve().absolute())

ioconfig["LogToStdOutput.Format"] = "[%TimeStamp%]: %Message%";
ioconfig["LogToStdOutput.Filter"] = "%Severity% >= error";
ioconfig["LogToStdOutput.AutoFlush"] = True
ioconfig["LogToStdOutput.Enabled"] = True

#ask coreDS to turn the callbacks to Python right away
ioconfig["ReturnMethod"] = 0

#Add a mutex to play nice with async tasks.
lock = threading.Lock()

## This is the first way to get information back from the simulation framework, 
## using a callable object it is possible to manage each kind of object inside it's own manager
class ObjectUpdateManager(coreDSPython.CallbackObjectUpdateHandler):
    def __init__(self):
        super(ObjectUpdateManager, self).__init__()
        self.objectList = {}
        self.ground = 0
        
    def run(self, localUniqueObjectIdentifier, objectType, values):
        ## Add the latest values to the discovered aircraft list
        with lock:
            try:                    
                self.objectList[localUniqueObjectIdentifier] = {}
            
                self.objectList[localUniqueObjectIdentifier]['name'] = objectType

                # Let's use pyproj to convert from geocentric to LLA

                transformer = pyproj.Transformer.from_crs(
                    {"proj":'geocent', "ellps":'WGS84', "datum":'WGS84'},
                    {"proj":'latlong', "ellps":'WGS84', "datum":'WGS84'},
                    )

                lon, lat, alt = transformer.transform(values['Location.X'].toDouble(),values['Location.Y'].toDouble(),values['Location.Z'].toDouble(),radians=False)

                self.objectList[localUniqueObjectIdentifier]['value'] = coreDSPython.CVariant(values) #copy values

                ## Add the LLA information into our CVariant so we can use it later
                self.objectList[localUniqueObjectIdentifier]['value']['lat'] = lat
                self.objectList[localUniqueObjectIdentifier]['value']['lon'] = lon
                self.objectList[localUniqueObjectIdentifier]['value']['alt'] = alt

                print("Received " , objectType, values['Name'], "at location received at location ", self.objectList[localUniqueObjectIdentifier]['value'])

            except Exception as e:
                logging.error(f'{e}. Continuing execution...')

def objectRemoved(objIdentifier):
    with lock:
        try:
            incomingObjManagerObj.objectList.pop(objIdentifier) 
            nodeList[objIdentifier].remove()
            nodeList.pop(objIdentifier)
            print("Removing object id: ", objIdentifier) 
        except:
            pass  

##Create a local instance of our Object Manager
incomingObjManagerObj = ObjectUpdateManager()

## Add a callback handler.
## When an object if type "Object" is updated, call the "AircraftManager" object
coreDSInstance.registerObjectUpdateHandler(incomingObjManagerObj)
coreDSInstance.registerObjectRemovedHandler(objectRemoved)

# Create a function to handle the timer  events. 
timerDelay = 0.01
def onTimer(): 
    global stopEverything
    if not stopEverything:
        _ = coreDSInstance.step() # Check for new data from the simulation backend
        threading.Timer(timerDelay, onTimer).start() 
        
def show_coreDS_ConfigurationWindow():
    # First we have to register the local object / local messages and properties known by this program
    # Input data -> from the simulation to this system
    # Output data -> from this software to the remote simulation
    ObjectIn = coreDSPython.cCoreDSMapping()
    ObjectIn.add("Object", "Location.X")
    ObjectIn.add("Object", "Location.Y")
    ObjectIn.add("Object", "Location.Z")
    ObjectIn.add("Object", "Orientation.Psi")
    ObjectIn.add("Object", "Orientation.Theta")
    ObjectIn.add("Object", "Orientation.Phi")
    ObjectIn.add("Object", "Name")
    ObjectIn.add("Object", "ObjClass")

    ObjectIn.add("Object", "DR_Mode")
    ObjectIn.add("Object", "DR_LinearVelocityX")
    ObjectIn.add("Object", "DR_LinearVelocityY")
    ObjectIn.add("Object", "DR_LinearVelocityZ")
    ObjectIn.add("Object", "DR_LinearAccelerationX")
    ObjectIn.add("Object", "DR_LinearAccelerationY")
    ObjectIn.add("Object", "DR_LinearAccelerationZ")
    ObjectIn.add("Object", "DR_AngularVelocityX")
    ObjectIn.add("Object", "DR_AngularVelocityY")
    ObjectIn.add("Object", "DR_AngularVelocityZ")

    #We show the configuration UI
    coreDSInstance.showConfigHelper(ioconfig, ObjectIn, coreDSPython.cCoreDSMapping(), coreDSPython.cCoreDSMapping(), coreDSPython.cCoreDSMapping())

# Function to add or update objects representing objects
def add_or_update_object(objects):
    # Loop through all objects and update or place objects at their location
    with lock:
        for i, obj_unique_name in enumerate(objects):
            try:
                
                lon = incomingObjManagerObj.objectList[obj_unique_name]['value']['lon'].toDouble()
                lat = incomingObjManagerObj.objectList[obj_unique_name]['value']['lat'].toDouble()
                
                name = incomingObjManagerObj.objectList[obj_unique_name]['value']['name'].toString()

                # Get heading (direction)
                #direction = properties.get("cog", 0)

                OrientationPsi = incomingObjManagerObj.objectList[obj_unique_name]['value']['Orientation.Psi'].toDouble()
                OrientationTheta = incomingObjManagerObj.objectList[obj_unique_name]['value']['Orientation.Theta'].toDouble()            
                OrientationPhi = incomingObjManagerObj.objectList[obj_unique_name]['value']['Orientation.Phi'].toDouble()

                #Do we have an existing node for that object?
                if not obj_unique_name in nodeList:
                    #select color based on object class
                    color = 'black'

                    if (incomingObjManagerObj.objectList[obj_unique_name]['value']['ObjClass'].toInt() == 1):
                        color = 'blue'
                    elif (incomingObjManagerObj.objectList[obj_unique_name]['value']['ObjClass'].toInt() == 2):
                        color = 'yellow'
                    elif (incomingObjManagerObj.objectList[obj_unique_name]['value']['ObjClass'].toInt() == 3):
                        color = 'red'

                    nodeList[obj_unique_name] = plt.scatter([], [], color=color, marker='o')

                nodeList[obj_unique_name].set_offsets([float(lon), float(lat)])

                # Logging to console
                # print(f"Updated object {obj_unique_name} (lat: {lat}, lon: {lon}, name: {obj_unique_name})")
            except Exception as e:
                print(f"Error object : {str(e)}")

# Main function to display DIS or HLA data
def updatePlot(i):
    if incomingObjManagerObj.objectList:
        add_or_update_object(incomingObjManagerObj.objectList)

# Run the main function
show_coreDS_ConfigurationWindow()
if (ioconfig.exists("ConfigFile") and ioconfig["ConfigFile"].toString() != ""): #A configuration has been activated
    ##Initialize the coreDS object (this will create the connection to the RTI or DIS)
    connectionResult = coreDSInstance.initAndConnect(ioconfig) 	
    if (connectionResult == coreDSPython.eRegistrationError) :
        sys.exit("coreDS Python is not activated - EXITING")

    anim = animation.FuncAnimation(fig = fig, func=updatePlot, interval=30)

    def press(event):
        global stopEverything
        if event.key == 'q':
            print("Stopping everything")
            anim.event_source.stop()
            stopEverything = True

    cid = fig.canvas.mpl_connect('key_press_event', press)
    plt.show()

    print("Press q, with focus on the map, to quit")

    #Register the timer callback. 
    threading.Timer(timerDelay, onTimer).start()
    try:
        while not stopEverything:
            time.sleep(0.1)
    except KeyboardInterrupt:
        anim.event_source.stop()

    coreDSInstance.deinit() 
    
else:
    sys.exit("No coreDS configuration has been loaded - Distributed simulation has been disabled   --- EXITING")



