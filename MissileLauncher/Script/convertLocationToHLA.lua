angleConversions = require("angleConversions")
require("lla2ecef")

function convertLocationToHLA (value)
	local lat = math.rad(value['WorldLocation.X']:toDouble())
	local lon = math.rad(value['WorldLocation.Y']:toDouble())

	X,Y,Z = lla2ecef(value.WorldLocation.X,value.WorldLocation.Y,value.WorldLocation.Z)

	value['WorldLocation.X']:set(X)
	value['WorldLocation.Y']:set(Y)
	value['WorldLocation.Z']:set(Z)

	local yaw = value['Orientation.Psi']:toFloat()-- heading
	local pitch = value['Orientation.Theta']:toFloat()--pitch
	local roll = value['Orientation.Phi']:toFloat()--roll

	value['Orientation.Theta']:set((angleConversions.getThetaFromTaitBryanAngles(lat, lon, yaw, pitch)));
	value['Orientation.Phi']:set((angleConversions.getPhiFromTaitBryanAngles(lat, lon, yaw, pitch, roll)))
	value['Orientation.Psi']:set((angleConversions.getPsiFromTaitBryanAngles(lat, lon, yaw, pitch))) 
end