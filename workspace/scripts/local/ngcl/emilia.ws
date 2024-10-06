statemachine class NGCL_EmiliaNPC extends CNewNPC {
	protected editable var shieldEffectName : name;
	protected editable var shieldBreakEffectName : name;
	protected editable var shieldActivateInterval : float;
	protected editable var shouldUseShield : bool;
	protected var shieldActive : bool;
	protected var savedInteractionPriority : EInteractionPriority;
	
	default shouldUseShield = true;
	default shieldActivateInterval = 20.f;
	default shieldEffectName = 'quen_lasting_shield';
	default shieldBreakEffectName = 'quen_electric_explode_bear_abl2';
	
	protected function OnCombatModeSet( toggle : bool )
	{
		super.OnCombatModeSet( toggle );
		if (toggle && shouldUseShield && !shieldActive) {
			ActivateShield(0.f, 0);
		} else if (!toggle && shieldActive) {
			DeactivateShield(false);
		}
	}
	
	timer function ActivateShield(delta : float, id : int) {
		var combatStorage  : CHumanAICombatStorage;
		
		if ( !IsAlive() )
			return;
		
		shieldActive = true;
		PlayEffect(shieldEffectName);
		AddBuffImmunity_AllNegative('MagicShield', true);
		/*
		AddBuffImmunity( EET_Swarm, 'MagicShield', true );
		AddBuffImmunity( EET_Burning, 'MagicShield', true );
		AddBuffImmunity( EET_Bleeding, 'MagicShield', true );
		AddBuffImmunity( EET_Poison, 'MagicShield', true );
		AddBuffImmunity( EET_PoisonCritical, 'MagicShield', true );
		*/
		SetImmortalityMode( AIM_Invulnerable, AIC_Default );
		SetImmortalityMode( AIM_Invulnerable, AIC_Combat );
		SetCanPlayHitAnim( false );
		SetUnstoppable( true );
		savedInteractionPriority = GetInteractionPriority();
		SetInteractionPriority( IP_Max_Unpushable );
		combatStorage = (CHumanAICombatStorage)GetScriptStorageObject('CombatData');
		combatStorage.SetProtectedByQuen(true);
	}
	
	public function DeactivateShield(breakShield : bool) {
		var combatStorage  : CHumanAICombatStorage;
		
		shieldActive = false;
		if (breakShield)
			PlayEffect(shieldBreakEffectName);
		StopEffect(shieldEffectName);
		RemoveBuffImmunity_AllNegative('MagicShield');
		SetImmortalityMode( AIM_None, AIC_Default );
		SetImmortalityMode( AIM_None, AIC_Combat );
		SetCanPlayHitAnim( true );
		SetUnstoppable( false );
		SetInteractionPriority( savedInteractionPriority );
		combatStorage = (CHumanAICombatStorage)GetScriptStorageObject('CombatData');
		combatStorage.SetProtectedByQuen(false);
	}
	
	public function ReactToBeingHit(damageAction : W3DamageAction, optional buffNotApplied : bool) : bool {
		var attacker : CActor;
		var shieldDamage : W3DamageAction;
		
		if (shieldActive) {
			attacker = (CActor)damageAction.attacker;
			if ( attacker && damageAction.IsActionMelee() ) {
				shieldDamage = new W3DamageAction in this;
				shieldDamage.Initialize( this, attacker, this, this.GetName(), EHRT_Light, CPS_SpellPower, false, false, false, true );
				shieldDamage.AddDamage( theGame.params.DAMAGE_NAME_ELEMENTAL, attacker.GetMaxHealth() * 0.03f );
				shieldDamage.AddEffectInfo(EET_Stagger, 2.f);
				theGame.damageMgr.ProcessAction( shieldDamage );
				delete shieldDamage;
			}
			if ( !damageAction.IsDoTDamage() && !damageAction.WasDodged() ) {
				DeactivateShield(true);
				AddTimer('ActivateShield', shieldActivateInterval * (1.f + RandRangeF(0.2, -0.2)), /*repeats*/ false);
			}
			damageAction.ClearDamage();
			damageAction.ClearEffects();
			return false;
		}
		return super.ReactToBeingHit(damageAction, buffNotApplied);
	}
}
