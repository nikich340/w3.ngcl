class CNGCL_LocalizedStringStorage extends CEntity {
	editable var stringValues	: array<LocalizedString>;
	editable var stringIds		: array<int>;

	public function GetLocalizedStringById(id : int) : LocalizedString {
		var i : int;
		var null : LocalizedString;

		if (id <= 0)
			return null;

		for (i = 0; i < stringIds.Size(); i += 1) {
			if (stringIds[i] == id) {
				return stringValues[i];
			}
		}
		NNS("CNGCL_LocalizedStringStorage: id NOT found: " + IntToString(id));
		return null;
	}
}

function NGCL_getStringStorage() : CNGCL_LocalizedStringStorage {
	var template : CEntityTemplate;
	var entity : CNGCL_LocalizedStringStorage;
	
	entity = (CNGCL_LocalizedStringStorage)theGame.GetEntityByTag('CNGCL_LocalizedStringStorage');
	if (!entity) {
		template = (CEntityTemplate)LoadResource("dlc\dlcngcl\data\entities\ngcl_names_storage.w2ent", true);
		entity = (CNGCL_LocalizedStringStorage)theGame.CreateEntity(template, thePlayer.GetWorldPosition());
		entity.AddTag('CNGCL_LocalizedStringStorage');
	}
	return entity;
}
