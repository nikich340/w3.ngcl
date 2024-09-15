class NGCL_CAICastArcaneExplosionSpecialAction extends CAICastArcaneExplosionSpecialAction
{
	default aiTreeName = "dlc\dlcngcl\data\gameplay\ai_trees\emilia_special_cast_arcane_missile.w2behtree";

	function Init()
	{
		params = new CAISpecialActionParams in this;
		params.OnCreated();
	}
}
