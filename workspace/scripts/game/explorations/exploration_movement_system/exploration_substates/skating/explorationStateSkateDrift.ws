// CExplorationSkatingDrift
//------------------------------------------------------------------------------------------------------------------
// Eduard Lopez Plans	( 04/02/2014 )	 
//------------------------------------------------------------------------------------------------------------------

//>-----------------------------------------------------------------------------------------------------------------
//------------------------------------------------------------------------------------------------------------------
class CExplorationStateSkatingDrift extends CExplorationStateAbstract
{		
	protected					var	skateGlobal			: CExplorationSkatingGlobal;
	
	protected editable	inlined	var baseParamsDrift		: SSkatingMovementParams;
	
	protected editable			var impulse				: float;					default	impulse				= 0.75f;
	protected editable			var impulseSpeedMax		: float;					default	impulseSpeedMax		= 8.0f;
	
	// Sharp / normal turn
	protected					var sharpTurn			: bool;	
	protected editable			var sharpTurnTime		: float;					default	sharpTurnTime		= 0.15f;
	protected editable			var sharpTurnSpeed		: float;					default sharpTurnSpeed		= 70.0f;//rs: lower the turn speed 100.0f;
	protected editable			var holdTurnSpeed		: float;					default holdTurnSpeed		= 70.0f;
	
	// Chain
	protected editable			var chainTimeToDrift	: float;					default	chainTimeToDrift	= 0.2f;
	
	// Ending
	protected 					var exiting				: bool;	
	protected editable			var timeEndingMax		: float;					default	timeEndingMax		= 0.2f;
	protected 					var timeEndingFlow		: bool;
	protected					var	timeEndingCur		: float;
	
	protected editable			var behDriftRestart		: name;						default	behDriftRestart		= 'Skate_DriftRestart';
	protected editable			var behDriftEnd			: name;						default	behDriftEnd			= 'Skate_DriftEnd';
	protected editable			var behDriftLeftSide	: name;						default	behDriftLeftSide	= 'Skate_DriftLeft';
	
	// Side locked
	protected 					var sideIsLeft			: bool;	
	
	
	//---------------------------------------------------------------------------------
	private function InitializeSpecific( _Exploration : CExplorationStateManager )
	{	
		if( !IsNameValid( m_StateNameN ) )
		{
			m_StateNameN	= 'SkateDrift';
		}
		
		skateGlobal	= _Exploration.m_SharedDataO.m_SkateGlobalC;
		
		// Set the type
		m_InputContextE = EGCI_Skating;
		m_StateTypeE	= EST_Skate;
		
		// Tweak the params
		//rs: restore tweaking of params
		baseParamsDrift.accel	= 0.0f;
		baseParamsDrift.decel = 0.05f; //base decel when letting go of the controls
		baseParamsDrift.decelMaxSpeed = 0.1f; // how much it will try to decel when above the max speed at the current speed level
		baseParamsDrift.frictionSquare = 0.0f; //decel due to friction times the square of your current speed
		baseParamsDrift.frictionLinear = 0.0f; //decel due to friction times your current speed(adds to above)
		baseParamsDrift.frictionConst = 0.7f;//decel due to friction constant(adds to above)
	}
	
	//---------------------------------------------------------------------------------
	private function AddDefaultStateChangesSpecific()
	{		
		AddStateToTheDefaultChangeList( 'SkateDash' );
		//AddStateToTheDefaultChangeList( 'SkateBackwards' );
		//AddStateToTheDefaultChangeList( 'SkateJump' );
		//AddStateToTheDefaultChangeList( 'SkateHitLateral' );
	}

	//---------------------------------------------------------------------------------
	function StateWantsToEnter() : bool
	{	
		if( skateGlobal.ShouldStop( true ) )
		{
			return false;
		}
		
		return m_ExplorationO.m_InputO.IsDriftPressed();
	}
	
	//---------------------------------------------------------------------------------
	function StateCanEnter( curStateName : name ) : bool
	{	
		return true;
	}
	
	//---------------------------------------------------------------------------------
	protected function StateEnterSpecific( prevStateName : name )	
	{		
		var impulseResulting	: float;
		
		// Get the side
		sideIsLeft		= m_ExplorationO.m_InputO.GetHeadingDiffFromPlayerF() < 0.0f;
		skateGlobal.m_DrifIsLeft	= sideIsLeft;
		m_ExplorationO.SetBehaviorParamBool( behDriftLeftSide, !sideIsLeft );
		
		//Impulse
		impulseResulting	= MaxF( 0.0f, impulseSpeedMax - m_ExplorationO.m_MoverO.GetMovementSpeedF() );
		//rs: corrected - into -= ?????
		impulseResulting	-= MinF( impulse, impulseResulting );
		m_ExplorationO.m_MoverO.AddSpeed( impulseResulting );
		//theGame.witcherLog.AddMessage("Resulting Impulse "+FormatF(impulseResulting));
		
		// Perfect Flow
		if( skateGlobal.CheckIfIsInFlowGapAndConsume() )
		{
			//rs: Add messages for testing
			//LogChannel('DRIFTFLOW','PERFECT');
			//theGame.witcherLog.AddMessage("Perfect Drift Flow!");
			skateGlobal.DecreaseSpeedLevel( true, false );
		}
		// No flow
		else
		{
			//rs: Add messages for testing
			//LogChannel('DRIFTFLOW','IMPERFECT');
			//theGame.witcherLog.AddMessage("Bad Drift Flow!");
			skateGlobal.DecreaseSpeedLevel( false, true );
			//skateGlobal.DecreaseSpeedLevel( false, false );
		}
		
		m_ExplorationO.m_MoverO.SetSkatingParams( baseParamsDrift );
		m_ExplorationO.m_MoverO.SetSkatingTurnSpeed( sharpTurnSpeed );
		
		exiting					= false;
		timeEndingCur			= 0.0f;
		sharpTurn				= true; //not used by CDPR
		timeEndingFlow			= false; 
		skateGlobal.m_Drifting	= true;//not used by CDPR


		
	}
	
	//---------------------------------------------------------------------------------
	function StateChangePrecheck( )	: name
	{
		if( timeEndingCur > timeEndingMax )
		{
			return 'SkateRun';
		}
		
		return super.StateChangePrecheck();
	}
	
	//---------------------------------------------------------------------------------
	protected function StateUpdateSpecific( _Dt : float )
	{		
		var accel	: float;
		var turn	: float;
		var braking	: bool;
		var camera	: CCustomCamera = theGame.GetGameCamera();
		
		// Attack
		skateGlobal.UpdateRandomAttack();
		
		// Movement
		m_ExplorationO.m_MoverO.UpdateSkatingMovement( _Dt, accel, turn, braking, true, sideIsLeft );
		
		// Exit or not exit
		UpdateExit( _Dt, braking );
		
		// Anim		
		skateGlobal.SetBehParams( accel, braking, turn );

		//rs: try implement camera - Now working automatically. Use this if it is not for some reason
		//camera.ChangePivotPositionController( 'Slide');
		//LogChannel('CURRENTCONTROLLER',camera.GetActivePivotPositionController().controllerName);
		//camera.ChangePivotRotationController( 'SkateDrift' );
		//LogChannel('CURRENTCONTROLLER',camera.GetActivePivotRotationController().controllerName);
	}
	
	//---------------------------------------------------------------------------------
	protected function StateExitSpecific( nextStateName : name )
	{		
		skateGlobal.m_Drifting	= false;
		skateGlobal.StartFlowTimeGap();
	}	
	
	//---------------------------------------------------------------------------------
	protected function UpdateExit( _Dt : float, braking : bool )
	{
		// Iddle?
		if( skateGlobal.ShouldStop( braking ) )
		{
			SetReadyToChangeTo( 'SkateIdle' );
		}
		
		// Exit time
		if( StateWantsToEnter() )
		{

			if( timeEndingCur > 0.0f  )
			{
				// Go to run so we can reenter the state
				if( m_ExplorationO.GetStateTimeF() >= chainTimeToDrift )
				{
					SetReadyToChangeTo(	'SkateRun' );
				}
				
				skateGlobal.CancelFlowTimeGap();
				m_ExplorationO.SendAnimEvent( behDriftRestart );
				
				timeEndingCur	= 0.0f;
				skateGlobal.m_Drifting	= true;
				//rs: Message for restart indication
				//theGame.witcherLog.AddMessage("RESTARTED DRIFT!");
			}
		}
		else
		{
			timeEndingCur	+= _Dt;
			if( !timeEndingFlow && timeEndingCur > timeEndingMax - skateGlobal.GetMaxFlowTimeGap() )
			{
				//rs: Message for end indication
				//theGame.witcherLog.AddMessage("ENDED DRIFT!");
				timeEndingFlow	= true;
				m_ExplorationO.SendAnimEvent( behDriftEnd );
				skateGlobal.m_Drifting	= false;
			}
		}
	}
	
	//---------------------------------------------------------------------------------
	// Collision events
	//---------------------------------------------------------------------------------
	
	//---------------------------------------------------------------------------------
	function ReactToLoseGround() : bool
	{
		SetReadyToChangeTo( 'StartFalling' );
		
		return true;
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

	//rs: Maybe needed for testing: formats float to string
	public function FormatF(f : float) : string
	{
		var str : string;
		var temp : float;
		
		temp = RoundTo(f, 2);
		str = NoTrailZeros(temp);
		str = "<font size=\"20\">" + str + "</font>";
		
		return str;
	}
}