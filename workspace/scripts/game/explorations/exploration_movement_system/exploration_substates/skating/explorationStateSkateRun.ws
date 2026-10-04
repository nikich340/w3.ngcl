// CExplorationStateSkatingRun
//------------------------------------------------------------------------------------------------------------------
// Eduard Lopez Plans	( 03/02/2014 )	 
//------------------------------------------------------------------------------------------------------------------


//>-----------------------------------------------------------------------------------------------------------------
//------------------------------------------------------------------------------------------------------------------
class CExplorationStateSkatingRun extends CExplorationStateAbstract
{		
	// Speed levels
	private	var	skateGlobal		: CExplorationSkatingGlobal;
	
	private	var m_Sprinting		: bool;
	
	//rs: allow setting of parameters for skate running
	protected editable	inlined	var baseParamsRun		: SSkatingMovementParams;

	
	//---------------------------------------------------------------------------------
	private function InitializeSpecific( _Exploration : CExplorationStateManager )
	{	
		if( !IsNameValid( m_StateNameN ) )
		{
			m_StateNameN	= 'SkateRun';
		}		
		
		skateGlobal	= _Exploration.m_SharedDataO.m_SkateGlobalC;
		

		//rs: set the params
		baseParamsRun.decel = 0.05f; //base decel when letting go of the controls
		baseParamsRun.decelMaxSpeed = 0.07f; // how much it will try to decel when above the max speed at the current speed level
		baseParamsRun.brake = 1.0f; //braking factor(multiplied by how much you are pushing the controls back and the maximum of your current speed or brakeBaseSpeed)
		baseParamsRun.brakeBaseSpeed = 2.0f; // brakeBaseSpeed (see above)
		baseParamsRun.frictionSquare = 0.0f; //decel due to friction times the square of your current speed
		baseParamsRun.frictionLinear = 0.0f; //decel due to friction times your current speed(adds to above)
		baseParamsRun.frictionConst = 0.01f;//decel due to friction constant(adds to above)


		// Set the type
		m_InputContextE = EGCI_Skating;
		m_StateTypeE	= EST_Skate;
	}
	
	//---------------------------------------------------------------------------------
	private function AddDefaultStateChangesSpecific()
	{
		//AddStateToTheDefaultChangeList( 'SkateJump' );
		//rs: Remove Hits for now from all states. Too buggy
		//AddStateToTheDefaultChangeList( 'SkateHitLateral' );
		//rs
		//AddStateToTheDefaultChangeList( 'SkateBackwards' );
		AddStateToTheDefaultChangeList( 'SkateSlide' );
		AddStateToTheDefaultChangeList( 'SkateStopFast' );
		AddStateToTheDefaultChangeList( 'SkateDrift' );
		AddStateToTheDefaultChangeList( 'SkateDashAttack' );
		AddStateToTheDefaultChangeList( 'SkateDash' );
	}

	//---------------------------------------------------------------------------------
	function StateWantsToEnter() : bool
	{	
		return m_ExplorationO.m_InputO.IsModuleConsiderable();
	}
	
	//---------------------------------------------------------------------------------
	function StateCanEnter( curStateName : name ) : bool
	{	
		return true;
	}
	
	//---------------------------------------------------------------------------------
	private function StateEnterSpecific( prevStateName : name )	
	{
		// Set the default params again
		//rs: apply our custom params
		m_ExplorationO.m_MoverO.SetSkatingParams( baseParamsRun );
		m_ExplorationO.m_MoverO.SetSkatingTurnSpeed( 150.0f );
		//skateGlobal.ApplyDefaultParams( );
		skateGlobal.ApplyCurLevelParams( );
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
		
		//LogChannel('BRAKING',braking);

		// Attack
		skateGlobal.UpdateRandomAttack();
		
		// Movement
		UpdateBaseSpeed();
		
		m_ExplorationO.m_MoverO.UpdateSkatingMovement( _Dt, accel, turn, braking );
		
		// Anim		
		skateGlobal.SetBehParams( accel, braking, turn );
		
		// Iddle?
		if( skateGlobal.ShouldStop( braking ) )
		{
			SetReadyToChangeTo( 'SkateIdle' );
		}
		
		//ngcl
		if( m_ExplorationO.m_InputO.IsSkateResetJustPressed() )
		{
			SkateReset();
			SetReadyToChangeTo( 'SkateIdle' );
			//theGame.witcherLog.AddMessage("RESET!");
		}
		
	}
	
	//---------------------------------------------------------------------------------
	private function StateExitSpecific( nextStateName : name )
	{		
		thePlayer.SetBIsCombatActionAllowed( true );
	}
	
	//---------------------------------------------------------------------------------
	private function UpdateBaseSpeed()
	{
		//rs: replace dash with sprint key to add sprint functionality
		//if( m_ExplorationO.m_InputO.IsDashPressed() )
		if( m_ExplorationO.m_InputO.IsSprintPressed() )
		{
			if( !m_Sprinting )
			{
				LogChannel('Sprint','Sprinted');
				m_Sprinting	= true;
				skateGlobal.SetSpeedLevel( 1, true );
			}
		}
		else if( m_Sprinting )
		{
			LogChannel('Unsprinted','Unsprinted');
			m_Sprinting	= false;
			skateGlobal.SetSpeedLevel( 0, true );
		}
		
	}
	
	//---------------------------------------------------------------------------------
	// Collision events
	//---------------------------------------------------------------------------------
	
	//---------------------------------------------------------------------------------
	function ReactToLoseGround() : bool
	{
		//ngcl
		//SetReadyToChangeTo( 'StartFalling' );
		
		return false;
	}
	
	//---------------------------------------------------------------------------------
	function ReactToHitGround() : bool
	{		
		return true;
	}	
	
	//---------------------------------------------------------------------------------
	function CanInteract( ) :bool
	{		
		return false;
	}
}