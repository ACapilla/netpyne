
"""
network.py 

Contains cell and population classes 

Version: 2015may26 by salvadordura@gmail.com
"""

###############################################################################
### IMPORT MODULES
###############################################################################

from neuron import h, init # Import NEURON
from pylab import seed, rand, sqrt, exp, transpose, ceil, concatenate, array, zeros, ones, vstack, show, disp, mean, inf, concatenate
from time import time, sleep
import pickle
import warnings

import params as p  # Import all shared variables and parameters
import shared as s

warnings.filterwarnings('error')


###############################################################################
### Instantiate network populations (objects of class 'Pop')
###############################################################################
def createPops():
    if p.popType == 'Basic': popClass = s.BasicPop
    elif p.popType == 'Yfrac': popClass = s.YfracPop
    s.pops = []  # list to store populations ('Pop' objects)
    for popParam in p.popParams: # for each set of population parameters 
        s.pops.append(popClass(*popParam))  # instantiate a new object of class Pop and add to list pop


###############################################################################
### Create Cells
###############################################################################
def createCells():
    s.pc.barrier()
    if s.rank==0: print("\nCreating simulation of %i cell populations for %0.1f s on %i hosts..." % (len(s.pops),p.duration/1000.,s.nhosts)) 
    s.gidVec=[] # Empty list for storing GIDs (index = local id; value = gid)
    s.gidDic = {} # Empty dict for storing GIDs (key = gid; value = local id) -- ~x6 faster than gidVec.index()  
    s.cells = []
    for ipop in s.pops: # For each pop instantiate the network cells (objects of class 'Cell')
        newCells = ipop.createCells() # create cells for this pop using Pop method
        s.cells.extend(newCells)  # add to list of cells
        s.pc.barrier()
        if s.rank==0 and p.verbose: print('Instantiated %d cells of population %d'%(ipop.numCells, ipop.popgid))           
    s.simdata.update({name:h.Vector(1e4).resize(0) for name in ['spkt','spkid']})
    print('  Number of cells on node %i: %i ' % (s.rank,len(s.cells)))            
    

###############################################################################
### Connect Cells
###############################################################################
def connectCells():
    # Instantiate network connections (objects of class 'Conn') - connects object cells based on pre and post cell's type, class and yfrac
    if s.rank==0: print('Making connections...'); connstart = time()

    if p.connType == 'random':  # if random connectivity
        connClass = s.RandConn  # select ConnRand class
        arg = p.ncell  # pass as argument num of presyn cell
    
    elif p.connType == 'yfrac':  # if yfrac-based connectivity
        connClass = s.YfracConn  # select ConnYfrac class
        data = [s.cells]*s.nhosts  # send cells data to other nodes
        gather = s.pc.py_alltoall(data)  # collect cells data from other nodes (required to generate connections)
        s.pc.barrier()
        allCells = []
        for x in gather:    allCells.extend(x)  # concatenate cells data from all nodes
        del gather, data  # removed unnecesary variables
        allCellsGids = [x.gid for x in allCells] # order gids
        allCells = [x for (y,x) in sorted(zip(allCellsGids,allCells))]
        arg = allCells  # pass as argument the list of presyn cell objects

    s.conns = []  # list to store connections   
    for ipost in s.cells: # for each postsynaptic cell in this node
        newConns = connClass.connect(arg, ipost)  # calculate all connections
        if newConns: s.conns.extend(newConns)  # add to list of connections in this node
    
    print('  Number of connections on host %i: %i ' % (s.rank, len(s.conns)))
    s.pc.barrier()
    if s.rank==0: conntime = time()-connstart; print('  Done; time = %0.1f s' % conntime) # See how long it took


###############################################################################
### Add background inputs
###############################################################################
def addBackground():
    if s.rank==0: print('Creating background inputs...')
    for c in s.cells: 
        c.addBackground()
    print('  Number created on host %i: %i' % (s.rank, len(s.cells)))
    s.pc.barrier()


###############################################################################
### Add stimulation
###############################################################################
def addStimulation():
    if p.usestims:
        s.stimuli.setStimParams()
        s.stimstruct = [] # For saving
        s.stimrands=[] # Create input connections
        s.stimsources=[] # Create empty list for storing synapses
        s.stimconns=[] # Create input connections
        s.stimtimevecs = [] # Create array for storing time vectors
        s.stimweightvecs = [] # Create array for holding weight vectors
        if p.saveraw: 
            s.stimspikevecs=[] # A list for storing actual cell voltages (WARNING, slow!)
            s.stimrecorders=[] # And for recording spikes
        for stim in range(len(s.stimuli.stimpars)): # Loop over each stimulus type
            ts = s.stimuli.stimpars[stim] # Stands for "this stimulus"
            ts.loc = ts.loc * s.modelsize # scale cell locations to model size
            stimvecs = s.stimuli.makestim(ts.isi, ts.var, ts.width, ts.weight, ts.sta, ts.fin, ts.shape) # Time-probability vectors
            s.stimstruct.append([ts.name, stimvecs]) # Store for saving later
            s.stimtimevecs.append(h.Vector().from_python(stimvecs[0]))
            for c in s.cells:
                gid = c.gid #s.cellsperhost*int(s.rank)+c # For deciding E or I    
                seed(s.id32('%d'%(s.randseed+gid))) # Reset random number generator for this cell
                if ts.fraction>rand(): # Don't do it for every cell necessarily
                    if any(s.cellpops[gid]==ts.pops) and s.xlocs[gid]>=ts.loc[0,0] and s.xlocs[gid]<=ts.loc[0,1] and s.ylocs[gid]>=ts.loc[1,0] and s.ylocs[gid]<=ts.loc[1,1]:
                        maxweightincrease = 20 # Otherwise could get infinitely high, infinitely close to the stimulus
                        distancefromstimulus = sqrt(sum((array([s.xlocs[gid], s.ylocs[gid]])-s.modelsize*ts.falloff[0])**2))
                        fallofffactor = min(maxweightincrease,(ts.falloff[1]/distancefromstimulus)**2)
                        s.stimweightvecs.append(h.Vector().from_python(stimvecs[1]*fallofffactor)) # Scale by the fall-off factor
                        stimrand = h.Random()
                        stimrand.MCellRan4() # If everything has the same seed, should happen at the same time
                        stimrand.negexp(1)
                        stimrand.seq(s.id32('%d'%(s.randseed+gid))*1e3) # Set the sequence i.e. seed
                        s.stimrands.append(stimrand)
                        stimsource = h.NetStim() # Create a NetStim
                        stimsource.interval = ts.rate**-1*1e3 # Interval between spikes
                        stimsource.number = 1e9 # Number of spikes
                        stimsource.noise = ts.noise # Fractional noise in timing
                        stimsource.noiseFromRandom(stimrand) # Set it to use this random number generator
                        s.stimsources.append(stimsource) # Save this NetStim
                        stimconn = h.NetCon(stimsource, s.cells[c]) # Connect this noisy input to a cell
                        for r in range(s.nreceptors): stimconn.weight[r]=0 # Initialize weights to 0, otherwise get memory leaks
                        s.stimweightvecs[-1].play(stimconn._ref_weight[0], s.stimtimevecs[-1]) # Play most-recently-added vectors into weight
                        stimconn.delay=s.mindelay # Specify the delay in ms -- shouldn't make a spot of difference
                        s.stimconns.append(stimconn) # Save this connnection
                        if s.saveraw:# and c <=100:
                            stimspikevec = h.Vector() # Initialize vector
                            s.stimspikevecs.append(stimspikevec) # Keep all those vectors
                            stimrecorder = h.NetCon(stimsource, None)
                            stimrecorder.record(stimspikevec) # Record simulation time
                            s.stimrecorders.append(stimrecorder)
        print('  Number of stimuli created on host %i: %i' % (s.rank, len(s.stimsources)))









