// if CPC replacer active (nr_player_type > 1): first call ChangePlayerQuest( EQRE_Geralt )
latent quest function NGCL_SwitchToBearWitcher_Q() {
	var inv : CInventoryComponent;
	var ids : array<SItemUniqueId>;
	var equipmentSlotEnums : array<EEquipmentSlots>;
	var equipmentItemNames : array<name>;
	var headComponent : CHeadManagerComponent;
	var   i : int;
	
	theGame.ChangePlayer( "ngcl_ulvbjorn_player" );
	while ( !((W3PlayerWitcher)thePlayer) )
		SleepOneFrame();
	thePlayer.abilityManager.RestoreStat(BCS_Vitality);

	inv = thePlayer.GetInventory();
	NGCL_GetBearEquipmentData(equipmentSlotEnums, equipmentItemNames);
	
	// head - remember
	headComponent = (CHeadManagerComponent)thePlayer.GetComponentByClassName( 'CHeadManagerComponent' );
	headComponent.SetCustomHead( 'NGCL Ulvbjorn head' );
	thePlayer.RememberCustomHead( 'NGCL Ulvbjorn head' );
	
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
	var headComponent : CHeadManagerComponent;
	var   i : int;
	
	theGame.ChangePlayer( "Geralt" );
	while ( !((W3PlayerWitcher)thePlayer) )
		SleepOneFrame();
	thePlayer.abilityManager.RestoreStat(BCS_Vitality);
	
	inv = thePlayer.GetInventory();
	NGCL_GetBearEquipmentData(equipmentSlotEnums, equipmentItemNames);
	
	// head - remember
	headComponent = (CHeadManagerComponent)thePlayer.GetComponentByClassName( 'CHeadManagerComponent' );
	headComponent.RemoveCustomHead();
	thePlayer.ClearRememberedCustomHead();

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

quest function NGCL_SetEncounterEnabled( encounterTag : name, enable : bool )
{
	var encounter 				: CEncounter;
	
	encounter = (CEncounter)theGame.GetEntityByTag ( encounterTag );
	if ( !encounter ) {
		NNS("NGCL_SetEncounterEnabled: not found " + encounterTag);
		return;
	}
	
	encounter.EnableEncounter(enable);
	if (!enable) {
		encounter.ForceDespawnDetached();
	} else {
		encounter.EnterArea();
	}
}

quest function NGCL_SetSkating(enable : bool)
{
	if (enable)
	{
		thePlayer.GotoState('Skating');
	}
	else
	{
		thePlayer.GotoState('Exploration');
	}
	NNS("NGCL_SetSkating = " + enable);
}

quest function NGCL_HandlePriscilla(hide : bool) {
	var priscillaNPC : CNewNPC;
	
	priscillaNPC = (CNewNPC)theGame.GetEntityByTag('priscilla');
	if (hide) {
		// position of q308_blanka_injured_bed1
		if ( priscillaNPC && VecDistanceSquared(priscillaNPC.GetWorldPosition(), Vector(776.736, 2041.56, 20.4375)) < 10.f ) {
			// hide priscilla and mark this
			FactsAdd("ngcl_priscilla_injured_hidden", 1);
		}
	} else {
		if ( FactsQuerySum("ngcl_priscilla_injured_hidden") > 0 ) {
			// unhide priscilla and remove mark
			FactsAdd("ngcl_priscilla_injured_shown", 1);
			FactsRemove("ngcl_priscilla_injured_hidden");
		}
	}
}

// player - PLAYER_SLOT
// npc - NPC_ANIM_SLOT
quest function NGCL_PlayAnim(entityTag : name, animName : name, slotName : name, blendIn : float, blendOut : float) {
	var entity : CEntity;
	
	entity = theGame.GetEntityByTag(entityTag);
	entity.GetRootAnimatedComponent().PlaySlotAnimationAsync( animName, slotName, SAnimatedComponentSlotAnimationSettings(blendIn, blendOut));
}

quest function NGCL_ShowSkatingTutorial() {
	NNS("Skating tutorial: TODO");
}
