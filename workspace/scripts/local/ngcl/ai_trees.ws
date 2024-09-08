class NGCL_CAIMagicCastShield extends CAISpecialAction
{
	default aiTreeName = "dlc\dlcngcl\data\gameplay\ai_trees\npc_special_cast_shield.w2behtree";

	function Init()
	{
		params = new CAISpecialActionParams in this;
		params.OnCreated();
	}
}

class NGCL_CBTTaskCastShield extends CBTTaskCastSign
{
	public var completeAfterHit 				: bool;
	public var alternateFireMode 				: bool;
	public var processQuenOnCounterActivation : bool;
	public var sphereEntityTag 				: name;
	public var resourceNameHit 				: name;
	public var animEventStart 					: name;
	public var animEventThrow 					: name;
	public var animEventEnd 					: name;
	public var hitMaxCount 					: int;
	public var hitEventReceived				: bool;
	public var hitEffectName					: name;
	private var hitCounter 						: int;
	private var hitEntity 						: CEntity;
	private var hitEntityTemplate				: CEntityTemplate;
	private var shieldActive					: bool;
	
	protected var humanCombatDataStorage : CHumanAICombatStorage;
	
	function IsAvailable() : bool
	{
		if ( theGame.GetEntityByTag(sphereEntityTag) ) {
			return false;
		}
		return true;
	}

	function OnActivate() : EBTNodeStatus
	{
		var npc : CNewNPC = GetNPC();
		
		NNS("NGCL_CBTTaskCastShield: OnActivate");
		if( !IsNameValid(attackRangeName) )
			attackRangeName = 'quen';
		if( !IsNameValid(resourceName) )
			resourceName = 'quen';
		
		npc.SetGuarded(true);
		npc.SetParryEnabled( true );
		npc.customHits = true;
		npc.SetCanPlayHitAnim( true );
		
		npc.AddBuffImmunity( EET_Swarm, 'TaskCastQuen', false );
		npc.AddBuffImmunity( EET_Burning, 'TaskCastQuen', false );
		
		InitializeCombatDataStorage();
		humanCombatDataStorage.SetProtectedByQuen(true);
		shieldActive = true;
		
		return super.OnActivate();
	}
	
	latent function Main() : EBTNodeStatus
	{
		NNS("NGCL_CBTTaskCastShield: Main");
		hitEntityTemplate = (CEntityTemplate) LoadResourceAsync( resourceNameHit );

		super.Main();
		signEntity.AddTag(sphereEntityTag);
		return BTNS_Active;
	}
	
	function OnDeactivate()
	{
		var npc : CNewNPC = GetNPC();
		NNS("NGCL_CBTTaskCastShield: OnDeactivate");
		super.OnDeactivate();
		
		if( hitEntity )
		{
			hitEntity.DestroyAfter(3.0);
			hitEntity = NULL;
		}
		
		npc.SetGuarded(false);
		npc.SetParryEnabled( false );
		npc.customHits = false;
		
		npc.RemoveBuffImmunity( EET_Swarm, 'TaskCastQuen' );
		npc.RemoveBuffImmunity( EET_Burning, 'TaskCastQuen' );
		
		if ( signEntity )
			signEntity.BreakAttachment();
		
		humanCombatDataStorage.SetProtectedByQuen(false);
		shieldActive = false;
	}
	
	function Started()
	{
		if( signEntity )
		{
			if( alternateFireMode )
				signEntity.SetAlternateCast( S_Magic_s04 );
			signEntity.OnStarted();
		}
		super.Started();
	}
	
	function Throw()
	{
		if( signEntity )
		{
			signEntity.OnThrowing();
		}		
	}
	
	function Ended()
	{
		signEntity.StopAllEffects();
		signEntity.OnEnded();
		signEntity.RemoveTag(sphereEntityTag);
		signEntity.DestroyAfter(3.f);
		signEntity = NULL;
	}
	
	function ProcessAction( data : CDamageData )
	{
		var npc 	: CNewNPC = GetNPC();
		var params 	: SCustomEffectParams;
		
		if ( data.isActionMelee )
		{
			params.effectType = EET_Stagger;
			params.creator = GetActor();
			params.sourceName = "quen";
			params.duration = 0.1;
			
			((CActor)data.attacker).AddEffectCustom( params );
		}
		
		
	}
	
	function OnGameplayEvent( eventName : name ) : bool
	{
		var npc 	: CNewNPC = GetNPC();
		var data 	: CDamageData;
		
		if ( eventName == 'BeingHit' && shieldActive )
		{
			data = (CDamageData) GetEventParamBaseDamage();
			
			hitCounter += 1;
			PlayHitEffect( data );
			ProcessAction( data );
			super.Throw();
			
			if ( hitCounter > hitMaxCount || completeAfterHit )
			{
				Ended();
			}
			return true;
		}
		else if ( eventName == 'FinishQuen' )
		{
			Complete(true);
		}
		return false;
	}
	
	function OnListenedGameplayEvent( eventName : CName ) : bool
	{
		PlayHitEffect();
		super.Throw();
		return true;
	}
	
	function OnAnimEvent( animEventName : name, animEventType : EAnimationEventType, animInfo : SAnimationEventAnimInfo ) : bool
	{
		NNS("NGCL_CAIMagicCastShield: OnAnimEvent = " + animEventName);
		if ( animEventName == animEventStart )
		{
			Started();
		}
		else if ( animEventName == animEventThrow )
		{
			Throw();
		}
		else if ( animEventName == animEventEnd )
		{
			Ended();
		}
		return true;
	}
	
	private var playEffectTimeStamp : float;
	function PlayHitEffect( optional data : CDamageData )
	{
		
		var rot : EulerAngles;
		var localTime : float;
		
		localTime = GetLocalTime();
		
		if ( playEffectTimeStamp + 0.4 >= localTime )
			return;
		
		
		if ( data )
		{
			
			
			rot = VecToRotation ( data.attacker.GetWorldPosition() - data.victim.GetWorldPosition() );
			rot.Yaw -= 90;
		}
		else
		{
			
			rot.Pitch += 90;
		}
		
		hitEntity = theGame.CreateEntity( hitEntityTemplate, signEntity.GetWorldPosition(), rot );
		if(hitEntity)
		{
			hitEntity.CreateAttachment( GetActor(), 'quen_sphere' );
			
			hitEntity.PlayEffect( hitEffectName );
		}
		
		playEffectTimeStamp = localTime;
	}
	
	function SetupSignType()
	{
		signType = ST_Quen;
	}
	
	function InitializeCombatDataStorage()
	{
		if ( !humanCombatDataStorage )
		{
			super.InitializeCombatDataStorage();
			humanCombatDataStorage = (CHumanAICombatStorage)combatDataStorage;
		}
	}
};

class NGCL_CBTTaskCastShieldDef extends CBTTaskCastSignDef
{
	default instanceClass = 'NGCL_CBTTaskCastShield';

	editable var completeAfterHit : bool;
	editable var alternateFireMode : bool;
	editable var processQuenOnCounterActivation : bool;
	editable var resourceName 					: name;
	editable var resourceNameHit 				: name;
	editable var animEventStart 				: name;
	editable var animEventThrow 				: name;
	editable var animEventEnd 					: name;
	editable var hitEffectName					: name;
	editable var hitMaxCount					: int;
	editable var sphereEntityTag				: name;
	
	function InitializeEvents()
	{
		super.InitializeEvents();
		listenToGameplayEvents.PushBack( 'CustomHit' );
	}
};
