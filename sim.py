import copy
from math import ceil
from random import random
import types

################################################################################
## Synth state
################################################################################

SynthConditionMult = { 'Normal':1.0, 'Good':1.5, 'Excellent':2.50, 'Poor':0.5 }

class Synth( object ):
    def __init__( self, durability, progress, quality, craftsmanship, control, rlvlDiff, cpMax ):
        # synth state and progress
        self._durability    = durability
        self.durabilityDelta = 0
        self.durabilityMax  = durability
        self.durabilityLost = 0             # delta of cur and max, not total over entire course of the synth
        self.progress       = 0
        self.progressMax    = progress
        self.progressDelta  = 0 #TODO
        self._quality       = 0
        self.qualityDelta   = 0
        self.qualityMax     = quality

        self.step               = 0
        self.condition          = 'Normal'
        self.lastAction         = 'None'
        self.lastActionStatus   = ''
        self.completionState    = 'in progress'

        # crafter stats
        self.cp             = cpMax
        self.cpMax          = cpMax
        self.cpDelta        = 0 #TODO
        self.craftsmanship  = craftsmanship
        self.control        = control
        self.control_base   = control
        self.rlvlDiff       = rlvlDiff

        # buffs and on-going effects
        self.innerQuiet         = False
        self.innerQuietStacks   = 0
        self.manipulationTTL    = 0
        self.manipulationUsed   = False
        self.greatStridesTTL    = 0


        self.recalcStats()

    @property
    def quality( self ): return self._quality
    @quality.setter
    def quality( self, val ):
        self.qualityDelta = val - self._quality
        if self.innerQuiet and self.qualityDelta > 0:
            self.innerQuietStacks += 1

        self._quality = val

    @property
    def durability( self ): return self._durability
    @durability.setter
    def durability( self, val ):
        self.durabilityDelta = val - self._durability
        if self.manipulationTTL > 0 and self.durabilityDelta < 0:
            self._durability += 10
        self._durability = val

    def recalcStats( self ):
        def calcQuality( rlvlDiff, control ): return (1-0.05* rlvlDiff) * (0.36 * control + 34)
        def calcProgress( rlvlDiff, craftsmanship ): return (1-0.05* rlvlDiff) * (0.21 * craftsmanship + 1.6)

        self.control        = self.control_base + self.control_base * 0.20 * self.innerQuietStacks

        self.stdProgress    = calcProgress( self.rlvlDiff, self.craftsmanship )
        self.stdQuality     = calcQuality( self.rlvlDiff, self.control )

        self.durabilityLost = self.durabilityMax - self.durability

        self.updateCompletionState()

    def __str__( self ):
        s = '#%d Last: %s (%s)\nCond: %s Comp: %s\nP %d / %d (%s)\nD %d / %d (%s)\nQ %d / %d (%s)\nCP %d / %d (%s)\n' % (
            self.step, self.lastAction, self.lastActionStatus,
            self.condition, self.completionState,
            self.progress, self.progressMax, self.progressDelta,
            self.durability, self.durabilityMax, self.durabilityDelta,
            self.quality, self.qualityMax, self.qualityDelta,
            self.cp, self.cpMax, self.cpDelta,
            )
        #TODO add any buffs / on-going effects info to __str__
        return s

    def updateCondition( self ):
        if self.condition == 'Excellent':   self.condition = 'Poor'
        elif self.condition == 'Good':      self.condition = 'Normal'
        elif self.condition == 'Poor':      self.condition = 'Normal'
        else:
            if 0.05 > random():             self.condition = 'Excellent'
            elif 0.25 > random():           self.condition = 'Good'

    def updateCompletionState( self ):
        if self.progress >= self.progressMax:   self.completionState = 'SUCCESS'
        elif self.durability <= 0:              self.completionState = 'FAILURE'
        else:                                   self.completionState = 'in progress'

    def applySkill( self, skill ):
        '''Returns false if skill was not applied'''
        # pre
        if self.completionState != 'in progress': return False
        if not skill.canDo( self ):
            raise RuntimeError, "Can't perform skill %s" % skill
            return False

        # payload
        r = skill.apply( self ) # generally returns 'Success' | 'Failure'

        # post
        self.lastAction = skill.__class__.__name__
        self.lastActionStatus = r
        self.updateCondition() #TODO: handle skills that don't count as a step for the purposes of progressing condition
        self.step += 1
        if self.manipulationTTL > 0: self.manipulationTTL -= 1 # ticks away even for non-durability loss actions
        if self.greatStridesTTL > 0: self.greatStridesTTL -= 1
        self.recalcStats()
        return True

    def score( self ):
        if self.completionState != 'SUCCESS': return 0
        score = 1   # for completion
        score += 3. * self.quality / self.qualityMax    # for quality
        return score

    def maxStepsLeft( self, usingMastersMend=True, cp=None ):
        '''Will do calculations on provided cp if provided, otherwise uses current'''
        if cp is None: cp = self.cp

        nsteps = self.durability / 10
        if usingMastersMend:
            nsteps += 3 * (cp / 92)
        return nsteps

    def minProgStepsLeft( self, synthSkill ):
        progLeft = self.progressMax - self.progress
        progPerStep = self.stdProgress * synthSkill.efficiency
        return int( ceil( progLeft / progPerStep ) )

    def stillPossibleToFinish( self, minusSteps, minusCp, synthSkill ):
        '''Return whether it's possible to finish despite losing the provided number of turns and cp'''
        nsteps = self.maxStepsLeft( cp = self.cp - minusCp )
        nprog = self.minProgStepsLeft( synthSkill )
        return nsteps - minusSteps >= nprog

################################################################################
## Skills
################################################################################

class Singleton( type ):
    _instances = {}
    def __call__( cls, *args, **kwargs ):
        if cls not in cls._instances:
            cls._instances[ cls ] = super( Singleton, cls ).__call__( *args, **kwargs )
        return cls._instances[ cls ]

class Skill( object ):
    __metaclass__ = Singleton
    def canDo( self, synth ):
        if synth.cp < self.cpCost: return False
        return True

class Synthesis( Skill ):
    def apply( self, synth ):
        synth.cp -= self.cpCost
        synth.durability -= self.durCost
        if self.chance >= random():
            synth.progress += synth.stdProgress * self.efficiency
            return 'Success'
        else:
            return 'Failed'

class Touch( Skill ):
    def apply( self, synth, efficiency=None ):
        if efficiency is None: efficiency = self.efficiency
        synth.cp -= self.cpCost
        synth.durability -= self.durCost
        q = synth.stdQuality * efficiency * SynthConditionMult[ synth.condition ]
        if synth.greatStridesTTL > 0:
            q *= 2
            synth.greatStridesTTL = 0
        if self.chance >= random():
            synth.quality += q
            return 'Success'
        else:
            return 'Failed'

class ByregotsBlessing( Touch ):
    def __init__( self ):
        self.cpCost = 24
        self.durCost = 10
        self.chance = 0.90

    def canDo( self, synth ):
        if synth.cp < self.cpCost: return False
        if not synth.innerQuiet: return False
        return True

    def apply( self, synth ):
        efficiency = 1.00 + 0.20 * synth.innerQuietStacks
        r = Touch.apply( self, synth, efficiency )
        InnerQuiet().remove( synth )
        return r

class Mend( Skill ):
    def apply( self, synth ):
        synth.cp -= self.cpCost
        synth.durability += self.durGain
        return 'Success'

class TricksOfTheTrade( Skill ):
    def canDo( self, synth ):
        if synth.condition != 'Good': return False
        return True

    def apply( self, synth ):
        synth.cp += 20
        #synth.durability -= 10 #TODO check if TotT costs durability

class GreatStrides( Skill ):
    def __init__( self ):
        self.cpCost = 32
        self.durCost = 10

    def apply( self, synth ):
        synth.cp -= self.cpCost
        synth.durability -= self.durCost
        synth.greatStridesTTL = 3

class InnerQuiet( Skill ):
    def __init__( self ):
        self.cpCost = 22

    def apply( self, synth ):
        synth.innerQuiet = True

    def remove( self, synth ):
        synth.innerQuiet = False
        synth.innerQuietStacks = 0

class Rumination( Skill ):
    def canDo( self, synth ):
        if not synth.innerQuiet: return False
        return True

    def amtRestorable( self, synth ):
        iqStacks = min( 10, synth.innerQuietStacks )
        return sum( [15,9,8,7,6,5,4,3,2,1][:iqStacks] )

    def apply( self, synth ):
        synth.cp += self.amtRestorable( synth )
        InnerQuiet().remove( synth )

class Manipulation( Skill ):
    def __init__( self ):
        self.cpCost = 88

    def canDo( self, synth ):
        if synth.durability <= 10: return False # some say you cant apply it at <=10 dur
        if synth.cp < self.cpCost: return False
        if synth.manipulationUsed: return False
        return True

    def apply( self, synth ):
        synth.manipulationTTL = 3
        synth.manipulationUsed = True

class BasicSynthesis( Synthesis ):
    def __init__( self ):
        self.chance = 0.90
        self.efficiency = 1.00
        self.cpCost = 0
        self.durCost = 10

class CarefulSynthesis( Synthesis ):
    def __init__( self ):
        self.chance = 1.00
        self.efficiency = 0.90
        self.cpCost = 0
        self.durCost = 10

class BasicTouch( Touch ):
    def __init__( self ):
        self.chance = 0.70
        self.efficiency = 1.00
        self.cpCost = 18
        self.durCost = 10

class StandardTouch( Touch ):
    def __init__( self ):
        self.chance = 0.80
        self.efficiency = 1.25
        self.cpCost = 32
        self.durCost = 10

class HastyTouch( Touch ):
    def __init__( self ):
        self.chance = 0.50
        self.efficiency = 1.00
        self.cpCost = 0
        self.durCost = 10

class MastersMend( Mend ):
    def __init__( self ):
        self.cpCost = 92
        self.durGain = 30

class MastersMend2( Mend ):
    def __init__( self ):
        self.cpCost = 160
        self.durGain = 60


################################################################################
## Synth and sim creation
################################################################################

synthDb = {
    'Brass Ingot' : { 'durability':40, 'progress':27, 'quality':300 },
    'Brass Choker' : { 'durability':70, 'progress':75, 'quality':1090 },
}

def mkSynth( id, craftsmanship, control, rlvlDiff, cpMax ):
    item = synthDb[ id ]
    return Synth( item['durability'], item['progress'], item['quality'], craftsmanship, control, rlvlDiff, cpMax )

def runSimOnce( synth, strat, debug=False ):
    i = 0
    if debug: print synth
    while synth.completionState == 'in progress' and i < 1000:
        i += 1
        skill = strat( synth )
        synth.applySkill( skill() )
        if debug: print synth
    if i >= 1000: raise RuntimeError( 'Infinite loop detected' )

def runSim( synth, strat, debug=False, runs=1000 ):
    totalScore = 0.0
    for _ in xrange( runs ):
        s = copy.copy( synth )
        runSimOnce( s, strat, debug )
        totalScore += s.score()
    return totalScore / runs

################################################################################
## Test
################################################################################

def test():
    s = mkSynth( 241, 100, 100, 0, 230 ) # rough guess @ lv14
    '''
    print '## No touch'
    print runSim( s, noTouch )

    print '## Dangerous - CarefulSynthesis'
    print runSim( s, dangerous_carefulSynth )

    print '## Dangerous - BasicSynthesis'
    print runSim( s, dangerous_basicSynth )

    print '## Smarter'
    print runSim( s, smarter, runs=1000 )
    '''

    t = copy.copy( s )
    runSimOnce( t, smarter, debug=False )
    print t.score()

    print runSim( s, smarter, runs=1000 )

    # test
    #runSimOnce( s, dangerous )
    #print s.score()
