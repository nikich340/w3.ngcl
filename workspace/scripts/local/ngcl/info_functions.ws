quest function NGCL_Notify(message : String) {
	NGCL_Notify_Shared(message);
}

function NGCL_Notify_Shared(message : String, optional showInGameplay : bool) {
	if (showInGameplay)
		theGame.GetGuiManager().ShowNotification(message, 5000.f, false);
	LogChannel('NGCL_Notify', "(" + FloatToStringPrec(theGame.GetEngineTimeAsSeconds(), 3) + "): " + message);
}
