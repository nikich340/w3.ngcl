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
