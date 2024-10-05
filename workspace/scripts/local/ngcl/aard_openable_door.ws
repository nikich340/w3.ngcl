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
		// NNS("OnAardHit: aardHitsCount = " + aardHitsCount);
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
	}
}