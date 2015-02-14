"""
MODEL

A large-scale network simulation for exploring traveling waves, stimuli,
and STDs. Built solely in Python, using Izhikevich neurons and with MPI
support. Runs in real-time with over 8000 cells when appropriately
parallelized.
M1 model extended to interface with Plexon-recorded PMd data, virtual arm,
and reinforcement learning

Usage:
    python model.py # Run simulation, optionally plot a raster
    python simmovie.py # Show a movie of the results
    python model.py scale=20 # Run simulation, set scale=20

MPI usage:
    mpiexec -n 4 nrniv -python -mpi model.py

Version: 2014feb21 by cliffk
2014sep19 modified by salvadord and giljael
"""


###############################################################################
### IMPORT MODULES
###############################################################################

from neuron import h, init # Import NEURON
from pylab import seed, rand, sqrt, exp, transpose, concatenate, array, zeros, ones, vstack, show, disp
from time import time, datetime
import shared as s # Import all shared variables and parameters
import analysis

def id32(obj): return hash(obj) & 0xffffffff # bitwise AND to retain only lower 32 bits, for consistency with 32-bit processors


###############################################################################
### CREATE MODEL
###############################################################################
def runSeq():
    createNetwork() 
    addStimulation()
    addBackground()
    setupSim()
    runSim()
    finalizeSim()
    saveData()
    plotData()


###############################################################################
### Create Network
###############################################################################

def createNetwork():
    ## Set cell types
    celltypes=[]
    for c in range(s.ncells): # Loop over each cell. ncells is all cells in the network.
        if s.cellclasses[c]==1: celltypes.append(s.pyramidal) # Append a pyramidal cell
        elif s.cellclasses[c]==2: celltypes.append(s.fastspiking) # Append a fast-spiking interneuron
        elif s.cellclasses[c]==3: celltypes.append(s.lowthreshold) # Append a low-threshold-spiking interneuron
        elif s.cellclasses[c]==4: celltypes.append(s.thalamocortical) # Append a thalamocortical cell
        elif s.cellclasses[c]==5: celltypes.append(s.reticular) # Append a thalamocortical cell
        elif s.cellclasses[c]==-1: celltypes.append(s.nsloc) # Append a nsloc
        else: raise Exception('Undefined cell class "%s"' % s.cellclasses[c]) # No match? Cause an error


    ## Set positions
    seed(id32('%d'%s.randseed)) # Reset random number generator
    xlocs = s.modelsize*rand(s.ncells) # Create random x locations
    ylocs = s.modelsize*rand(s.ncells) # Create random y locations
    zlocs = rand(s.ncells) # Create random z locations
    for c in range(s.ncells): 
        zlocs[c] = s.corticalthick * (zlocs[c]*(s.popyfrac[s.cellclasses[c]][1]-s.popyfrac[s.cellclasses[c]][0])) # calculate based on yfrac for population and corticalthick 


    ## Actually create the cells
    ninnclDic = len(s.innclDic) # number of PMd created in this worker
    for c in xrange(int(s.rank), s.ncells, s.nhosts):
        s.dummies.append(h.Section()) # Create fake sections
        gid = c
        if s.cellnames[gid] == 'PMd':
            cell = celltypes[gid](cellid = gid) # create an NSLOC
            s.inncl.append(h.NetCon(None, cell))  # This netcon receives external spikes
            s.innclDic[gid - s.ncells - s.numPMd] = ninnclDic # This dictionary works in case that PMd's gid starts from 0.
            ninnclDic += 1
        elif s.cellnames[gid] == 'ASC':
            cell = celltypes[gid](cellid = gid) #create an NSLOC    
        else: 
            if s.cellclasses[gid]==3: 
                cell = s.fastspiking(s.dummies[s.cellsperhost], vt=-47, cellid=gid) # Don't use LTS cell, but instead a FS cell with a low threshold
            else: 
                cell = celltypes[gid](s.dummies[s.cellsperhost], cellid=gid) # Create a new cell of the appropriate type (celltypes[gid]) and store it
            if s.verbose>0: s.cells[-1].useverbose(s.verbose, s.filename+'los.txt') # Turn on diagnostic to file
        s.cells.append(cell) 
        s.gidVec.append(gid) # index = local id; value = global id
        s.gidDic[gid] = s.cellsperhost # key = global id; value = local id -- used to get local id because gid.index() too slow!
        s.pc.set_gid2node(gid, s.rank)

        spikevec = h.Vector()
        s.hostspikevecs.append(spikevec)
        spikerecorder = h.NetCon(cell, None)
        spikerecorder.record(spikevec)
        s.spikerecorders.append(spikerecorder)
        s.pc.cell(gid, s.spikerecorders[s.cellsperhost])
        s.cellsperhost += 1 # contain cell numbers per host including PMd and P
    print('  Number of cells on node %i: %i ' % (s.rank,len(s.cells)))
    s.pc.barrier()


    ## Calculate distances and probabilities
    if s.rank==0: print('Calculating connection probabilities (est. time: %i s)...' % (s.performance*s.cellsperhost**2/3e4))
    conncalcstart = s.time() # See how long connecting the cells takes
    nPostCells = 0
    for c in range(s.cellsperhost): # Loop over all postsynaptic cells on this host (has to be postsynaptic because of gid_connect)
        gid = s.gidVec[c] # Increment global identifier       
        if s.cellnames[gid] == 'PMd' or s.cellnames[gid] == 'ASC':
            # There are no presynaptic connections for PMd or ASC.
            continue
        nPostCells += 1
        if s.toroidal: 
            xpath=(abs(xlocs-xlocs[gid]))**2
            xpath2=(s.modelsize-abs(xlocs-xlocs[gid]))**2
            xpath[xpath2<xpath]=xpath2[xpath2<xpath]
            ypath=(abs(ylocs-ylocs[gid]))**2
            ypath2=(s.modelsize-abs(ylocs-ylocs[gid]))**2
            ypath[ypath2<ypath]=ypath2[ypath2<ypath]
            distances = sqrt(xpath + ypath) # Calculate all pairwise distances
        else: distances = sqrt((xlocs-xlocs[gid])**2 + (ylocs-ylocs[gid])**2) # Calculate all pairwise distances
        allconnprobs = s.scaleconnprob[s.EorI,s.EorI[gid]] * s.connprobs[s.cellpops,s.cellpops[gid]] * exp(-distances/s.connfalloff[s.EorI]) # Calculate pairwise probabilities
        allconnprobs[gid] = 0 # Prohibit self-connections using the cell's GID
        seed(id32('%d'%(s.randseed+gid))) # Reset random number generator  
        allrands = rand(s.ncells) # Create an array of random numbers for checking each connection  
        if s.usePlexon:
            for c in xrange(s.popGidStart[s.PMd], s.popGidEnd[s.PMd] + 1):
                allrands[c] = 1
        if s.cellnames[gid] == 'ER5': 
                PMdId = (gid % s.numPMd) + s.ncells - s.numPMd
                allconnprobs[PMdId] = s.connprobs[s.PMd,s.ER5] # to make this connected to ER5
                allrands[PMdId] = 0 # to make this connect to ER5
                distances[PMdId] = 300 # to make delay 5 in conndata[3] 
        makethisconnection = allconnprobs>allrands # Perform test to see whether or not this connection should be made
        preids = array(makethisconnection.nonzero()[0],dtype='int') # Return True elements of that array for presynaptic cell IDs
        postids = array(gid+zeros(len(preids)),dtype='int') # Post-synaptic cell IDs
        s.conndata[0].append(preids) # Append pre-cell ID
        s.conndata[1].append(postids) # Append post-cell ID
        s.conndata[2].append(distances[preids]) # Distances
        s.conndata[3].append(s.mindelay + distances[preids]/float(s.velocity)) # Calculate the delays
        wt1 = s.scaleconnweight[s.EorI[preids],s.EorI[postids]] # N weight scale factors -- WARNING, might be flipped
        wt2 = s.connweights[s.cellpops[preids],s.cellpops[postids],:] # NxM inter-population weights
        wt3 = s.receptorweight[:] # M receptor weights
        finalweights = transpose(wt1*transpose(wt2*wt3)) # Multiply out population weights with receptor weights to get NxM matrix
        s.conndata[4].append(finalweights) # Initialize weights to 0, otherwise get memory leaks
    for pp in range(s.nconnpars): s.conndata[pp] = array(concatenate([s.conndata[pp][c] for c in range(nPostCells)])) # Turn pre- and post- cell IDs lists into vectors
    nconnections = len(s.conndata[0]) # Find out how many connections we're going to make
    conncalctime = time()-conncalcstart # See how long it took
    if s.rank==0: print('  Done; time = %0.1f s' % conncalctime)


    ## Actually make connections
    if s.rank==0: print('Making connections (est. time: %i s)...' % (s.performance*nconnections/9e2))
    print('  Number of connections on host %i: %i' % (s.rank, nconnections))
    connstart = time() # See how long connecting the cells takes
    for con in range(nconnections): # Loop over each connection
        pregid = s.conndata[0][con] # GID of presynaptic cell    
        pstgid = s.conndata[1][con] # Index of postsynaptic cell
        pstid = s.gidDic[pstgid]# Index of postynaptic cell -- convert from GID to local
        newcon = s.pc.gid_connect(pregid, s.cells[pstid]) # Create a connection
        newcon.delay = s.conndata[3][con] # Set delay
        for r in range(s.nreceptors): newcon.weight[r] = s.conndata[4][con][r] # Set weight of connection
        s.connlist.append(newcon) # Connect the two cells
        if s.usestdp: # Using STDP?
            if sum(abs(s.stdprates[s.EorI[pregid],:]))>0 or sum(abs(s.RLrates[s.EorI[pregid],:]))>0: # Don't create an STDP connection if the learning rates are zero
                for r in range(s.nreceptors): # Need a different STDP instances for each receptor
                    if newcon.weight[r]>0: # Only make them for nonzero connections
                        stdpmech = h.STDP(0,sec=s.dummies[pstid]) # Create STDP adjuster
                        stdpmech.hebbwt = s.stdprates[s.EorI[pregid],0] # Potentiation rate
                        stdpmech.antiwt = s.stdprates[s.EorI[pregid],1] # Depression rate
                        stdpmech.wmax = s.maxweight # Maximum synaptic weight
                        precon = s.pc.gid_connect(pregid,stdpmech); precon.weight[0] = 1 # Send presynaptic spikes to the STDP adjuster
                        pstcon = s.pc.gid_connect(pstgid,stdpmech); pstcon.weight[0] = -1 # Send postsynaptic spikes to the STDP adjuster
                        h.setpointer(s.connlist[-1]._ref_weight[r],'synweight',stdpmech) # Associate the STDP adjuster with this weight
                        s.stdpmechs.append(stdpmech) # Save STDP adjuster
                        s.precons.append(precon) # Save presynaptic spike source
                        s.pstcons.append(pstcon) # Save postsynaptic spike source
                        s.stdpconndata.append([pregid,pstgid,r]) # Store presynaptic cell ID, postsynaptic, and receptor
                        if s.useRL: # using RL
                            stdpmech.RLon = 1 # make sure RL is on
                            stdpmech.RLhebbwt = s.RLrates[s.EorI[pregid],0] # Potentiation rate
                            stdpmech.RLantiwt = s.RLrates[s.EorI[pregid],1] # Depression rate
                            stdpmech.tauhebb = stdpmech.tauanti = s.stdpwin # stdp window length (ms)
                            stdpmech.RLwindhebb = stdpmech.RLwindhebb = s.eligwin # RL eligibility trace window length (ms)
                            stdpmech.useRLexp = s.useRLexp # RL 
                            stdpmech.softthresh = s.useRLsoft # RL soft-thresholding
                        else:
                            stdpmech.RLon = 0 # make sure RL is off
                 
    nstdpconns = len(s.stdpconndata) # Get number of STDP connections
    conntime = time()-connstart # See how long it took
    if s.usestdp: print('  Number of STDP connections on host %i: %i' % (s.rank, nstdpconns))
    if s.rank==0: print('  Done; time = %0.1f s' % conntime)


###############################################################################
### Add stimulation
###############################################################################

## IMPLEMENT STIMULATION
def addStimulation():
    if s.usestims:
        for stim in range(len(s.stimpars)): # Loop over each stimulus type
            ts = s.stimpars[stim] # Stands for "this stimulus"
            ts.loc = ts.loc * s.modelsize # scale cell locations to model size
            stimvecs = s.makestim(ts.isi, ts.var, ts.width, ts.weight, ts.sta, ts.fin, ts.shape) # Time-probability vectors
            s.stimstruct.append([ts.name, stimvecs]) # Store for saving later
            s.stimtimevecs.append(h.Vector().from_python(stimvecs[0]))
            
            for c in range(s.cellsperhost):
                gid = s.cellsperhost*int(s.rank)+c # For deciding E or I    
                seed(id32('%d'%(s.randseed+gid))) # Reset random number generator for this cell
                if ts.fraction>rand(): # Don't do it for every cell necessarily
                    if any(s.cellpops[gid]==ts.pops) and s.xlocs[gid]>=ts.loc[0,0] and s.xlocs[gid]<=ts.loc[0,1] and s.ylocs[gid]>=ts.loc[1,0] and s.ylocs[gid]<=ts.loc[1,1]:
                        
                        maxweightincrease = 20 # Otherwise could get infinitely high, infinitely close to the stimulus
                        distancefromstimulus = sqrt(sum((array([s.xlocs[gid], s.ylocs[gid]])-s.modelsize*ts.falloff[0])**2))
                        fallofffactor = min(maxweightincrease,(ts.falloff[1]/distancefromstimulus)**2)
                        s.stimweightvecs.append(h.Vector().from_python(stimvecs[1]*fallofffactor)) # Scale by the fall-off factor
                        
                        stimrand = h.Random()
                        stimrand.MCellRan4() # If everything has the same seed, should happen at the same time
                        stimrand.negexp(1)
                        stimrand.seq(id32('%d'%(s.randseed+gid))*1e3) # Set the sequence i.e. seed
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
        
                        if s.saveraw:
                            stimspikevec = h.Vector() # Initialize vector
                            s.stimspikevecs.append(stimspikevec) # Keep all those vectors
                            stimrecorder = h.NetCon(stimsource, None)
                            stimrecorder.record(stimspikevec) # Record simulation time
                            s.stimrecorders.append(stimrecorder)
        print('  Number of stimuli created on host %i: %i' % (s.rank, len(s.stimsources)))


###############################################################################
### Add background inputs
###############################################################################
def addBackground():
    if s.rank==0: print('Creating background inputs...')
    for c in range(s.cellsperhost): 
        gid = s.gidVec[c]
        if s.cellnames[gid] == 'ASC' or s.cellnames[gid] == 'DSC' or s.cellnames[gid] == 'PMd': # These pops won't receive background stimulations.
            continue 
        backgroundrand = h.Random()
        backgroundrand.MCellRan4(gid,gid*2)
        backgroundrand.negexp(1)
        s.backgroundrands.append(backgroundrand)
        
        backgroundsource = h.NetStim() # Create a NetStim
        backgroundsource.interval = s.backgroundrate**-1*1e3 # Take inverse of the frequency and then convert from Hz^-1 to ms
        backgroundsource.number = s.backgroundnumber # Number of spikes
        backgroundsource.noise = s.backgroundnoise # Fractional noise in timing
        backgroundsource.noiseFromRandom(backgroundrand) # Set it to use this random number generator
        s.backgroundsources.append(backgroundsource) # Save this NetStim
        
        backgroundconn = h.NetCon(backgroundsource, s.cells[c]) # Connect this noisy input to a cell
        for r in range(s.nreceptors): backgroundconn.weight[r]=0 # Initialize weights to 0, otherwise get memory leaks
        backgroundconn.weight[s.backgroundreceptor] = s.backgroundweight[s.EorI[gid]] # Specify the weight -- 1 is NMDA receptor for smoother, more summative activation
        backgroundconn.delay=2 # Specify the delay in ms -- shouldn't make a spot of difference
        s.backgroundconns.append(backgroundconn) # Save this connnection
        
        if s.saveraw:
            backgroundspikevec = h.Vector() # Initialize vector
            s.backgroundspikevecs.append(backgroundspikevec) # Keep all those vectors
            backgroundrecorder = h.NetCon(backgroundsource, None)
            backgroundrecorder.record(backgroundspikevec) # Record simulation time
            s.backgroundrecorders.append(backgroundrecorder)
    print('  Number created on host %i: %i' % (s.rank, len(s.backgroundsources)))
    s.pc.barrier()


###############################################################################
### Setup Simulation
###############################################################################
def setupSim():
    global nstdpconns

    ## Initialize STDP -- just for recording
    if s.usestdp:
        if s.rank==0: print('\nSetting up STDs...')
        if s.usestdp:
            weightchanges = [[] for ps in range(s.nstdpconns)] # Create an empty list for each STDP connection -- warning, slow with large numbers of connections!
        for ps in range(s.nstdpconns): weightchanges[ps].append([0, s.stdpmechs[ps].synweight]) # Time of save (0=initial) and the weight


    ## Set up LFP recording
    for c in range(s.cellsperhost): # Loop over each cell and decide which LFP population, if any, it belongs to
        gid = s.gidVec[c] # Get this cell's GID
        if s.cellnames[gid] == 'ASC' or s.cellnames[gid] == 'PMd': # 'ER2' won't be fired by background stimulations.
                continue 
        for pop in range(s.nlfps): # Loop over each LFP population
            thispop = s.cellpops[gid] # Population of this cell
            if sum(s.lfppops[pop]==thispop)>0: # There's a match
                s.lfpcellids[pop].append(gid) # Flag this cell as belonging to this LFP population


    ## Set up raw recording
    if s.saveraw: 
        if s.rank==0: print('\nSetting up raw recordins...')
        nquantities = 4 # Number of variables from each cell to record from
        # Later this part should be modified because NSLOC doesn't have V, u and I.
        for c in range(s.cellsperhost):
            gid = s.gidVec[c] # Get this cell's GID
            if s.cellnames[gid] == 'ASC' or s.cellnames[gid] == 'PMd': # NSLOC doesn't have V, u and I
                continue 
            recvecs = [h.Vector() for q in range(nquantities)] # Initialize vectors
            recvecs[0].record(h._ref_t) # Record simulation time
            recvecs[1].record(s.cells[c]._ref_V) # Record cell voltage
            recvecs[2].record(s.cells[c]._ref_u) # Record cell recovery variable
            recvecs[3].record(s.cells[c]._ref_I) # Record cell current
            s.rawrecordings.append(recvecs) # Keep all those vectors


    ## Set up virtual arm
    if s.useArm != 'None':
            s.arm.setup(s)#duration, loopstep, RLinterval, pc, scale, popnumbers, p)


    ## Communication setup for plexon input
    if s.usePlexon:
        h('''
            objref cvode
            cvode = new CVode()
            tstop = 0
        ''')

        if s.isOriginal == 0: # With communication program
            if s.rank == 0: 
                #serverManager = s.server.Manager() # isDp in confis.py = 0
                s.server.Manager.start() # launch sever process
                print "Server process completed and callback function initalized"
            e = s.server.Manager.Event() # Queue callback function in the NEURON queue

        
        # Wait for external spikes for PMd from Plexon  
            if s.rank == 0:
                if s.server.isCommunication == 1:
                    s.server.getServerInfo() # show parameters of the server process
                    print "[Waiting for spikes; run the client on Windows machine...]"
                    while s.server.queue.empty(): # only Rank 0 is waiting for spikes in the queue.
                        pass
            s.pc.barrier() # other workers are waiting here.


###############################################################################
### Run Simulation
###############################################################################
def runSim():
    global timeoflastsave

    if s.rank == 0:
        print('\nRunnins...')
    runstart = time() # See how long the run takes
    s.pc.set_maxstep(10) # MPI: Set the maximum integration time in ms -- not very important
    init() # Initialize the simulation

    while round(h.t) < s.duration:
        s.pc.psolve(min(s.duration,h.t+s.loopstep)) # MPI: Get ready to run the simulation (it isn't actually run until pc.runworker() is called I think)
        if s.simMode == 0:
            if s.rank==0 and (round(h.t) % s.progupdate)==0: print('  t = %0.1f s (%i%%; time remaining: %0.1f s)' % (h.t/1e3, int(h.t/s.duration*100), (s.duration-h.t)*(time()-runstart)/h.t))
        else:
            if s.rank==0: print('  t = %0.1f s (%i%%; time remaining: %0.1f s)' % (h.t/1e3, int(h.t/s.duration*100), (s.duration-h.t)*(time()-runstart)/h.t))

        # Calculate LFP -- WARNING, need to think about how to optimize
        if s.savelfps:
            s.lfptime.append(h.t) # Append current time
            tmplfps = zeros((s.nlfps)) # Create empty array for storing LFP voltages
            for pop in range(s.nlfps):
                for c in range(len(s.lfpcellids[pop])):
                    id = s.gidDic[s.lfpcellids[pop][c]]# Index of postynaptic cell -- convert from GID to local
                    tmplfps[pop] += s.cells[id].V # Add voltage to LFP estimate
                if s.verbose:
                    if s.server.Manager.ns.isnan(tmplfps[pop]) or s.server.Manager.ns.isinf(tmplfps[pop]):
                        print "Nan or inf"
            s.hostlfps.append(tmplfps) # Add voltages

        # Periodic weight saves
        if s.usestdp: 
            timesincelastsave = h.t - s.timeoflastsave
            if timesincelastsave>=s.timebetweensaves:
                timeoflastsave = h.t
                for ps in range(s.nstdpconns):
                    if s.stdpmechs[ps].synweight != s.weightchanges[ps][-1][-1]: # Only store connections that changed; [ps] = this connection; [-1] = last entry; [-1] = weight
                        s.weightchanges[ps].append([timeoflastsave, s.stdpmechs[ps].synweight])
        

        ## Virtual arm 
        if s.useArm != 'None':
            armStart = time()
            s.arm.run(h.t, s) #pc, cells, gidVec, gidDic, s.cellsperhost, hostspikevecs) # run virtual arm apparatus (calculate command, move arm, feedback)
            if s.useRL and (h.t - s.timeoflastRL >= s.RLinterval): # if time for next RL
                vec = h.Vector()
                if s.rank == 0:
                    critic = s.arm.RLcritic() # get critic signal (-1, 0 or 1)
                    s.pc.broadcast(vec.from_python([critic]), 0) # convert python list to hoc vector for broadcast data received from arm
                    print critic
                else: # other workers
                    s.pc.broadcast(vec, 0)
                    critic = vec.to_python()[0]
                if critic != 0: # if critic signal indicates punishment (-1) or reward (+1)
                    for stdp in s.stdpmechs: # for all connections in stdp conn list
                        pass
                        stdp.reward_punish(float(critic)) # run stds.mod method to update syn weights based on RL
            # Synaptic scaling?
        
            #print(' Arm time = %0.4f s' % time() - armStart)


        ## Time adjustment for online mode simulation
        if s.usePlexon and s.simMode == 1:                   
            # To avoid izhi cell's over shooting when h.t moves forward because sim is slow.
            for c in range(s.cellsperhost): 
                gid = s.gidVec[c]
                if s.cellnames[gid] == 'PMd': # 'PMds don't have t0 variable.
                    continue
                s.cells[c].t0 = s.server.newCurrTime.value - h.dt             
            dtSave = h.dt # save original dt
            h.dt = s.server.newCurrTime.value - h.t # new dt
            active = h.cvode.active()
            if active != 0:
                h.cvode.active(0)         
            h.fadvance() # Integrate with new dt
            if active != 0:
                h.cvode.active(1)         
            h.dt = dtSave # Restore orignal dt   
                
    runtime = time()-runstart # See how long it took
    if s.rank==0: print('  Done; run time = %0.1f s; real-time ratio: %0.2f.' % (runtime, s.duration/1000/runtime))
    s.pc.barrier() # Wait for all hosts to get to this point


###############################################################################
### Finalize Simulation  (gather data from nodes, etc.)
###############################################################################
def finalizeSim():
    ## Pack data from all hosts
    if s.rank==0: print('\nGathering spikes...')
    gatherstart = time() # See how long it takes to plot
    for host in range(s.nhosts): # Loop over hosts
        if host==s.rank: # Only act on a single host
            hostspikecells=array([])
            hostspiketimes=array([])
            for c in range(len(s.hostspikevecs)):
                thesespikes = array(s.hostspikevecs[c]) # Convert spike times to an array
                nthesespikes = len(thesespikes) # Find out how many of spikes there were for this cell
                hostspiketimes = concatenate((hostspiketimes, thesespikes)) # Add spikes from this cell to the list
                #hostspikecells = concatenate((hostspikecells, (c+host*s.cellsperhost)*ones(nthesespikes))) # Add this cell's ID to the list
                hostspikecells = concatenate((hostspikecells, s.gidVec[c]*ones(nthesespikes))) # Add this cell's ID to the list
                if s.saveraw:
                    for q in range(s.nquantities):
                        s.rawrecordings[c][q] = array(s.rawrecordings[c][q])
            messageid=s.pc.pack([hostspiketimes, hostspikecells, s.hostlfps, s.conndata, s.stdpconndata, s.weightchanges, s.rawrecordings]) # Create a mesage ID and store this value
            s.pc.post(host,messageid) # Post this message


    ## Unpack data from all hosts
    if s.rank==0: # Only act on a single host
        for host in range(s.nhosts): # Loop over hosts
            s.pc.take(host) # Get the last message
            hostdata = s.pc.upkpyobj() # Unpack them
            s.allspiketimes = concatenate((s.allspiketimes, hostdata[0])) # Add spikes from this cell to the list
            s.allspikecells = concatenate((s.allspikecells, hostdata[1])) # Add this cell's ID to the list
            if s.savelfps: lfps += array(hostdata[2]) # Sum LFP voltages
            for pp in range(s.nconnpars): s.allconnections[pp] = concatenate((s.allconnections[pp], hostdata[3][pp])) # Append pre/post synapses
            if s.usestdp and len(hostdata[4]): # Using STDP and at least one STDP connection
                s.allstdpconndata = concatenate((s.allstdpconndata, hostdata[4])) # Add data on STDP connections
                for ps in range(len(hostdata[4])): s.weightchanges.append(hostdata[5][ps]) # "ps" stands for "plastic synapse"
            if s.saveraw:
                for c in range(len(hostdata[6])): s.allraw.append(hostdata[6][c]) # Append cell-by-cell

        s.totalspikes = len(s.allspiketimes) # Keep a running tally of the number of spikes
        s.totalconnections = len(s.allconnections[0]) # Total number of connections
        s.totalstdpconns = len(s.allstdpconndata) # Total number of STDP connections
        

        # Record input spike times
        if s.saveraw and s.usebackground:
            for c in range(len(s.backgroundspikevecs)):
                thesespikes = array(s.backgroundspikevecs[c])
                s.allbackgroundspiketimes = concatenate((s.allbackgroundspiketimes, thesespikes)) # Add spikes from this stimulator to the list
                s.allbackgroundspikecells = concatenate((s.allbackgroundspikecells, c+zeros(len(thesespikes)))) # Add this cell's ID to the list
            s.backgrounddata = transpose(vstack([s.allbackgroundspikecells,s.allbackgroundspiketimes]))
        else: s.backgrounddata = [] # For saving s no error
        
        if s.saveraw and s.usestims:
            for c in range(len(s.stimspikevecs)):
                thesespikes = array(s.stimspikevecs[c])
                s.allstimspiketimes = concatenate((s.allstimspiketimes, thesespikes)) # Add spikes from this stimulator to the list
                s.allstimspikecells = concatenate((s.allstimspikecells, c+zeros(len(thesespikes)))) # Add this cell's ID to the list
            s.stimspikedata = transpose(vstack([s.allstimspikecells,s.allstimspiketimes]))
        else: s.stimspikedata = [] # For saving so no error
    gathertime = time()-gatherstart # See how long it took
    if s.rank==0: print('  Done; gather time = %0.1f s.' % gathertime)
    s.pc.barrier()

    print 'min delay for node ',s.rank,' is ', s.pc.set_maxstep(10)
    mindelay = s.pc.allreduce(s.pc.set_maxstep(10), 2) # flag 2 returns minimum value
    if s.rank==0: print 'Minimum delay (time-step for queue exchange) is ',mindelay

    ## Run and clean up
    s.pc.runworker() # MPI: Start simulations running on each host
    s.pc.done() # MPI: Close MPI


    ## Finalize virtual arm (es. close pipes, saved data)
    if s.useArm != 'None':
      s.arm.close()


    # terminate the server process
    if s.usePlexon:
      if s.isOriginal == 0:
          s.server.Manager.stop()

    ## Print statistics
    print('\nAnalyzins...')
    firingrate = float(s.totalspikes)/s.ncells/s.duration*1e3 # Calculate firing rate -- confusing but cool Python trick for iterating over a list
    connspercell = s.totalconnections/float(s.ncells) # Calculate the number of connections per cell
    print('  Run time: %0.1f s (%i-s sim; %i scale; %i cells; %i workers)' % (s.runtime, s.duration/1e3, scale, s.ncells, s.nhosts))
    print('  Spikes: %i (%0.2f Hz)' % (s.totalspikes, firingrate))
    print('  Connections: %i (%i STDP; %0.2f per cell)' % (s.totalconnections, s.totalstdpconns, connspercell))
    print('  Mean connection distance: %0.2f um' % mean(s.allconnections[2]))
    print('  Mean connection delay: %0.2f ms' % mean(s.allconnections[3]))


###############################################################################
### Save data
###############################################################################
def saveData():
    ## Save to txt file (spikes and conn)
    if s.savetxt: 
        filename = 'data/m1ms-spk.txt'
        fd = open(filename, "w")
        for c in range(len(s.allspiketimes)):
            print >> fd, int(s.allspikecells[c]), s.allspiketimes[c], s.popNamesDic[s.cellnames[int(s.allspikecells[c])]]
        fd.close()
        print "[Spikes are stored in", filename, "]"

        if s.verbose:
            filename = 'm1ms-conn.txt'
            fd = open(filename, "w")
            for c in range(len(s.allconnections[0])):
                print >> fd, int(s.allconnections[0][c]), int(s.allconnections[1][c]), s.allconnections[2][c], s.allconnections[3][c], s.allconnections[4][c] 
            fd.close()
            print "[Connections are stored in", filename, "]"

    ## Save to mat file
    if s.savemat:
        print('Saving output as %s...' % filename)
        savestart = time() # See how long it takes to save
        from scipy.io import savemat # analysis:ignore -- because used in exec() statement
        
        # Save simulation code
        filestosave = ['main.py', 'shared.py', 'network.py', 'arm.py', 'arminterface.py', 'server.py', 'izhi.py', 'izhi.mod', 'stdp.mod', 'nsloc.py', 'nsloc.mod'] # Files to save
        argv = [];
        simcode = [argv, filestosave] # Start off with input parameters, if any, and then the list of files being saved
        for f in range(len(filestosave)): # Loop over each file
            fobj = open(filestosave[f]) # Open it for reading
            simcode.append(fobj.readlines()) # Append to list of code to save
            fobj.close() # Close file object
        
        # Tidy variables
        spikedata = vstack([s.allspikecells,s.allspiketimes]).T # Put spike data together
        connections = vstack([s.allconnections[0],s.allconnections[1]]).T # Put connection data together
        distances = s.allconnections[2] # Pull out distances
        delays = s.allconnections[3] # Pull out delays
        weights = s.allconnections[4] # Pull out weights
        stdpdata = s.allstdpconndata # STDP connection data
        if s.usestims: stimdata = [vstack(s.stimstruct[c][1]).T for c in range(len(stimstruct))] # Only pull out vectors, not text, in stimdata

        # Save variables
        info = {'timestamp':datetime.today().strftime("%d %b %Y %H:%M:%S"), 'runtime':s.runtime, 'popnames':s.popnames, 'popEorI':s.popEorI} # Save date, runtime, and input arguments
        variablestosave = ['info', 'simcode', 's.spikedata', 's.cellpops', 's.cellnames', 's.cellclasses', 's.xlocs', 's.ylocs', 's.zlocs', 's.connections', 's.distances', 's.delays', 's.weights', 's.EorI']
        if s.savelfps:  variablestosave.extend(['s.lfptime', 's.lfps'])   
        if s.usestdp: variablestosave.extend(['s.stdpdata', 's.weightchanges'])
        if s.saveraw: variablestosave.extend(['s.backgrounddata', 's.stimspikedata', 's.allraw'])
        if s.usestims: variablestosave.extend(['s.stimdata'])
        savecommand = "savemat(filename, {"
        for var in range(len(variablestosave)): savecommand += "'" + variablestosave[var] + "':" + variablestosave[var] + ", " # Create command out of all the variables
        savecommand = savecommand[:-2] + "}, oned_as='column')" # Omit final comma-space and complete command
        exec(savecommand) # Actually perform the save
        
        savetime = time()-savestart # See how long it took to save
        print('  Done; time = %0.1f s' % savetime)


###############################################################################
### Plot data
###############################################################################
def plotData():
    ## Plotting
    if s.plotraster: # Whether or not to plot
        if (s.totalspikes>s.maxspikestoplot): 
            disp('  Too many spikes (%i vs. %i)' % (s.totalspikes, s.maxspikestoplot)) # Plot raster, but only if not too many spikes
        elif s.nhosts>1: 
            disp('  Plotting raster despite using too many cores (%i)' % s.nhosts) 
            analysis.plotraster()#;allspiketimes, allspikecells, EorI, ncells, connspercell, backgroundweight, firingrate, duration)
        else: 
            print('Plotting raster...')
            analysis.plotraster()#allspiketimes, allspikecells, EorI, ncells, connspercell, backgroundweight, firingrate, duration)

    if s.plotconn:
        print('Plotting connectivity matrix...')
        analysis.plotconn()

    if s.plotweightchanges:
        print('Plotting weight changes...')
        analysis.plotweightchanges()#p, allconnections, allstdpconndata, weightchanges)

    show()


