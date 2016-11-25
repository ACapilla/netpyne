"""
sandbox.py 

netParams is a class containing a set of network parameters using a standardized structure

simConfig is a class containing a set of simulation configurations using a standardized structure

Contributors: salvadordura@gmail.com
"""

###############################################################################
#
# SANDBOX PARAMS
#
###############################################################################

import netpyne
netpyne.__gui__ = True

from netpyne import specs, sim
from netpyne.specs import Dict

netParams = specs.NetParams()  # object of class NetParams to store the network parameters
simConfig = specs.SimConfig()  # dictionary to store sets of simulation configurations


###############################################################################
# NETWORK PARAMETERS
###############################################################################

netParams.scaleConnWeightModels = {'HH': 1.0}

# Population parameters
netParams.addPopParams('PYR1', {'cellModel': 'HH', 'cellType': 'PYR', 'numCells': 1}) # add dict with params for this pop 
netParams.addPopParams('PYR2', {'cellModel': 'HH', 'cellType': 'PYR', 'numCells': 1}) # add dict with params for this pop 
netParams.addPopParams('background', {'cellModel': 'NetStim', 'rate': 20, 'noise': 0.5, 'start': 1, 'seed': 2})  # background inputs

# Synaptic mechanism parameters
netParams.addSynMechParams('AMPA', {'mod': 'Exp2Syn', 'tau1': 0.1, 'tau2': 1.0, 'e': 0})
netParams.addSynMechParams('esyn', {'mod': 'ElectSyn', 'g': 0.000049999999999999996})


# Cell parameters
## PYR cell properties
cellParams = Dict()
cellParams.secs.soma.geom = {'diam': 18.8, 'L': 18.8, 'Ra': 123.0}
cellParams.secs.soma.mechs.hh = {'gnabar': 0.12, 'gkbar': 0.036, 'gl': 0.003, 'el': -70}
cellParams.conds = {'cellType': 'PYR'}
netParams.addCellParams('PYR', cellParams)

netParams.connParams['bg->PYR1'] = {
    'preConds': {'popLabel': 'background'}, 'postConds': {'popLabel': 'PYR1'}, # background -> PYR
    'weight': 0.1,                    # fixed weight of 0.08
    'synMech': 'AMPA',                     # target NMDA synapse
    'delay': 'uniform(1,5)'}           # uniformly distributed delays between 1-5ms

netParams.addConnParams('PYR1->PYR2',
    {'preConds': {'popLabel': 'PYR1'}, 'postConds': {'popLabel': 'PYR2'}, # PYR1 -> PYR2
    'weight': 200.0,                    # fixed weight of 0.08
    'synMech': 'esyn',                     # target NMDA synapse
    'gapJunction': True,
    'sec': 'soma',
    'loc': 0.5,
    'preSec': 'soma',
    'preLoc': 0.5})        


# if (isCellOnNode("SampleCellGroup", 1)) {
#     a_SampleCellGroup[1].Soma { elecsyn_NetConn_SampleCellGroup_SampleCellGroup_ElectSyn_A[0] = new ElectSyn(0.5) }
#     elecsyn_NetConn_SampleCellGroup_SampleCellGroup_ElectSyn_A[0].weight = 1.0
#     pnm.pc.target_var(&elecsyn_NetConn_SampleCellGroup_SampleCellGroup_ElectSyn_A[0].vgap, 100000000)
#     pnm.pc.source_var(&a_SampleCellGroup[1].Soma.v(0.5), 200000000)
# }
# if (isCellOnNode("SampleCellGroup", 0)) {
#     a_SampleCellGroup[0].Soma { elecsyn_NetConn_SampleCellGroup_SampleCellGroup_ElectSyn_B[0] = new ElectSyn(0.5) }
#     elecsyn_NetConn_SampleCellGroup_SampleCellGroup_ElectSyn_B[0].weight = 1.0
#     pnm.pc.target_var(&elecsyn_NetConn_SampleCellGroup_SampleCellGroup_ElectSyn_B[0].vgap, 200000000)
#     pnm.pc.source_var(&a_SampleCellGroup[0].Soma.v(0.5), 100000000)
# }


###############################################################################
# SIMULATION PARAMETERS
###############################################################################

# Simulation parameters
simConfig.duration = 1*1e3 # Duration of the simulation, in ms
simConfig.dt = 0.1 # Internal integration timestep to use
simConfig.seeds = {'conn': 2, 'stim': 2, 'loc': 2} # Seeds for randomizers (connectivity, input stimulation and cell locations)
simConfig.createNEURONObj = 1  # create HOC objects when instantiating network
simConfig.createPyStruct = 1  # create Python structure (simulator-independent) when instantiating network
simConfig.verbose = 1 #False  # show detailed messages 

# Recording 
simConfig.recordCells = []# [1,2]  # which cells to record from
simConfig.recordTraces = {'Vsoma':{'sec':'soma','loc':0.5,'var':'v'}}
#'AMPA_i': {'synMech':'homSyn', 'var':'i'}}
#'AMPA_i': {'synMech':'homSyn', 'sec': 'dend', 'loc': 0.775, 'var':'i'}}

simConfig.recordStim = True  # record spikes of cell stims
simConfig.recordStep = 0.1 # Step size in ms to save data (eg. V traces, LFP, etc)

# Saving
simConfig.filename = 'mpiHHTut'  # Set file output name
simConfig.saveFileStep = 1000 # step size in ms to save data to disk
simConfig.savePickle = 0 # Whether or not to write spikes etc. to a .mat file
simConfig.saveJson = 0 # Whether or not to write spikes etc. to a .mat file
simConfig.saveMat = 0 # Whether or not to write spikes etc. to a .mat file
simConfig.saveDpk = 0 # save to a .dpk pickled file
simConfig.saveHDF5 = 0
simConfig.saveCSV = 0

# # Analysis and plotting 
simConfig.addAnalysis('plotRaster', {'spikeHist': 'subplot'})
simConfig.addAnalysis('plotTraces', {'include': [0,1]})


###############################################################################
# RUN SIM
###############################################################################


sim.initialize(netParams = netParams, simConfig = simConfig)
sim.net.createPops()
sim.net.createCells()
sim.net.connectCells()
sim.net.addStims()
sim.setupRecording()

sim.simulate()

sim.analyze()


