quest function NGCL_Notify(message : String) {
	NGCL_Notify_Shared(message);
}

function NGCL_Notify_Shared(message : String) {
	theGame.GetGuiManager().ShowNotification(message, 5000.f, false);
	LogChannel('NGCL_Notify', "(" + FloatToStringPrec(theGame.GetEngineTimeAsSeconds(), 3) + "): " + message);
}

exec function topoint(pointName : String) {
	if (pointName == "1") {
		thePlayer.Teleport( Vector(691.167969, 2014.068604, 32.415546) );
	} else if (pointName == "2") {
		thePlayer.Teleport( Vector(449.05, 2232.24, 46.06) );
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
