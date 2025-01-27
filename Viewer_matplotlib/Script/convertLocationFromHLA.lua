angleConversions = require("angleConversions")
require("ecef2lla")

function convertLocationFromHLA (value)
	Y, X, Y = ecef2lla(value['WorldLocation.X']:toDouble(),value['WorldLocation.Y']:toDouble(),value['WorldLocation.Z']:toDouble())

	local lat = math.rad(Y)  --converting to rad because function requires rad
	local lon = math.rad(X)

	local psi =  value['Orientation.Psi']:toFloat()-- heading
	local theta = value['Orientation.Theta']:toFloat()--pitch
	local phi = value['Orientation.Phi']:toFloat() --roll

	value['Orientation.Psi']:set(angleConversions.getOrientationFromEuler(lat, lon, psi, theta))
	value['Orientation.Theta']:set(angleConversions.getPitchFromEuler(lat, lon, psi, theta))
	value['Orientation.Phi']:set(angleConversions.getRollFromEuler(lat, lon, psi, theta, phi))

	value['WorldLocation.Y']:set(Y)
	value['WorldLocation.X']:set(X)
	value['WorldLocation.Z']:set(Z)
end