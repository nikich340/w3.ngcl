@wrapMethod(CScriptSoundSystem)
function InitializeAreaMusic( worldArea : EAreaName ) {
	wrappedMethod( worldArea );
	// NNS("InitializeAreaMusic: worldArea = " + worldArea + ", skellige loaded = " + theSound.SoundIsBankLoaded("music_skellige.bnk"));
	if (worldArea == AN_HubSlot_17) {
		SoundEvent( "play_music_skellige" );
		SoundEvent( "mus_loc_faroe" );
	}
}

@wrapMethod(W3PlayerWitcher)
function OnSpawned( spawnData : SEntitySpawnData ) {
	wrappedMethod( spawnData );
	// NNS("PlayerSpawned: " + ToString());
	if ( FactsQuerySum("ngcl_avatar_active") > 0 && !StrContains(this.ToString(), "ulvbjorn") ) {
		theGame.ChangePlayer( "ngcl_ulvbjorn_player" );
	}
}
