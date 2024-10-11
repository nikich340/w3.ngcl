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
		if ( actor )
		{
			if ( FactsQuerySum("ngcl_geralt_tracheostomy") > 0 )
				actor.ApplyAppearance("doppler_geralt_tracheostomy");
			else
				actor.ApplyAppearance("doppler_geralt");
		}
		return true;
	}
	function GetEditorFriendlyName() : string
	{
		return "NGCL Geralt NPC Apply Appearance";
	}
};