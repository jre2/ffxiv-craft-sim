#!/usr/bin/python

import sys
import sim
import strats

def main():
    synth = sim.mkSynth( 'Brass Choker', 111, 90, 0, 255 ) # change this

    if len( sys.argv ) < 3:
        print 'Usage: python main.py strategyName numRuns [boolDebug]'
        print '    if you want to change the item or player stats, modify this file'
        return

    stratName = sys.argv[1]
    runs = int( sys.argv[2] )
    debug = len( sys.argv ) > 3 and sys.argv[3] == 'True'
    print 'Running strategy %s over %d runs%s' % ( stratName, runs, ' with debug' if debug else '' )

    if not hasattr( strats, stratName ):
        print 'Strategy does not exist'
        return

    strat = getattr( strats, stratName )
    score = sim.runSim( synth, strat, runs=runs, debug=debug )
    print 'Score:', score

main()
