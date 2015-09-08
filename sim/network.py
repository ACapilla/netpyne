
"""
network.py 

Defines Network class which contains cell objects and network-realated methods

Contributors: salvadordura@gmail.com
"""

from pylab import seed, rand, sqrt, exp, transpose, ceil, concatenate, array, zeros, ones, vstack, show, disp, mean, inf, concatenate
import random
from time import time, sleep
import pickle
import warnings
from neuron import h  # import NEURON
import shared as s


class Network(object):

    ###############################################################################
    # initialize variables
    ###############################################################################
    def __init__(self, params = None):
        self.params = params

    ###############################################################################
    # Set network params
    ###############################################################################
    def setParams(self, params):
        self.params = params

    ###############################################################################
    # Instantiate network populations (objects of class 'Pop')
    ###############################################################################
    def createPops(self):
        self.pops = []  # list to store populations ('Pop' objects)
        for popParam in self.params['popParams']: # for each set of population paramseters 
            self.pops.append(s.Pop(popParam))  # instantiate a new object of class Pop and add to list pop


    ###############################################################################
    # Create Cells
    ###############################################################################
    def createCells(self):
        s.pc.barrier()
        if s.rank==0: print("\nCreating simulation of %i cell populations for %0.1f s on %i hosts..." % (len(self.pops), s.cfg['duration']/1000.,s.nhosts)) 
        self.gidVec = [] # Empty list for storing GIDs (index = local id; value = gid)
        self.gidDic = {} # Empty dict for storing GIDs (key = gid; value = local id) -- ~x6 faster than gidVec.index()  
        self.cells = []
        for ipop in self.pops: # For each pop instantiate the network cells (objects of class 'Cell')
            newCells = ipop.createCells() # create cells for this pop using Pop method
            self.cells.extend(newCells)  # add to list of cells
            s.pc.barrier()
            if s.rank==0 and s.cfg['verbose']: print('Instantiated %d cells of population %s'%(len(newCells), ipop.tags['popLabel']))    
        s.simdata.update({name:h.Vector(1e4).resize(0) for name in ['spkt','spkid']})
        print('  Number of cells on node %i: %i ' % (s.rank,len(self.cells)))            
        

    ###############################################################################
    # Connect Cells
    ###############################################################################
    def connectCells(self):
        # Instantiate network connections based on the connectivity rules defined in params
        if s.rank==0: print('Making connections...'); connstart = time()

        if s.nhosts > 1: # Gather tags from all cells 
            allCellTags = s.sim.gatherAllCellTags()  
        else:
            allCellTags = {cell.gid: cell.tags for cell in self.cells} 
        
        for connParam in self.params['connParams']:  # for each conn rule or parameter set
            if 'sec' not in connParam: connParam['sec'] = None  # if section not specified, make None (will be assigned to first section in cell)
            if 'synReceptor' not in connParam: connParam['synReceptor'] = None  # if section not specified, make None (will be assigned to first synapse in cell)     
            preCells = allCellTags  # initialize with all presyn cells 
            for condKey,condValue in connParam['preTags'].iteritems():  # Find subset of cells that match presyn criteria
                preCells = {gid: tags for (gid,tags) in preCells.iteritems() if tags[condKey] == condValue}  # dict with pre cell tags
            
            postCells = {cell.gid:cell for cell in self.cells}
            for cellPreondKey,condValue in connParam['postTags'].iteritems():  # Find subset of cells that match postsyn criteria
                postCells = {gid: cell for (gid,cell) in postCells.iteritems() if cell.tags[condKey] == condValue}  # dict with post Cell objects

            connFunc = getattr(self, connParam['connFunc'])  # get function name from params
            connFunc(preCells, postCells, connParam)  # call specific conn function
        
        # print('  Number of connections on host %i: %i ' % (s.rank, len(self.conns)))
        # s.pc.barrier()
        # if s.rank==0: conntime = time()-connstart; print('  Done; time = %0.1f s' % conntime) # See how long it took


    ###############################################################################
    # Add background inputs
    ###############################################################################
    # def addBackground(self):
    #     if s.rank==0: print('Creating background inputs...')
    #     for cellPre in self.cells: 
    #         c.addBackground()
    #     print('  Number created on host %i: %i' % (s.rank, len(self.cells)))
    #     s.pc.barrier()


        # netParams['connParams'].append({'preTags': {'popLabel': 'background'}, 'postTags': {'cellType': 'IT' }, # background -> IT
        #     'connFunc': 'fullConn',
        #     'probability': 0.5, 
        #     'weight': 0.1, 
        #     'syn': 'NMDA',
        #     'delay': 5})  

                
   ###############################################################################
    ### Full connectivity
    ###############################################################################
    def fullConn(self, preCells, postCells, connParam):
        ''' Generates connections between all pre and post-syn cells '''
        if all (k in connParam for k in ('delayMean', 'delayVar')):  # generate list of delays based on mean and variance
            random.seed(s.sim.id32('%d'%(s.cfg['randseed']+postCells.keys()[0])))  # Reset random number generator  
            randDelays = [random.gauss(connParam['delayMean'], connParam['delayVar']) for pre in range(len(preCells)*len(postCells))]  # select random delays based on mean and var params    
        else:
            randDelays = None   
            delay = connParam['delay']  # fixed delay
        for postCellGid, postCell in postCells.iteritems():  # for each postsyn cell
            for preCellGid in preCells.keys():  # for each presyn cell
                if randDelays:  delay = randDelays.pop()  # set random delay
                params = {'preGid': preCellGid, 
                'sec': connParam['sec'], 
                'synReceptor': connParam['synReceptor'], 
                'weight': connParam['weight'], 'delay': delay, 
                'threshold': connParam['threshold']}
                postCell.addConn(params)  # call cell method to add connections


    ###############################################################################
    ### Random connectivity
    ###############################################################################
    def randConn(self, preCells, postCells, connParam):
        ''' Generates connections between  maxcons random pre and postsyn cells'''
        if 'maxConns' not in connParam: connParam['maxConns'] = len(preCells)
        if all (k in connParam for k in ('delayMean', 'delayVar')):  # generate list of delays based on mean and variance
            random.seed(s.sim.id32('%d'%(s.cfg['randseed']+postCells.keys()[0])))  # Reset random number generator  
            randDelays = [random.gauss(connParam['delayMean'], connParam['delayVar']) for pre in range(connParam['maxConns']*len(postCells))] # select random delays based on mean and var params    
        else:
            randDelays = None   
            delay = connParam['delay']  # fixed delay
        for postCellGid, postCell in postCells.iteritems():  # for each postsyn cell
            preCellGids = random.sample(preCells.keys(), random.randint(0, connParam['maxCons'])) # select random subset of pre cells
            for preCellGid in preCellGids: # for each presyn cell
                if randDelays:  delay = randDelays.pop()  # set random delay
                params = {'preGid': preCellGid, 
                'sec': connParam['sec'], 
                'synReceptor': connParam['synReceptor'], 
                'weight': connParam['weight'], 'delay': delay, 
                'threshold': connParam['threshold']}
                postCell.addConn(params)  # call cell method to add connections


    ###############################################################################
    ### Yfrac-based connectivity
    ###############################################################################
    def yfracConn(self, preCells, postCells, connParam):
        ''' Calculate connectivity as a func of preCell.topClass, preCell['yfrac'], postCell.topClass, postCell.tags['yfrac']
            preCells = {gid: tags} 
            postCells = {gid: Cell object}
            '''
        for postCell in postCells.values():
            # calculate distances of pre to post
            if self.params['toroidal']: 
                xpath=[(preCellTags['x']-postCell.tags['x'])**2 for preCellTags in preCells.values()]
                xpath2=[(s.modelsize - abs(preCellTags['x']-postCell.tags['x']))**2 for preCellTags in preCells.values()]
                xpath[xpath2<xpath]=xpath2[xpath2<xpath]
                xpath=array(xpath)
                ypath=array([((preCellTags['yfrac']-postCell.tags['yfrac'])*s.corticalthick)**2 for preCellTags in preCells.values()])
                zpath=[(preCellTags['z']-postCell.tags['z'])**2 for preCellTags in preCells.values()]
                zpath2=[(s.modelsize - abs(preCellTags['z']-postCell.tags['z']))**2 for preCellTags in preCells.values()]
                zpath[zpath2<zpath]=zpath2[zpath2<zpath]
                zpath=array(zpath)
                distances = array(sqrt(xpath + zpath)) # Calculate all pairwise distances
                distances3d = sqrt(array(xpath) + array(ypath) + array(zpath)) # Calculate all pairwise 3d distances
            else: 
               distances = sqrt([(preCellTags['x']-postCell.tags['x'])**2 + \
                (preCellTags['z']-postCell.tags['z'])**2 for preCellTags in preCells.values()])  # Calculate all pairwise distances
               distances3d = sqrt([(preCellTags['x']-postCell.tags['x'])**2 + \
                (preCellTags['yfrac']*self.params['corticalthick']-postCell.tags['yfrac'])**2 + \
                (preCellTags['z']-postCell.tags['z'])**2 for preCellTags in preCells.values()])  # Calculate all pairwise distances
            allConnProbs = array([self.params['scaleconnprob'] * \
                exp(-distances/self.params['connfalloff']) * \
                connParam['probability'](preCellTags['yfrac'], postCell.tags['yfrac']) \
                for preCellTags in preCells.values()]) # Calculate pairwise probabilities
         
            seed(s.sim.id32('%d'%(s.cfg['randseed']+postCell.gid)))  # Reset random number generator  
            allRands = rand(len(allConnProbs))  # Create an array of random numbers for checking each connection
            makeThisConnection = allConnProbs>allRands # Perform test to see whether or not this connection should be made
            preInds = array(makeThisConnection.nonzero()[0],dtype='int') # Return True elements of that array for presynaptic cell IDs
   
            delays = self.params['mindelay'] + distances[preInds]/float(self.params['velocity']) # Calculate the delays
            weight = self.parms['scaleconnweight'] * connParam['weight']
            for i in preInds:
                params = {'preGid': reCells.keys()[i], 
                'sec': connParam['sec'], 
                'synReceptor': connParam['synReceptor'], 
                'weight': weight, 
                'delay': delays[i], 
                'threshold': connParam['threshold']}
                postCell.addConn(params)  # call cell method to add connections

      
