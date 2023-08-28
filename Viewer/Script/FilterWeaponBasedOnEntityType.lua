
function FilterWeaponBasedOnEntityType(value)
	-- if Platform of type Ground
	
	entitykind = __concatenateEntityType(value)
	
	if(string.find(entitykind, "^2%.") == nil) then
		return true
	end
end