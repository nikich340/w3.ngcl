class CNGCL_PlayerData {
	saved var avatarActive : bool;
	saved var headName : name;
	saved var hairName : name;
	saved var equipmentItemNames : array<name>;
}

@addField(CR4Player)
protected saved var NGCLData : CNGCL_PlayerData;

// v potential conflict with another mod importing this var: just remove these lines then
@addField(CR4Player)
import var displayName : LocalizedString;
// ^ potential conflict with another mod importing this var: just remove these lines then

@addMethod(CR4Player)
public function NGCL_getDataObject() : CNGCL_PlayerData
{
	if (!NGCLData)
		NGCLData = new CNGCL_PlayerData in this;
	return NGCLData;
}

@addMethod(CR4Player)
public function NGCL_setDisplayName(stringId : int)
{
	displayName = NGCL_getStringStorage().GetLocalizedStringById(stringId);
}

@wrapMethod(CR4Player)
function OnSpawned( spawnData : SEntitySpawnData ) {
	var headManager : CHeadManagerComponent;

	if (NGCLData.avatarActive) {
		NGCL_setDisplayName(2119453171);
		headManager = (CHeadManagerComponent)(GetComponentByClassName( 'CHeadManagerComponent' ));
		headManager.BlockGrowing( true );
		headManager.SetCustomHead( 'NGCL Ulvbjorn head' );
		RememberCustomHead( 'NGCL Ulvbjorn head' );
	}
	wrappedMethod( spawnData );
}
