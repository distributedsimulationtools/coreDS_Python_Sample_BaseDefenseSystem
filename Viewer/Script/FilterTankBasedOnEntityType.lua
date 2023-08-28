
function FilterTankBasedOnEntityType(value)
	-- if Platform of type Ground
	
	entitykind = __concatenateEntityType(value)
	
	if(string.find(entitykind, "^1%.1%.") == nil) then
		return true
	end
end