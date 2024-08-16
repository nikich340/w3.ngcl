quest function NGCL_Notify(message : String) {
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
