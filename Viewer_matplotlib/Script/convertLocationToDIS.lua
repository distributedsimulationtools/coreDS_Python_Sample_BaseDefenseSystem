angleConversions = require("angleConversions")
require("lla2ecef")

lastLat = 0;
lastLong = 0;
lastAlt = 0;

function convertLocationToDIS(value)
	lastLat = value['Y']:toFloat();
	lastLong = value['X']:toFloat();
	lastAlt = value['Z']:toFloat();

	--convert lat/long to geocentric
	a,b,c = lla2ecef(lastLat, lastLong,lastAlt)

	value['X']:set(a)
	value['Y']:set(b)
	value['Z']:set(c)
end