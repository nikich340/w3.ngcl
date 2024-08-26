// if CPC replacer active (nr_player_type > 1): first call ChangePlayerQuest( EQRE_Geralt )
latent quest function NGCL_SwitchToBearWitcher_Q() {
	var inv : CInventoryComponent;
	var ids : array<SItemUniqueId>;
	var equipmentSlotEnums : array<EEquipmentSlots>;
	var equipmentItemNames : array<name>;
	var   i : int;
	
	theGame.ChangePlayer( "ngcl_ulvbjorn_player" );
	while ( !((W3PlayerWitcher)thePlayer) )
		SleepOneFrame();
	thePlayer.abilityManager.RestoreStat(BCS_Vitality);

	inv = thePlayer.GetInventory();
	NGCL_GetBearEquipmentData(equipmentSlotEnums, equipmentItemNames);
	
	// hair - set new hair
	ids = inv.GetItemsByCategory( 'hair' );
	for ( i = 0; i < ids.Size(); i += 1 )
	{
		if ( inv.IsItemMounted(ids[i]) )
			inv.UnmountItem(ids[i]);
		inv.RemoveItem(ids[i], 1);
	}
	ids.Clear();
	ids = inv.AddAnItem('NGCL Ulvbjorn hair', 1);
	inv.MountItem(ids[0]);

	// equipment - equip
	for (i = 0; i < equipmentItemNames.Size(); i += 1) {
		//if ( inv.GetItemEquippedOnSlot(equipmentSlotEnums[i], id) )
		//	savedDataObj.equipmentItemNames.PushBack( inv.GetItemName(id) );
		ids.Clear();
		ids = inv.AddAnItem(equipmentItemNames[i], 1);
		thePlayer.EquipItem(ids[0]);
	}
	
	FactsAdd("ngcl_avatar_active", 1);
}

latent quest function NGCL_SwitchToGeralt_Q() {
	var inv : CInventoryComponent;
	var ids : array<SItemUniqueId>;
	var equipmentSlotEnums : array<EEquipmentSlots>;
	var equipmentItemNames : array<name>;
	var result : bool;
	var   i : int;
	
	theGame.ChangePlayer( "Geralt" );
	while ( !((W3PlayerWitcher)thePlayer) )
		SleepOneFrame();
	thePlayer.abilityManager.RestoreStat(BCS_Vitality);
	
	inv = thePlayer.GetInventory();
	NGCL_GetBearEquipmentData(equipmentSlotEnums, equipmentItemNames);

	// hair - restore saved
	ids = inv.GetItemsByCategory( 'hair' );
	for ( i = 0; i < ids.Size(); i += 1 )
	{
		if ( inv.IsItemMounted(ids[i]) )
			inv.UnmountItem(ids[i]);
		inv.RemoveItem(ids[i], 1);
	}
	ids.Clear();
	// TODO - use saved hair on Geralt NPC
	ids = inv.AddAnItem('Preview Hair', 1);
	inv.MountItem(ids[0]);

	for (i = 0; i < equipmentItemNames.Size(); i += 1) {
		inv.RemoveItemByName(equipmentItemNames[i], 1);
	}

	FactsRemove("ngcl_avatar_active");
}

function NGCL_GetBearEquipmentData(out equipmentSlotEnums : array<EEquipmentSlots>, out equipmentItemNames : array<name>) {
	var NGP : bool = FactsQuerySum("NewGamePlus") > 0;;

	// equipment - armor
	equipmentSlotEnums.PushBack(EES_Armor);
	if (NGP)
		equipmentItemNames.PushBack('NGP NGCL Bear Armor 4');
	else
		equipmentItemNames.PushBack('NGCL Bear Armor 4');

	// equipment - boots
	equipmentSlotEnums.PushBack(EES_Boots);
	if (NGP)
		equipmentItemNames.PushBack('NGP NGCL Bear Boots 5');
	else
		equipmentItemNames.PushBack('NGCL Bear Boots 5');
	
	// equipment - gloves
	equipmentSlotEnums.PushBack(EES_Gloves);
	if (NGP)
		equipmentItemNames.PushBack('NGP NGCL Bear Gloves 5');
	else
		equipmentItemNames.PushBack('NGCL Bear Gloves 5');
	
	// equipment - pants
	equipmentSlotEnums.PushBack(EES_Pants);
	if (NGP)
		equipmentItemNames.PushBack('NGP NGCL Bear Pants 5');
	else
		equipmentItemNames.PushBack('NGCL Bear Pants 5');
	
	// equipment - silver
	equipmentSlotEnums.PushBack(EES_SilverSword);
	if (NGP)
		equipmentItemNames.PushBack('NGP NGCL Bear School silver sword 4');
	else
		equipmentItemNames.PushBack('NGCL Bear School silver sword 4');
	
	// equipment - steel
	equipmentSlotEnums.PushBack(EES_SteelSword);
	if (NGP)
		equipmentItemNames.PushBack('NGP NGCL Bear School steel sword 4 Ardaenye');
	else
		equipmentItemNames.PushBack('NGCL Bear School steel sword 4 Ardaenye');

	// equipment - crossbow
	equipmentSlotEnums.PushBack(EES_RangedWeapon);
	equipmentItemNames.PushBack('NGCL Bear School Crossbow');
}
