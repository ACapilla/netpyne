from netpyne import specs, sim

# Network parameters
netParams = specs.NetParams()  # object of class NetParams to store the network parameters

## Population parameters
netParams.addPopParams('S', {'cellType': 'PYR', 'numCells': 20, 'cellModel': 'HH'}) 
netParams.addPopParams('M', {'cellType': 'PYR', 'numCells': 20, 'cellModel': 'HH'}) 
netParams.addPopParams('background', {'rate': 10, 'noise': 0.5, 'cellModel': 'NetStim'})

## Cell property rules
cellRule = {'conds': {'cellType': 'PYR'},  'secs': {}}  # cell rule dict
cellRule['secs']['soma'] = {'geom': {}, 'mechs': {}}                                                        # soma params dict
cellRule['secs']['soma']['geom'] = {'diam': 18.8, 'L': 18.8, 'Ra': 123.0}                                   # soma geometry
cellRule['secs']['soma']['mechs']['hh'] = {'gnabar': 0.12, 'gkbar': 0.036, 'gl': 0.003, 'el': -70}          # soma hh mechanism
netParams.addCellParams('PYRrule', cellRule)                                                # add dict to list of cell params

## Synaptic mechanism parameters
netParams.addSynMechParams('exc', {'mod': 'Exp2Syn', 'tau1': 0.1, 'tau2': 5.0, 'e': 0})  # excitatory synaptic mechanism
 
## Stimulation parameters
netParams.addStimSourceParams('Input_1', {'type': 'IClamp', 'delay': 200, 'dur': 400, 'amp': 'uniform(0.05,0.5)'})
netParams.addStimSourceParams('Input_2', {'type': 'VClamp', 'dur': [0,1,200], 'amp': [1,1,1], 'gain': 1, 'rstim': 0, 'tau1': 1, 'tau2': 1, 'i': 1})
netParams.addStimSourceParams('Input_3', {'type': 'AlphaSynapse', 'onset': 'uniform(600,800)', 'tau': 5, 'gmax': 'post_ynorm', 'e': 0})
netParams.addStimSourceParams('Input_4', {'type': 'NetStim', 'interval': 'uniform(20,100)', 'number': 1000, 'start': 800, 'noise': 0.1})

netParams.addStimTargetParams('Input_1->S', 
    {'source': 'Input_1', 
    'sec':'soma', 
    'loc': 0.8, 
    'conds': {'popLabel':'S', 'cellList': range(15)}})

netParams.addStimTargetParams('Input_2->S', 
    {'source': 'Input_2', 
    'sec':'soma', 
    'loc': 0.5, 
    'conds': {'popLabel':'S', 'ynorm': [0,0.5]}})

netParams.addStimTargetParams('Input_2->M1', 
    {'source': 'Input_3', 
    'sec':'soma', 
    'loc': 0.2, 
    'conds': {'popLabel':'M', 'cellList': [2,4,5,8,10,15,19]}})

netParams.addStimTargetParams('Input_4->PYR', 
  {'source': 'Input_4', 
  'sec':'soma', 
  'loc': 0.5, 
  'weight': '0.1+gauss(0.2,0.05)',
  'delay': 1,
  'conds': {'cellType':'PYR', 'ynorm': [0.6,1.0]}})


# Simulation options
simConfig = specs.SimConfig()       # object of class SimConfig to store simulation configuration

simConfig.duration = 1*1e3          # Duration of the simulation, in ms
simConfig.dt = 0.025                # Internal integration timestep to use
simConfig.verbose = False           # Show detailed messages 
simConfig.recordTraces = {'V_soma':{'sec':'soma','loc':0.5,'var':'v'}}  # Dict with traces to record
simConfig.recordStep = 0.1          # Step size in ms to save data (eg. V traces, LFP, etc)
simConfig.filename = 'model_output'  # Set file output name
simConfig.savePickle = False        # Save params, network and sim output to pickle file

simConfig.addAnalysis('plotRaster', True)           # Plot a raster
simConfig.addAnalysis('plotTraces', {'include': [1]})           # Plot recorded traces for this list of cells
simConfig.addAnalysis('plot2Dnet', True)           # plot 2D visualization of cell positions and connections


# Create network and run simulation
sim.createSimulateAnalyze(netParams = netParams, simConfig = simConfig)    
   
# import pylab; pylab.show()  # this line is only necessary in certain systems where figures appear empty
