angleConversions = require("angleConversions")
require("lla2ecef")

function convertAngleToDIS(value)
	local lat = math.rad(lastLat)
	local lon = math.rad(lastLong)

	local yaw = value['Psi']:toFloat()-- heading
	local pitch =  value['Theta']:toFloat()--pitch
	local roll =  value['Phi']:toFloat()--roll

	value['Theta']:set(angleConversions.getThetaFromTaitBryanAngles(lat, lon, yaw, pitch))
	value['Phi']:set(angleConversions.getPhiFromTaitBryanAngles(lat, lon, yaw, pitch, roll))
	value['Psi']:set(angleConversions.getPsiFromTaitBryanAngles(lat, lon, yaw, pitch)) 
end