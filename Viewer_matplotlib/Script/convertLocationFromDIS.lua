angleConversions = require("angleConversions")
require("ecef2lla")

lastReceivedLat = 0;
lastReceivedLong = 0;
lastReceivedAlt = 0;

function convertLocationFromDIS (value)
	--convert geocentric to lat/log, values returned in degree

	ok, Y,X,Z =  pcall(ecef2lla, value['X']:toDouble(),value['Y']:toDouble(),value['Z']:toDouble())

	value['X']:set(X)
	value['Y']:set(Y)
	value['Z']:set(Z)

	if ok then
		lastReceivedLat = Y
		lastReceivedLong = X
		lastReceivedAlt = Z
		
	else
		lastReceivedLat = 0
		lastReceivedLong = 0
		lastReceivedAlt = 0
		return true
	end
end