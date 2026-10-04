// CExplorationStateSkateSlide
//------------------------------------------------------------------------------------------------------------------
// Eduard Lopez Plans	( 11/02/2014 )	 

//>-----------------------------------------------------------------------------------------------------------------
//------------------------------------------------------------------------------------------------------------------
class CExplorationStateSkateSlide extends CExplorationStateSkatingDrift
{			
	private editable	var inputRangeToEnter		: float;		default inputRangeToEnter	= 15.0f;
	private editable	var height					: float;		default height				= 1.0f;
	protected editable	inlined	var baseParamsSlide		: SSkatingMovementParams;
	
	
	//---------------------------------------------------------------------------------
	private function InitializeSpecific( _Exploration : CExplorationStateManager )
	{	
		if( !IsNameValid( m_StateNameN ) )
		{
			m_StateNameN	= 'SkateSlide';
		}
		
		skateGlobal	= _Exploration.m_SharedDataO.m_SkateGlobalC;
		
		// Set the type
		m_InputContextE = EGCI_Skating;
		m_StateTypeE	= EST_Skate;


		// Tweak the params
		//rs: restore tweaking of params
		baseParamsSlide.accel	= 0.0f;
		baseParamsSlide.decel = 0.05f; //base decel when letting go of the controls
		baseParamsSlide.decelMaxSpeed = 0.1f; // how much it will try to decel when above the max speed at the current speed level
		baseParamsSlide.frictionSquare = 0.0f; //decel due to friction times the square of your current speed
		baseParamsSlide.frictionLinear = 0.0f; //decel due to friction times your current speed(adds to above)
		baseParamsSlide.frictionConst = 0.75f;//decel due to friction constant(adds to above)
	}
	
	//---------------------------------------------------------------------------------
	private function AddDefaultStateChangesSpecific()
	{		
		AddStateToTheDefaultChangeList( 'SkateDashAttack' );
		AddStateToTheDefaultChangeList( 'SkateDash' );
		//AddStateToTheDefaultChangeList( 'SkateJump' );
		//AddStateToTheDefaultChangeList( 'SkateHitLateral' );
	}

	//---------------------------------------------------------------------------------
	function StateWantsToEnter() : bool
	{	
		var inputHeadingAbs	: float;
		
		if( skateGlobal.ShouldStop( true ) )
		{
			return false;
		}
		
		inputHeadingAbs	= m_ExplorationO.m_InputO.GetHeadingOnPadF();
		inputHeadingAbs	= AbsF( inputHeadingAbs );
		
		if( !m_ExplorationO.m_InputO.IsModuleConsiderable() || inputHeadingAbs < inputRangeToEnter )// AbsF( m_ExplorationO.m_InputO.GetHeadingDiffFromPlayerF() ) < inputRangeToEnter )
		{
			return m_ExplorationO.m_InputO.IsDriftPressed();
		}
		
		return false;
	}
	
	//---------------------------------------------------------------------------------
	protected function StateEnterSpecific( prevStateName : name )
	{
		m_ExplorationO.m_OwnerMAC.SetHeight( height );
		
		super.StateEnterSpecific( prevStateName );
		
		// Not exactly drifting
		m_ExplorationO.m_MoverO.SetSkatingParams( baseParamsSlide );
		skateGlobal.m_Drifting = false;		
	}
	
	//---------------------------------------------------------------------------------
	protected function StateUpdateSpecific( _Dt : float )
	{		
		var accel	: float;
		var turn	: float;
		var braking	: bool;
		
		
		// Attack
		skateGlobal.UpdateRandomAttack();
		
		// Movement
		m_ExplorationO.m_MoverO.UpdateSkatingMovement( _Dt, accel, turn, braking );
		
		
		// Exiting?
		UpdateExit( _Dt, braking );
	}
	
	//---------------------------------------------------------------------------------
	protected function StateExitSpecific( nextStateName : name )
	{
		m_ExplorationO.m_OwnerMAC.ResetHeight( );
		
		super.StateExitSpecific( nextStateName );
	}
}