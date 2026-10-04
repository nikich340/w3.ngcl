// CExplorationStateSkatingDash
//------------------------------------------------------------------------------------------------------------------
// Eduard Lopez Plans	( 04/02/2014 )	 
//------------------------------------------------------------------------------------------------------------------


//>-----------------------------------------------------------------------------------------------------------------
//------------------------------------------------------------------------------------------------------------------
class CExplorationStateSkatingDash extends CExplorationStateAbstract
{		
	protected					var	skateGlobal			: CExplorationSkatingGlobal;
	
	// Speed
	protected editable			var impulse				: float;		default	impulse					= 3.0f;
	protected editable			var timeMax				: float;		default	timeMax					= 0.75f;
	protected editable			var timeToChainMin		: float;		default	timeToChainMin			= 0.2f;	
	
	
	// Turn
	protected editable			var sharpTurnSpeed		: float;		default	sharpTurnSpeed			= 300.0f;
	protected editable			var holdTurnSpeed		: float;		default	holdTurnSpeed			= 80.0f;
	protected					var sharpTurn			: bool;	
	protected editable			var sharpTurnTime		: float;		default	sharpTurnTime			= 0.2f;
	
	
	// Attack
	protected editable			var behAttackEvent		: name;			default	behAttackEvent			= 'Skate_Attack';
	protected editable			var behLeftFootParam	: name;			default	behLeftFootParam		= 'Skate_LeftFoot';
	
	
	// Bones
	protected 					var	boneRightFoot		: name;			default	boneRightFoot			= 'r_foot';
	protected 					var	boneLeftFoot		: name;			default	boneLeftFoot			= 'l_foot';
	protected 					var	boneIndexRightFoot	: int;
	protected 					var	boneIndexLeftFoot	: int;
	
	
	//Beh
	private editable			var behEventEnd			: name;			default	behEventEnd			= 'AnimEndAUX';
	
	
	//---------------------------------------------------------------------------------
	protected function InitializeSpecific( _Exploration : CExplorationStateManager )
	{	
		if( !IsNameValid( m_StateNameN ) )
		{
			m_StateNameN	= 'SkateDash';
		}
		
		skateGlobal	= _Exploration.m_SharedDataO.m_SkateGlobalC;
		
		
		// Get and store bone indexes
		boneIndexRightFoot	= m_ExplorationO.m_OwnerE.GetBoneIndex( boneRightFoot );
		boneIndexLeftFoot	= m_ExplorationO.m_OwnerE.GetBoneIndex( boneLeftFoot );
		
		
		// Set the type
		m_InputContextE = EGCI_Skating;
		m_StateTypeE			= EST_Skate;
		m_UpdatesWhileInactiveB	= true;
	}
	
	//---------------------------------------------------------------------------------
	private function AddDefaultStateChangesSpecific()
	{
		//AddStateToTheDefaultChangeList( 'SkateSlide' );
		////AddStateToTheDefaultChangeList( 'SkateStopFast' );
		//AddStateToTheDefaultChangeList( 'SkateDrift' );
		//AddStateToTheDefaultChangeList( 'SkateBackwards' );
		AddStateToTheDefaultChangeList( 'SkateDashAttack' );
		AddStateToTheDefaultChangeList( 'SkateJump' );
		//AddStateToTheDefaultChangeList( 'SkateHitLateral' );
	}

	//---------------------------------------------------------------------------------
	function StateWantsToEnter() : bool
	{	
		return m_ExplorationO.m_InputO.IsDashJustPressed();
	}
	
	//---------------------------------------------------------------------------------
	function StateCanEnter( curStateName : name ) : bool
	{	
		
		if( !HasEnoughStamina() )
		{
			LogChannel('NO','STAMINA');
			return false;
		}
		

		
		return skateGlobal.IsDashReady();
	}
	
	//---------------------------------------------------------------------------------
	protected function StateEnterSpecific( prevStateName : name )	
	{		
		var finalImpulse	: float;
		
		//rs: Restore the original dash flow system from comments.
		// Dash increases one level
		
		
		// Perfect Flow
		
		
		
		// Impulse not exceeding max
		//ngcl
		if( m_StateNameN != 'SkateDashAttack')
		{
			if( skateGlobal.CheckIfIsInFlowGapAndConsume() )
			{
				skateGlobal.IncreaseSpeedLevel( true, true );
			}
			else
			{
				skateGlobal.IncreaseSpeedLevel( true, false );
			}
			skateGlobal.ImpulseToNextSpeedLevel( impulse );
		}
		
		//rs: Remove "final impulse": not needed
		//finalImpulse	= skateGlobal.ImpulseToNextSpeedLevel( impulse );
		//m_ExplorationO.m_MoverO.AddSpeed( finalImpulse );
		
		//rs: remove debug behavior
		// Increases to the max level
		//skateGlobal.SetSpeedLevel( 1, true );
		//skateGlobal.ImpulseNotExceedingMaxSpeedLevel( impulse );

		//rs: Hack combat log to add messages for speed level
		//theGame.witcherLog.AddMessage("Speed Level:"+skateGlobal.GetSpeedLevel());
		//theGame.witcherLog.AddMessage("Current Max Speed:"+skateGlobal.GetSpeedMaxCur());
		
		// Stamina
		BlockStamina();
		
		// Turn
		m_ExplorationO.m_MoverO.SetSkatingTurnSpeed( sharpTurnSpeed );
		sharpTurn		= true;
		
		// Set the foot
		SetTheForwardFoot();
	}
	
	//---------------------------------------------------------------------------------
	function StateChangePrecheck( )	: name
	{
		if( m_ExplorationO.GetStateTimeF() > timeMax )
		{
			return 'SkateRun';
		}
		// Don't allow for auto state changes if the time is not enough
		else if( m_ExplorationO.GetStateTimeF() < timeToChainMin )
		{
			return GetStateName();
		}
		
		
		return super.StateChangePrecheck();
	}
	
	//---------------------------------------------------------------------------------
	protected function StateUpdateSpecific( _Dt : float )
	{		
		var accel	: float;
		var turn	: float;
		var braking	: bool;
		
		
		// Attack
		skateGlobal.UpdateRandomAttack();
		//skateGlobal.UpdateDashAttack();
		
		// Sharp turn
		if( sharpTurn && m_ExplorationO.GetStateTimeF() >= sharpTurnTime )
		{
			// rs: quick fix as we are using custom params for running rather than default for now so we don't overwrite
			//skateGlobal.ApplyDefaultParams();
			m_ExplorationO.m_MoverO.SetSkatingTurnSpeed( 170.0f);
			sharpTurn	= false;
		}
		
		// Movement
		m_ExplorationO.m_MoverO.UpdateSkatingMovement( _Dt, accel, turn, braking );
		
		// Anim
		skateGlobal.SetBehParams( accel, braking, turn );
	}

	//---------------------------------------------------------------------------------
	function StateUpdateInactive( _Dt : float )
	{
		skateGlobal.UpdateDashCooldown( _Dt );
	}
	
	//---------------------------------------------------------------------------------
	private function StateExitSpecific( nextStateName : name )
	{		
		skateGlobal.ConsumeDashCooldown();
		skateGlobal.StartFlowTimeGap();
	}	
	
	//---------------------------------------------------------------------------------
	private function SetTheForwardFoot()
	{
		var startRightFoot	: bool;
		
		startRightFoot	= m_ExplorationO.m_MoverO.IsRightFootForward();
		
		m_ExplorationO.SetBehaviorParamBool( behLeftFootParam, !startRightFoot );
	}	
	
	//---------------------------------------------------------------------------------
	private function HasEnoughStamina() : bool
	{
		/*
		var res : bool;
		//rs: re do check for stamina
		res = GetCiriPlayer().GetStatPercents( BCS_Stamina ) >= (GetCiriPlayer().GetStatMax(BCS_Stamina)*(0.5))*0.01;
		
		if ( !res )
		{
			theGame.witcherLog.AddMessage("Not Enough Stamina!");
			GetCiriPlayer().SetShowToLowStaminaIndication(GetCiriPlayer().GetStatMax(BCS_Stamina));
			//theSound.SoundEvent( "gui_ingame_low_stamina_warning" );
		}
		
		return res;
		*/
		return thePlayer.HasStaminaToUseAction( ESAT_UsableItem  );
	}
	
	//---------------------------------------------------------------------------------
	private function BlockStamina()
	{
		//rs: re do drain stamina
		//GetCiriPlayer().DrainStamina(ESAT_FixedValue, GetCiriPlayer().GetStatMax(BCS_Stamina)*(0.5));
		thePlayer.DrainStamina(ESAT_UsableItem);
	}
	
	//---------------------------------------------------------------------------------
	// Anim events
	//---------------------------------------------------------------------------------
	
	//------------------------------------------------------------------------------------------------------------------
	function OnAnimEvent( animEventName : name, animEventType : EAnimationEventType, animInfo : SAnimationEventAnimInfo )
	{
		if( animEventName	== behEventEnd )
		{		
			m_ExplorationO.m_MoverO.SetSpeedFromAnim();
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

	//rs: Use this for messages: formats float to string
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
