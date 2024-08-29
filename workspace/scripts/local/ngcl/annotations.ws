@wrapMethod(CScriptSoundSystem)
function InitializeAreaMusic( worldArea : EAreaName ) {
	wrappedMethod( worldArea );
	// NNS("InitializeAreaMusic: worldArea = " + worldArea + ", skellige loaded = " + theSound.SoundIsBankLoaded("music_skellige.bnk"));
	if (worldArea == AN_HubSlot_17) {
		SoundEvent( "play_music_skellige" );
		SoundEvent( "mus_loc_faroe" );
	}
}
