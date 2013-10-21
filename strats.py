from sim import *

################################################################################
## Strategies
################################################################################
def static1( synth ):
    order = [
    HastyTouch,
    HastyTouch,
    HastyTouch,
    MastersMend,

    HastyTouch,
    HastyTouch,
    HastyTouch,
    MastersMend,

    HastyTouch,
    HastyTouch,
    BasicSynthesis,
    BasicSynthesis,
    ]
    return order[ synth.step ]

def noTouch( synth ):
    if synth.progress < synth.progressMax:
        return BasicSynthesis

def dangerous( synth, synthSkill ):
    '''Use all cp on masters mend and all durability on hasty touch until finally doing synth'''
    if synth.cp >= 92 and synth.durabilityLost >= 30:
        return MastersMend
    if synth.stillPossibleToFinish( 1, 0, synthSkill() ):
        return HastyTouch
    return synthSkill

def dangerous_carefulSynth( synth ): return dangerous( synth, synthSkill=CarefulSynthesis )
def dangerous_basicSynth( synth ): return dangerous( synth, synthSkill=BasicSynthesis )

def smarter( synth ):
    synthSkill = CarefulSynthesis

    # absolute musts or we fail
    if synth.durability <= 10 and synth.cp >= MastersMend().cpCost:
        return MastersMend
    if synth.maxStepsLeft() == synth.minProgStepsLeft( synthSkill() ):
        return synthSkill

    # sanity checking
    if synthSkill != BasicSynthesis \
    and synth.maxStepsLeft() < synth.minProgStepsLeft( synthSkill() ):
        raise RuntimeError( 'Algo failed to stillPossibleToFinish checks' )


    spareCp = synth.cp % MastersMend().cpCost
    maxBasicsCanDo = spareCp / BasicTouch().cpCost
    maxNonProgSteps = synth.maxStepsLeft() - synth.minProgStepsLeft( synthSkill() )

    # InnerQuiet right away
    if synth.step == 0:
        return InnerQuiet

    # Try to restore cp if not on 2nd last step and can utilize the extra cp
    if synth.condition == 'Good':
        # if we can get an extra MastersMend
        if spareCp + 20 >= MastersMend().cpCost:
            return TricksOfTheTrade
        # if we can get an extra BasicTouch at the end
        if maxNonProgSteps > 1 and maxBasicsCanDo < maxNonProgSteps:
            return TricksOfTheTrade

        #return TricksOfTheTrade # [always TotT]

    # Use touches on good/excellent condition; favor the ones with better chance
    if synth.condition in [ 'Excellent', 'Good' ]:
        if synth.stillPossibleToFinish( 1, BasicTouch().cpCost, synthSkill() ): return BasicTouch
        return HastyTouch
    else:
        # if we can, try something else while the condition isn't useful
        if not synth.manipulationUsed and synth.cp >= Manipulation().cpCost:
            return Manipulation #TODO this is even better on Poor because then it's less likely to clash with TotT
        elif synth.durabilityLost >= 30 and synth.cp >= MastersMend().cpCost:
            return MastersMend
        elif synth.minProgStepsLeft( synthSkill() ) > 1:
            return synthSkill

    # Blow IQ stacks for either extra CP or a Byregot's
    if synth.innerQuiet \
    and synth.stillPossibleToFinish( 1, ByregotsBlessing().cpCost, synthSkill() ) \
    and maxNonProgSteps == 1:
        return ByregotsBlessing

    if synth.innerQuiet \
    and maxNonProgSteps < 4 \
    and spareCp + Rumination().amtRestorable( synth ) > MastersMend().cpCost \
    and True:
        return Rumination

    # aggressively use basic touch if have cp remaining that can't be used for masters mend and
    # you have enough to always have cp to afford a basic in case an Excellent comes up
    if synth.stillPossibleToFinish( 1, BasicTouch().cpCost, synthSkill() ) \
    and maxBasicsCanDo >= maxNonProgSteps:
        return BasicTouch

    return HastyTouch
