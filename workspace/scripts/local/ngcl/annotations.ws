@wrapMethod(CScriptSoundSystem)
function InitializeAreaMusic( worldArea : EAreaName ) {
	wrappedMethod( worldArea );
	// NNS("InitializeAreaMusic: worldArea = " + worldArea + ", skellige loaded = " + theSound.SoundIsBankLoaded("music_skellige.bnk"));
	if (worldArea == AN_HubSlot_17) {
		SoundEvent( "play_music_skellige" );
		SoundEvent( "mus_loc_faroe" );
	}
}

@addMethod(CR4Player)
function NGCL_IsUlvbjorn() : bool {
	return StrContains(this.ToString(), "ulvbjorn");
}

@wrapMethod(W3PlayerWitcher)
function OnSpawned( spawnData : SEntitySpawnData ) {
	wrappedMethod( spawnData );
	// NNS("PlayerSpawned: " + ToString());
	if ( FactsQuerySum("ngcl_avatar_active") > 0 && !NGCL_IsUlvbjorn() ) {
		theGame.ChangePlayer( "ngcl_ulvbjorn_player" );
	}
}

@wrapMethod(W3PlayerWitcher)
function GetEncumbrance() : float {
	if ( NGCL_IsUlvbjorn() ) {
		return 0.f;
	}
	return wrappedMethod();
}
