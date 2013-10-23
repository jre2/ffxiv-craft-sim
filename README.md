ffxiv-craft-sim
===============

A crafting simulator for ffxiv.

You can write an AI by creating a function in strat.py which determines what action to perform based on the current state of the synthesis.

You can then simulate using that AI against thousands of synths in order to determine an average score, which is currently based on whether it succeeded and what the final quality was, but can be easily changed in sim.Synth.score (eg. factor in # of steps to optimize xp/hr).

Not all actions are implemented, but the majority are and many are easily added to sim.py.


Usage
=====
Create a strategy function in strat.py then invoke main.py, specifying strategy name and number of runs.

For example:

`python main.py static1 100`


To get a step by step breakdown for debugging purposes, you can specify the debug flag at the end. Ex:

`python main.py static1 1 True`
