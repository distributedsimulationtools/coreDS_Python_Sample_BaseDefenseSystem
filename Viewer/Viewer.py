""" viewer.py

    Required packages:
    - flask
    - folium
    - pyproj
    
    ATTENTION: This scripts download the  missing dependencies!

    Head to http://127.0.0.1:5000/ in your browser to see the map displayed

"""

import pathlib
import os   
import threading
import coreDSPython #Import the coreDS library
import subprocess
import sys
import signal
import logging

from background_thread import BackgroundThreadFactory, TASKS_QUEUE

try: 
    from flask import Flask, render_template_string
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'flask'])
finally:
    from flask import Flask, render_template_string
    
try: 
    import folium
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'folium'])
finally:
    import folium

try: 
   import pyproj
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'pyproj'])
finally:
    import pyproj


# My main coreDS Object
coreDSInstance = coreDSPython.cCoreDS()

# Create a function to handle the timer  events. 
timerDelay = 0.1
def onTimer(): 
    _ = coreDSInstance.step() # Check for new data from the simulation backend
    threading.Timer(timerDelay, onTimer).start() 

# First we have to register the local object / local messages and properties known by this program
# Input data -> from the simulation to this system
# Output data -> from this software to the remote simulation

MessageIn = coreDSPython.cCoreDSMapping()
MessageIn.add("Explosion", "X")
MessageIn.add("Explosion", "Y")
MessageIn.add("Explosion", "Z")

ObjectIn = coreDSPython.cCoreDSMapping()
ObjectIn.add("Airplane", "X")
ObjectIn.add("Airplane", "Y")
ObjectIn.add("Airplane", "Z")
ObjectIn.add("Airplane", "Name")

ObjectIn.add("Tank", "X")
ObjectIn.add("Tank", "Y")
ObjectIn.add("Tank", "Z")
ObjectIn.add("Tank", "Name")

ObjectIn.add("MissileObject", "X")
ObjectIn.add("MissileObject", "Y")
ObjectIn.add("MissileObject", "Z")
ObjectIn.add("MissileObject", "Name")

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
ioconfig["LogToStdOutput.AutoFlush"] = False
ioconfig["LogToStdOutput.Enabled"] = True

#We show the configuration UI
coreDSInstance.showConfigHelper(ioconfig, ObjectIn, coreDSPython.cCoreDSMapping(), MessageIn, coreDSPython.cCoreDSMapping())

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

                lon, lat, alt = transformer.transform(values['X'].toDouble(),values['Y'].toDouble(),values['Z'].toDouble(),radians=False)

                self.objectList[localUniqueObjectIdentifier]['value'] = coreDSPython.CVariant(values) #copy values

                ## Add the LLA information into our CVariant so we can use it later
                self.objectList[localUniqueObjectIdentifier]['value']['lat'] = lat
                self.objectList[localUniqueObjectIdentifier]['value']['lon'] = lon
                self.objectList[localUniqueObjectIdentifier]['value']['alt'] = alt

                print("Received " , objectType, values['Name'], "at location received at location ", self.objectList[localUniqueObjectIdentifier]['value'])

            except Exception as e:
                logging.error(f'{e}. Continuing execution...')
        
##Create a local instance of our Object Manager
incomingObjManagerObj = ObjectUpdateManager()

#Add a mutex to play nice with async tasks.
lock = threading.Lock()

## Function handler. This is the second way to receive information from the simulation framework
## You can either register a function call back of a callable object with coreDS
## This function will be called whenever a GroundVehicule is updated (based on the current mapping)
def explosionReceived(messagename, values):
    # This function is called when new values are available for the given "object type"
    # This is a sample - you will have to add more code to support
    # multiple instance or multiple object type
    print("Boom received at location explosionReceived", values) 
   
def objectRemoved(objIdentifier):
    with lock:
        try:
            incomingObjManagerObj.objectList.pop(objIdentifier) 
            print("Removing object id: ", objIdentifier) 
        except:
            pass         
        
## Add a callback handler.
## When an object if type "Aircraft" is updated, call the "AircraftManager" object
coreDSInstance.registerObjectUpdateHandler("Airplane", incomingObjManagerObj)

# Another way of registering an handler.
# You must careful to have the correct function signature.
# Commented because it is not useful for this sample
# coreDSInstance.registerObjectUpdateHandler("Airplane", fake)

## When an object if type "Tank" is updated, call the "objectTankUpdated" function
coreDSInstance.registerObjectUpdateHandler("Tank", incomingObjManagerObj)

## When an object if type "Tank" is updated, call the "objectTankUpdated" function
coreDSInstance.registerObjectUpdateHandler("MissileObject", incomingObjManagerObj)

## When an object if type "Tank" is updated, call the "objectTankUpdated" function
coreDSInstance.registerMessageReceivedHandler("Explosion", explosionReceived)
coreDSInstance.registerMessageReceivedHandler("Collision", explosionReceived)

coreDSInstance.registerObjectRemovedHandler("Airplane", objectRemoved)
coreDSInstance.registerObjectRemovedHandler("Tank", objectRemoved)
coreDSInstance.registerObjectRemovedHandler("MissileObject", objectRemoved)

if (ioconfig.exists("ConfigFile") and ioconfig["ConfigFile"].toString() != ""): #A configuration has been activated
    ##Initialize the coreDS object (this will create the connection to the RTI or DIS)
    coreDSInstance.initAndConnect(ioconfig) 	

    #Register the timer callback. 
    threading.Timer(timerDelay, onTimer).start()
else:
    sys.exit("No coreDS configuration has been loaded - Distributed simulation has been disabled   --- EXITING")

#### DISPLAY STUFF

centerLatitude = 46.8563684
centerLongitude =  -71.3416925

# web // display stuff
app = Flask(__name__)

notification_thread = BackgroundThreadFactory.create('notification')

# this condition is needed to prevent creating duplicated thread in Flask debug mode
if not (app.debug or os.environ.get('FLASK_ENV') == 'development') or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    notification_thread.start()

    original_handler = signal.getsignal(signal.SIGINT)

    def sigint_handler(signum, frame):
        notification_thread.stop()

        # wait until thread is finished
        if notification_thread.is_alive():
            notification_thread.join()

        original_handler(signum, frame)

    try:
        signal.signal(signal.SIGINT, sigint_handler)
    except ValueError as e:
        logging.error(f'{e}. Continuing execution...')


@app.route('/')
def display_map():
    m = folium.Map(location=[centerLatitude, centerLongitude], zoom_start=9)

    for obj, prop in incomingObjManagerObj.objectList.items():
        # Add a marker for the new data point
        color = 'black'

        if (prop['name'] == "Airplane"):
            color = 'blue'
        if (prop['name'] == "Tank"):
            color = 'yellow'
        if (prop['name'] == "MissileObject"):
            color = 'red'

        b = folium.CircleMarker(location=[prop['value']['lat'].toDouble(), prop['value']['lon'].toDouble()], radius=2, color=color, popup=prop['name']).add_to(m)
          
    # set the iframe width and height
    m.get_root().width = "800px"
    m.get_root().height = "600px"
    iframe = m.get_root()._repr_html_()

    return render_template_string(
        """
            <meta http-equiv="refresh" content="1" /> 
            <!DOCTYPE html>
            <html>
                <head></head>
                <body>
                    <h1>coreDS Python viewer sample</h1>
                    {{ iframe|safe }}
                </body>
            </html>
        """,
        iframe=iframe,
    )

if __name__ == "__main__":
    app.run(debug=False, use_reloader=False) # Start the web server and update the map
