from netpyne import specs

###############################################################################
# NETWORK PARAMETERS
###############################################################################

netParams = specs.NetParams()  # object of class NetParams to store the network parameters

netParams.sizeX = 50 # x-dimension (horizontal length) size in um
netParams.sizeY = 1200 # y-dimension (vertical height or cortical depth) size in um
netParams.sizeZ = 50 # z-dimension (horizontal length) size in um
netParams.propVelocity = 100.0 # propagation velocity (um/ms)
netParams.probLengthConst = 150.0 # length constant for conn probability (um)

## Population parameters
netParams.addPopParams('L2_E',  {'cellType': 'E2', 'density': 50, 'ynormRange': [0.2,0.4], 'cellModel': 'perisom'}) 
netParams.addPopParams('L2_IF', {'cellType': 'IF', 'density': 50, 'ynormRange': [0.2,0.4], 'cellModel': 'perisom'}) 
netParams.addPopParams('L2_IL', {'cellType': 'IL', 'density': 50, 'ynormRange': [0.2,0.4], 'cellModel': 'perisom'}) 
netParams.addPopParams('L4_E',  {'cellType': 'E4', 'density': 50, 'ynormRange': [0.4,0.6], 'cellModel': 'perisom'}) 
netParams.addPopParams('L4_IF', {'cellType': 'IF', 'density': 50, 'ynormRange': [0.4,0.6], 'cellModel': 'perisom'}) 
netParams.addPopParams('L4_IL', {'cellType': 'IL', 'density': 50, 'ynormRange': [0.4,0.6], 'cellModel': 'perisom'}) 
netParams.addPopParams('L5_E',  {'cellType': 'E5', 'density': 50, 'ynormRange': [0.6,0.8], 'cellModel': 'perisom'}) 
netParams.addPopParams('L5_IF', {'cellType': 'IF', 'density': 50, 'ynormRange': [0.6,0.8], 'cellModel': 'perisom'}) 
netParams.addPopParams('L5_IL', {'cellType': 'IL', 'density': 50, 'ynormRange': [0.6,0.8], 'cellModel': 'perisom'}) 

#netParams.popParams['L2_E'] = {'cellType': 'E2', 'density': 50, 'ynormRange': [0.2,0.4], 'cellModel': 'perisom'}

## Cell property rules
netParams.importCellParams(label='E2_perisom', conds={'cellType': 'E2', 'cellModel': 'perisom'}, fileName='getCells.py', cellName='E2')
netParams.importCellParams(label='E4_perisom', conds={'cellType': 'E4', 'cellModel': 'perisom'}, fileName='getCells.py', cellName='E4')
netParams.importCellParams(label='E5_perisom', conds={'cellType': 'E5', 'cellModel': 'perisom'}, fileName='getCells.py', cellName='E5')
netParams.importCellParams(label='IF_perisom', conds={'cellType': 'IF', 'cellModel': 'perisom'}, fileName='getCells.py', cellName='IF')
netParams.importCellParams(label='IL_perisom', conds={'cellType': 'IL', 'cellModel': 'perisom'}, fileName='getCells.py', cellName='IL')

#netParams.addCellParams()

## Synaptic mechanism parameters
netParams.addSynMechParams('AMPA', {'mod': 'Exp2Syn', 'tau1': 0.05, 'tau2': 5.3, 'e': 0})  # excitatory synaptic mechanism
netParams.addSynMechParams('GABA', {'mod': 'Exp2Syn', 'tau1': 0.07, 'tau2': 18.2, 'e': -80})  # inhibitory synaptic mechanism
 
## Cell connectivity rules
# netParams.addConnParams('bg->all',
# {'preConds': {'popLabel': 'background'}, 'postConds': {'cellType': ['E', 'I']}, # background -> all
#   'weight': 0.01,                     # synaptic weight 
#   'delay': 'max(1, gauss(5,2))',      # transmission delay (ms) 
#   'synMech': 'exc'})                  # synaptic mechanism 

# netParams.addConnParams('E->all',
# {'preConds': {'cellType': 'E'}, 'postConds': {'y': [100,1000]},  #  E -> all (100-1000 um)
#   'probability': 0.1 ,                  # probability of connection
#   'weight': '0.005*post_ynorm',         # synaptic weight 
#   'delay': 'dist_3D/propVelocity',      # transmission delay (ms) 
#   'synMech': 'exc'})                    # synaptic mechanism 

# netParams.addConnParams('I->E',
# {'preConds': {'cellType': 'I'}, 'postConds': {'popLabel': ['E2','E4','E5']},       #  I -> E
#   'probability': '0.4*exp(-dist_3D/probLengthConst)',   # probability of connection
#   'weight': 0.001,                                     # synaptic weight 
#   'delay': 'dist_3D/propVelocity',                    # transmission delay (ms) 
#   'synMech': 'inh'})                                  # synaptic mechanism 


###############################################################################
# SIMULATION CONFIGURATION
###############################################################################

simConfig = specs.SimConfig()        # object of class SimConfig to store simulation configuration
simConfig.duration = 1*1e3           # Duration of the simulation, in ms
simConfig.dt = 0.05                 # Internal integration timestep to use
simConfig.verbose = False            # Show detailed messages 
simConfig.recordTraces = {'V_soma':{'sec':'soma','loc':0.5,'var':'v'}}  # Dict with traces to record
simConfig.recordStep = 1             # Step size in ms to save data (eg. V traces, LFP, etc)
simConfig.filename = 'model_output'  # Set file output name
simConfig.savePickle = True        # Save params, network and sim output to pickle file
simConfig.timestampFilename = True

# simConfig.addAnalysis('plotRaster', {'orderBy': 'y', 'orderInverse': True, 'saveFig': True})      # Plot a raster
# simConfig.addAnalysis('plotTraces', {'include': [('E2',0), ('E4', 0), ('E5', 5)]})      # Plot recorded traces for this list of cells
# simConfig.addAnalysis('plot2Dnet', True)           # plot 2D visualization of cell positions and connections
# simConfig.addAnalysis('plotConn', True)           # plot connectivity matrix

# Create network and run simulation
#sim.createSimulateAnalyze(netParams = netParams, simConfig = simConfig)    
   
# import pylab; pylab.show()  # this line is only necessary in certain systems where figures appear empty
