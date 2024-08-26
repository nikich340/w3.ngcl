quest function NGCL_Notify(message : String) {
	NGCL_Notify_Shared(message);
}

function NGCL_Notify_Shared(message : String) {
	theGame.GetGuiManager().ShowNotification(message, 5000.f, false);
	LogChannel('NGCL_Notify', "(" + FloatToStringPrec(theGame.GetEngineTimeAsSeconds(), 3) + "): " + message);
}

exec function topoint(pointName : String) {
	if (pointName == "1" || pointName == "board") {
		thePlayer.Teleport( Vector(691.167969, 2014.068604, 32.415546) );
	} else if (pointName == "2" || pointName == "redanian") {
		thePlayer.Teleport( Vector(449.05, 2232.24, 46.06) );
	} else if (pointName == "3" || pointName == "crime") {
		thePlayer.Teleport( Vector(642.598, 1180.57, 8.33731) );
	} else if (pointName == "4" || pointName == "vilmerius") {
		thePlayer.Teleport( Vector(786.28, 2033.21, 14.74) );
	} else if (pointName == "whale") {
		thePlayer.Teleport( Vector(-737.5, -83.43, 1.41) );
	}
}

exec function testanim(animName : name, blend : bool) {
	var blendIn, blendOut : float;
	
	if (blend) {
		blendIn = 0.25f;
		blendOut = 0.25f;
	} else {
		blendIn = 0.f;
		blendOut = 0.f;
	}
	thePlayer.GetRootAnimatedComponent().PlaySlotAnimationAsync( animName, 'PLAYER_SLOT', SAnimatedComponentSlotAnimationSettings(blendIn, blendOut) );
}

exec function getpos() {
	NGCL_Notify_Shared( "PlayerPos: " + VecToString(thePlayer.GetWorldPosition()) );
}

exec function showfact(factName : String) {
	if ( !FactsDoesExist(factName) ) {
		NGCL_Notify_Shared("Fact does not exist: [" + factName + "]");
	} else {
		NGCL_Notify_Shared("Fact [" + factName + "] = " + FactsQuerySum(factName));
	}
}

exec function tobear1() {
	theGame.ChangePlayer( "ngcl_ulvbjorn_player" );
}

exec function tobear2() {
	var inv : CInventoryComponent;
	var ids : array<SItemUniqueId>;
	var equipmentSlotEnums : array<EEquipmentSlots>;
	var equipmentItemNames : array<name>;
	var   i : int;

	thePlayer.abilityManager.RestoreStat(BCS_Vitality);

	inv = thePlayer.GetInventory();
	NGCL_GetBearEquipmentData(equipmentSlotEnums, equipmentItemNames);

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

exec function togeralt1() {
	theGame.ChangePlayer( "Geralt" );
}

exec function togeralt2() {
	var inv : CInventoryComponent;
	var ids : array<SItemUniqueId>;
	var equipmentSlotEnums : array<EEquipmentSlots>;
	var equipmentItemNames : array<name>;
	var result : bool;
	var   i : int;
	
	thePlayer.abilityManager.RestoreStat(BCS_Vitality);
	
	inv = thePlayer.GetInventory();
	NGCL_GetBearEquipmentData(equipmentSlotEnums, equipmentItemNames);

	// hair - restore saved (TODO)
	/*
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
	*/

	for (i = 0; i < equipmentItemNames.Size(); i += 1) {
		inv.RemoveItemByName(equipmentItemNames[i], 1);
	}

	FactsRemove("ngcl_avatar_active");
}

exec function gpscene(inputName : String) {
	var scene      : CStoryScene;
	scene = (CStoryScene)LoadResource("dlc\dlcngcl\data\scenes\ngcl_gp_geralt_oneliners.w2scene", true);
	if (!scene)
		NGCL_Notify_Shared("NULL scene!");

	theGame.GetStorySceneSystem().PlayScene(scene, inputName);
}

exec function testname() {
	thePlayer.displayName;
}

exec function testnpc(npcName : String, optional hostile : bool) {
	var path : String;
	var template : CEntityTemplate;
	var npc : CNewNPC;
	
	if (npcName == "geralt1") {
		path = "dlc\dlcngcl\data\entities\ngcl_geralt_npc.w2ent";
	} else {
		NGCL_Notify_Shared("Unknown npcName!");
		return;
	}
	
	template = (CEntityTemplate)LoadResource(path, true);
	if (!template) {
		NGCL_Notify_Shared("NULL template");
		return;
	}
	
	npc = (CNewNPC)theGame.CreateEntity(template, thePlayer.GetWorldPosition() + thePlayer.GetWorldForward() * 3.f);
	if (!npc) {
		NGCL_Notify_Shared("NULL entity");
		return;
	}
	npc.AddTag('NGCL_Test');
	
	if (hostile) {
		npc.SetTemporaryAttitudeGroup( 'hostile_to_player', AGP_Default );
	}
}
