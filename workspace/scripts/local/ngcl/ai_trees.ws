class NGCL_CAICastArcaneExplosionSpecialAction extends CAICastArcaneExplosionSpecialAction
{
	default aiTreeName = "dlc\dlcngcl\data\gameplay\ai_trees\emilia_special_cast_arcane_missile.w2behtree";

	function Init()
	{
		params = new CAISpecialActionParams in this;
		params.OnCreated();
	}
}

class NGCL_GeraltNPCApplyAppearanceInitializer extends ISpawnTreeScriptedInitializer
{	
	function Init( actor : CActor ) : bool
	{
		var appearanceName : String;
		if ( actor )
		{
			if ( FactsQuerySum("ngcl_geralt_tracheostomy") > 0 ) {
				if ( FactsQuerySum("q601_geralt_has_demon_mark") > 0 ) {
					if ( FactsQuerySum("import_geralt_has_tattoo") > 0 ) {
						appearanceName = "doppler_geralt_tracheostomy_mark_tattoo";
					} else {
						appearanceName = "doppler_geralt_tracheostomy_mark";
					}
				} else {
					if ( FactsQuerySum("import_geralt_has_tattoo") > 0 ) {
						appearanceName = "doppler_geralt_tracheostomy_tattoo";
					} else {
						appearanceName = "doppler_geralt_tracheostomy";
					}
				}
			} else {
				if ( FactsQuerySum("q601_geralt_has_demon_mark") > 0 ) {
					if ( FactsQuerySum("import_geralt_has_tattoo") > 0 ) {
						appearanceName = "doppler_geralt_mark_tattoo";
					} else {
						appearanceName = "doppler_geralt_mark";
					}
				} else {
					if ( FactsQuerySum("import_geralt_has_tattoo") > 0 ) {
						appearanceName = "doppler_geralt_tattoo";
					} else {
						appearanceName = "doppler_geralt";
					}
				}
			}
		}
		NGCL_Notify_Shared("NGCL_GeraltNPCApplyAppearanceInitializer -> " + appearanceName);
		actor.ApplyAppearance(appearanceName);
		return true;
	}
	function GetEditorFriendlyName() : string
	{
		return "NGCL Geralt NPC Apply Appearance";
	}
};