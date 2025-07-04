// CExplorationStateSkatingDash
//------------------------------------------------------------------------------------------------------------------
// Eduard Lopez Plans	( 14/05/2014 )	 
//------------------------------------------------------------------------------------------------------------------


//>-----------------------------------------------------------------------------------------------------------------
//------------------------------------------------------------------------------------------------------------------
class CExplorationStateSkatingDashAttack extends CExplorationStateSkatingDash
{
	private 			var attacked			: bool;
	private editable	var	afterAttackTime		: float;	default	afterAttackTime		= 0.5f;
	private 			var timeToEndCur		: float;
	public	editable 	var	behParamAttackName	: name;		default	behParamAttackName	= 'Skate_Attack';
	
	private editable	var	afterAttackImpulse	: float;	default	afterAttackImpulse	= 0.0f; //ngcl
	

	//---------------------------------------------------------------------------------
	private function InitializeSpecific( _Exploration : CExplorationStateManager )
	{	
		if( !IsNameValid( m_StateNameN ) )
		{
			m_StateNameN	= 'SkateDashAttack';
		}
		
		super.InitializeSpecific( _Exploration );
	}
	
	//---------------------------------------------------------------------------------
	private function AddDefaultStateChangesSpecific()
	{
		//AddStateToTheDefaultChangeList( 'SkateSlide' );
		////AddStateToTheDefaultChangeList( 'SkateStopFast' );
		//AddStateToTheDefaultChangeList( 'SkateDrift' );
		//AddStateToTheDefaultChangeList( 'SkateBackwards' );
		AddStateToTheDefaultChangeList( 'SkateJump' );
		//AddStateToTheDefaultChangeList( 'SkateHitLateral' );
	}
	
	//---------------------------------------------------------------------------------
	function StateWantsToEnter() : bool
	{	
		return m_ExplorationO.m_InputO.IsSkateAttackJustPressed();
	}
	
	//---------------------------------------------------------------------------------
	protected function StateEnterSpecific( prevStateName : name )	
	{
		attacked	= false;
		
		super.StateEnterSpecific( prevStateName );
	}
	
	//---------------------------------------------------------------------------------
	function StateChangePrecheck( )	: name
	{
		return super.StateChangePrecheck();
	}
	
	//---------------------------------------------------------------------------------
	protected function StateUpdateSpecific( _Dt : float )
	{		
		var accel	: float;
		var turn	: float;
		var braking	: bool;
		
		
		UpdateAttack( _Dt );
		
		super.StateUpdateSpecific( _Dt );
	}
	
	//---------------------------------------------------------------------------------
	private function UpdateAttack( _Dt : float )
	{
		if( attacked )
		{
			timeToEndCur -= _Dt;
			if( timeToEndCur <= 0.0f )
			{
				SetReadyToChangeTo( 'SkateRun' );
			}
		}
		
		//rs: Make this function more reliable and add messages to indicate attack
		else if( !m_ExplorationO.m_InputO.IsSkateAttackPressedInTime(0.3f) )
		{
			//theGame.witcherLog.AddMessage('ATTACK');
			m_ExplorationO.SendAnimEvent( behParamAttackName );
			//skateGlobal.UpdateDashAttack();
			attacked		= true;
			timeToEndCur	= afterAttackTime;
			skateGlobal.ImpulseNotExceedingMaxSpeedLevel( afterAttackImpulse );
			
			
			// Push enemies while attacking
			((CActor) thePlayer ).SetInteractionPriority( IP_Prio_14 );
		}
	}
	
	//---------------------------------------------------------------------------------
	private function StateExitSpecific( nextStateName : name )
	{
		// Push enemies while attacking
		((CActor) thePlayer ).SetInteractionPriority( IP_Prio_0 );
	}
}