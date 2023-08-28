angleConversions = require("angleConversions")
require("lla2ecef")

function convertAngleFromDIS(value)
	local lat = math.rad(lastReceivedLat)
	local lon = math.rad(lastReceivedLong)

	local yaw = angleConversions.getOrientationFromEuler(lat, lon, value['Psi']:toFloat() , value['Theta']:toFloat())
	local pitch = angleConversions.getPitchFromEuler(lat, lon, value['Psi']:toFloat() , value['Theta']:toFloat())
	local roll = angleConversions.getRollFromEuler(lat, lon, value['Psi']:toFloat(), value['Theta']:toFloat(), value['Phi']:toFloat())

	value['Psi']:set(yaw)
	value['Theta']:set(pitch)
	value['Phi']:set(roll)
end