/*
class NGCL_SignHitTracker extends CGameplayEntity {
	editable var trackSignType : ESignType;
	editable var trackHitsCount : int;
	editable var factNameOnCompleted : String;
	protected var signHitsCount : int;
	
	default trackSignType = ST_Aard;
	default trackHitsCount = 1;
	
	function IncreaseHitsCount( signType : ESignType ) {
		if ( signType == trackSignType ) {
			signHitsCount += 1;
			if (signHitsCount == trackHitsCount)
				FactsAdd(factNameOnCompleted, 1);
		}
	}
	
	event OnAardHit( sign : W3AardProjectile )
	{
		IncreaseHitsCount( ST_Aard );
		super.OnAardHit( sign );
	}
	
	event OnIgniHit( sign : W3IgniProjectile )
	{
		IncreaseHitsCount( ST_Igni );
		super.OnIgniHit( sign );
	}
	
	event OnYrdenHit( caster : CGameplayEntity )
	{
		IncreaseHitsCount( ST_Yrden );
		super.OnYrdenHit( caster );
	}
	
	event OnAxiiHit( sign : W3AxiiProjectile )
	{
		IncreaseHitsCount( ST_Axii );
		super.OnAxiiHit( sign );
	}
}
*/

class NGCL_AardOpenableDoor extends W3NewDoor {
	editable var isOpenableByAard : bool;
	editable var isSmoothOpenByAard : bool;
	editable var isOpenableByAardHits : int;
	editable var factOnOpenedByAard : String;
	protected var aardHitsCount : int;
	
	default isOpenableByAard = true;
	default isSmoothOpenByAard = true;
	default isOpenableByAardHits = 1;
	
	event OnAardHit( sign : W3AardProjectile )
	{
		var doorComponent : CDoorComponent;
		
		aardHitsCount += 1;
		NGCL_Notify_Shared("OnAardHit: aardHitsCount = " + aardHitsCount);
		if (isOpenableByAard && aardHitsCount >= isOpenableByAardHits) {
			doorComponent = (CDoorComponent)GetComponentByClassName( 'CDoorComponent' );
			doorComponent.SetEnabled( true );
			this.Unlock();
			if (isSmoothOpenByAard) {
				doorComponent.Open( true, true );
			} else {
				doorComponent.InstantOpen( true );
				// doorComponent.AddForceImpulse( sign.caster.GetWorldPosition(), 3000.0f );
			}
			if ( StrLen(factOnOpenedByAard) > 0 ) {
				FactsAdd( factOnOpenedByAard, 1 );
			}
		}
		super.OnAardHit( sign );
	}
}
