require("__concatenateEntityType")

function FilterPlanesBasedOnEntityType(value)
	-- if Plateform of type Air
	
	entitykind = __concatenateEntityType(value)
	
	if(string.find(entitykind, "^1%.2%.") == nil) then
		return true
	end
end
