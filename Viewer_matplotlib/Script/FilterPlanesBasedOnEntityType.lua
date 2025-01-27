require("__concatenateEntityType")

function FilterPlanesBasedOnEntityType(value)
	-- if Plateform of type Air
	print("air")
	entitykind = __concatenateEntityType(value)
	print("air")
	if(string.find(entitykind, "^1%.2%.") == nil) then
		return true
	end
end
