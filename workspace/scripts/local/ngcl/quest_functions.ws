function NGCL_SwitchToBearWitcher() {
	var headManager : CHeadManagerComponent;
	var inv : CInventoryComponent;
	var id : SItemUniqueId;
	var ids : array<SItemUniqueId>;
	var equipmentSlotEnums : array<EEquipmentSlots>;
	var equipmentItemNames : array<name>;
	var savedDataObj : CNGCL_PlayerData;
	var NGP : bool;
	var   i : int;
	
	NGP = FactsQuerySum("NewGamePlus") > 0;
	inv = thePlayer.GetInventory();
	savedDataObj = thePlayer.NGCL_getDataObject();
	
	// name
	thePlayer.NGCL_setDisplayName(2119453171);
	
	// head
	headManager = (CHeadManagerComponent)(thePlayer.GetComponentByClassName( 'CHeadManagerComponent' ));
	savedDataObj.headName = headManager.GetCurHeadName();
	headManager.BlockGrowing( true );
	headManager.SetCustomHead( 'NGCL Ulvbjorn head' );
	thePlayer.RememberCustomHead( 'NGCL Ulvbjorn head' );
	
	// hair
	ids = inv.GetItemsByCategory( 'hair' );
	for ( i = 0; i < ids.Size(); i += 1 )
	{
		if ( inv.IsItemMounted(ids[i]) )
			inv.UnmountItem(ids[i]);
		savedDataObj.hairName = inv.GetItemName(ids[i]);
		inv.RemoveItem(ids[i], 1);
	}
	ids.Clear();
	ids = inv.AddAnItem('NGCL Ulvbjorn hair', 1);
	inv.MountItem(ids[0]);

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
	equipmentItemNames.PushBack('Ardaenye');

	// equipment - crossbow
	equipmentSlotEnums.PushBack(EES_RangedWeapon);
	equipmentItemNames.PushBack('NGCL Bear School Crossbow');

	// equipment - equip
	savedDataObj.equipmentItemNames.Clear();
	for (i = 0; i < equipmentItemNames.Size(); i += 1) {
		if ( inv.GetItemEquippedOnSlot(equipmentSlotEnums[i], id) )
			savedDataObj.equipmentItemNames.PushBack( inv.GetItemName(id) );
		ids.Clear();
		ids = inv.AddAnItem(equipmentItemNames[i], 1);
		thePlayer.EquipItem(ids[0]);
	}
	
	savedDataObj.avatarActive = true;
	FactsAdd("ngcl_avatar_active", 1);
}

function NGCL_SwitchToGeralt(equipPrevArmor : bool) {
	var headManager : CHeadManagerComponent;
	var inv : CInventoryComponent;
	var ids : array<SItemUniqueId>;
	var equipmentItemNames : array<name>;
	var NGP, result : bool;
	var savedDataObj : CNGCL_PlayerData;
	var   i : int;
	
	NGP = FactsQuerySum("NewGamePlus") > 0;
	inv = thePlayer.GetInventory();
	savedDataObj = thePlayer.NGCL_getDataObject();
	
	// name
	thePlayer.NGCL_setDisplayName(318188);
	
	// head
	headManager = (CHeadManagerComponent)(thePlayer.GetComponentByClassName( 'CHeadManagerComponent' ));
	headManager.BlockGrowing( false );
	headManager.RemoveCustomHead();
	thePlayer.ClearRememberedCustomHead();
	
	// hair
	ids = inv.GetItemsByCategory( 'hair' );
	for ( i = 0; i < ids.Size(); i += 1 )
	{
		if ( inv.IsItemMounted(ids[i]) )
			inv.UnmountItem(ids[i]);
		inv.RemoveItem(ids[i], 1);
	}
	ids.Clear();
	ids = inv.AddAnItem(savedDataObj.hairName, 1);
	inv.MountItem(ids[0]);
	
	// equipment - armor
	if (NGP)
		equipmentItemNames.PushBack('NGCL NGP Bear Armor 4 with medallion');
	else
		equipmentItemNames.PushBack('NGCL Bear Armor 4 with medallion');

	// equipment - boots
	if (NGP)
		equipmentItemNames.PushBack('NGP Bear Boots 5');
	else
		equipmentItemNames.PushBack('Bear Boots 5');
	
	// equipment - gloves
	if (NGP)
		equipmentItemNames.PushBack('NGP Bear Gloves 5');
	else
		equipmentItemNames.PushBack('Bear Gloves 5');
	
	// equipment - pants
	if (NGP)
		equipmentItemNames.PushBack('NGP Bear Pants 5');
	else
		equipmentItemNames.PushBack('Bear Pants 5');
	
	// equipment - silver
	if (NGP)
		equipmentItemNames.PushBack('NGP Bear School silver sword 4');
	else
		equipmentItemNames.PushBack('Bear School silver sword 4');
	
	// equipment - steel
	equipmentItemNames.PushBack('Ardaenye');

	// equipment - crossbow
	equipmentItemNames.PushBack('Bear School Crossbow');
	
	for (i = 0; i < equipmentItemNames.Size(); i += 1) {
		result = inv.RemoveItemByName(equipmentItemNames[i], 1);
	}
	
	if (equipPrevArmor) {
		for (i = 0; i < savedDataObj.equipmentItemNames.Size(); i += 1) {
			ids = inv.GetItemsIds( savedDataObj.equipmentItemNames[i] );
			if ( ids.Size() < 1 ) {
				NGCL_Notify_Shared("ERROR: not found saved eq: " + savedDataObj.equipmentItemNames[i]);
				ids = inv.AddAnItem( savedDataObj.equipmentItemNames[i], 1 );
			}
			result = thePlayer.EquipItem(ids[0]);
		}
	}
	savedDataObj.equipmentItemNames.Clear();

	savedDataObj.avatarActive = false;
	FactsRemove("ngcl_avatar_active");
}
