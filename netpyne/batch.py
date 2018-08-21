"""
batch.py 

Class to setup and run batch simulations

Contributors: salvadordura@gmail.com
"""

import imp
import json
import logging
import datetime
from neuron import h
from netpyne import specs
from netpyne.utils import bashTemplate
from random import Random
from time import sleep, time
from itertools import izip, product
from subprocess import Popen, PIPE
from inspyred.ec import Bounder
from inspyred.ec import EvolutionaryComputation
from inspyred.ec.terminators import generation_termination
from inspyred.ec.replacers import generational_replacement
from inspyred.ec.variators import uniform_crossover, mutator
from inspyred.ec.observers import stats_observer, file_observer
from inspyred.ec.selectors import default_selection, tournament_selection

pc = h.ParallelContext() # use bulletin board master/slave
if pc.id()==0: pc.master_works_on_jobs(0) 

# -------------------------------------------------------------------------------
# function to run single job using ParallelContext bulletin board (master/slave) 
# -------------------------------------------------------------------------------
# func needs to be outside of class  gen_0_inv_0_cfg.json init.py netParams.py
def runJob(script, cfgSavePath, netParamsSavePath, simDataPath):
    # print '\nJob in rank id: ',pc.id()
    command = 'nrniv %s simConfig=%s netParams=%s' % (script, cfgSavePath, netParamsSavePath) 
    # print command+'\n'
    with open(simDataPath+'.run', 'w') as outf, open(simDataPath+'.err', 'w') as errf:
        Popen(command.split(' '), stdout=outf, stderr=errf)
    
    # proc = Popen(command.split(' '), stdout=PIPE, stderr=PIPE)
    # print proc.stdout.read()

# -------------------------------------------------------------------------------
# function to create a folder if it does not exist
# -------------------------------------------------------------------------------
def createFolder(folder):
    import os
    if not os.path.exists(folder):
        try:
            os.mkdir(folder)
        except OSError:
            print ' Could not create %s' %(folder)
# -------------------------------------------------------------------------------
# function to convert tuples to strings (avoids erro when saving/loading)
# -------------------------------------------------------------------------------
def tupleToStr (obj):
    #print '\nbefore:', obj
    if type(obj) == list:
        for item in obj:
            if type(item) in [list, dict]:
                tupleToStr(item)
    elif type(obj) == dict:
        for key,val in obj.iteritems():
            if type(val) in [list, dict]:
                tupleToStr(val)
            if type(key) == tuple:
                obj[str(key)] = obj.pop(key) 
    #print 'after:', obj
    return obj
# -------------------------------------------------------------------------------
# function to modify parameter in object of type specs.SimConfig
# -------------------------------------------------------------------------------
def setCfgNestedParam(cfg, paramLabel, paramVal):
    if isinstance(paramLabel, tuple):
        container = cfg
        for ip in range(len(paramLabel)-1):
            if isinstance(container, specs.SimConfig):
                container = getattr(container, paramLabel[ip])
            else:
                container = container[paramLabel[ip]]
        container[paramLabel[-1]] = paramVal
    else:
        setattr(cfg, paramLabel, paramVal) # set simConfig params
# -------------------------------------------------------------------------------
# Evolutionary optimization: Parallel evaluation
# -------------------------------------------------------------------------------
def evaluator(candidates, args):
    import os
    import signal
    global ngen
    ngen += 1
    total_jobs = 0

    # options slurm, mpi
    type = args.get('type', 'mpi_direct')
    
    # paths to required scripts
    script = '../../' + args.get('script', 'init.py')
    cfgSavePath = '../' + args.get('cfgSavePath')
    netParamsSavePath = '../../' + args.get('netParamsSavePath')
    simDataFolder = args.get('simDataFolder') + '/gen_' + str(ngen)
    
    # mpi command setup
    nodes = args.get('nodes', 1)
    paramLabels = args.get('paramLabels', [])
    coresPerNode = args.get('coresPerNode', 1)
    mpiCommand = args.get('mpiCommand', 'ibrun')
    numproc = nodes*coresPerNode
    
    # slurm setup
    custom = args.get('custom', '')
    folder = args.get('folder', '.')
    email = args.get('email', 'a@b.c')
    walltime = args.get('walltime', '00:01:00')
    reservation = args.get('reservation', None)
    allocation = args.get('allocation', 'csd403') # NSG account

    # modules and functions
    cfg = args.get('cfg')

    # fitness function
    fitness_expression = args.get('fitness')
    default_fitness = args.get('default_fitness')
    
    # read params or set defaults
    sleepInterval = args.get('sleepInterval', 0.2)
    
    # create folder if it does not exist
    createFolder(simDataFolder)
    
    # remember pids in a list
    pids = list()
    # create a job for each candidate
    for candidate_index, candidate in enumerate(candidates):
        # required for slurm
        sleep(sleepInterval)
        
        # name and path
        jobName = "gen_" + str(ngen) + "_cand_" + str(candidate_index)
        simDataPath = simDataFolder + '/' + jobName
        
        # modify cfg instance with candidate values
        for label, value in zip(paramLabels, candidate):
            setCfgNestedParam(cfg, label, value)
            print 'set %s=%s' % (label, value)
        
        # change output name
        if type=='mpi_bulletin':
            setCfgNestedParam(cfg, "filename", simDataPath)
        else:
            setCfgNestedParam(cfg, "filename", jobName)
            
        # save cfg instance to file
        cfg.save(simDataPath + '_cfg.json')
        
        if type=='mpi_bulletin':
            # ----------------------------------------------------------------------
            # MPI master-slaves
            # ----------------------------------------------------------------------
            pc.submit(runJob, './'+script.split('../../')[1], simDataPath+'_cfg.json', './'+netParamsSavePath.split('../../')[1], simDataPath)
            pids.append("-")
            print '-'*80
        else:
            # ----------------------------------------------------------------------
            # MPI job commnand
            # ----------------------------------------------------------------------
            command = '%s -np %d nrniv -python -mpi %s simConfig=%s netParams=%s ' % (mpiCommand, numproc, script, jobName+'_cfg.json', netParamsSavePath)
            # ----------------------------------------------------------------------
            # run on local machine with <nodes*coresPerNode> cores
            # ----------------------------------------------------------------------
            if type=='mpi_direct':
                executer = '/bin/bash'
                jobString = bashTemplate('mpi_direct') %(custom, simDataFolder, command)
            # ----------------------------------------------------------------------
            # run on HPC through slurm
            # ----------------------------------------------------------------------
            elif type=='hpc_slurm':
                executer = 'sbatch'
                res = '#SBATCH --res=%s' % (reservation) if reservation else ''
                jobString = bashTemplate('hpc_slurm') % (jobName, allocation, walltime, nodes, coresPerNode, simDataPath, simDataPath, email, res, custom, simDataFolder, command)
            # ----------------------------------------------------------------------
            # run on HPC through PBS
            # ----------------------------------------------------------------------
            elif type=='hpc_torque':
                executer = 'qsub'
                queueName = args.get('queueName', 'default')
                nodesppn = 'nodes=%d:ppn=%d' % (nodes, coresPerNode)
                jobString = bashTemplate('hpc_torque') % (jobName, walltime, queueName, nodesppn, simDataPath, simDataPath, custom, command)
            # ----------------------------------------------------------------------
            # save job and run
            # ----------------------------------------------------------------------
            print 'Submitting job ', jobName
            print jobString
            print '-'*80
            # save file 
            batchfile = '%s.sbatch' % (simDataPath)
            with open(batchfile, 'w') as text_file:
                text_file.write("%s" % jobString)
            
            with open(simDataPath+'.run', 'w') as outf, open(simDataPath+'.err', 'w') as errf:
                pids.append(Popen([executer, batchfile], stdout=outf,  stderr=errf, preexec_fn=os.setsid).pid)
        total_jobs += 1
        sleep(0.1)
    # ----------------------------------------------------------------------
    # gather data and compute fitness
    # ----------------------------------------------------------------------
    if type=='mpi_bulletin':
        # wait for pc bulletin board jobs to finish
        try:
            while pc.working():
                sleep(1)
            #pc.done()
        except:
            pass
            
    num_iters = 0
    jobs_completed = 0
    targetFitness = [None for cand in candidates]
    # print outfilestem
    print "waiting jobs from generation: %d/%d to finish..." %(ngen, args.get('max_generations'))
    print "PID's: %r" %(pids)
    # start fitness calculation
    while jobs_completed < total_jobs:
        unfinished = [i for i, x in enumerate(targetFitness) if x is None ]
        for candidate_index in unfinished:
            try: # load simData and evaluate fitness
                simDataPath = simDataFolder + "/gen_" + str(ngen) + "_cand_" + str(candidate_index)
                with open('%s.json'% (simDataPath)) as file:
                    simData = json.load(file)['simData']
                targetFitness[candidate_index] = eval(fitness_expression)
                jobs_completed += 1
            except:
                pass
        num_iters += 1
        if num_iters >= args.get('maxiter_wait', 5000): 
            print "max iterations reached -- remaining jobs set to default fitness"
            for canditade_index in unfinished:
                targetFitness[canditade_index] = default_fitness
                jobs_completed += 1
        print 'completed: %d' %(jobs_completed)
        sleep(args.get('time_sleep', 1))
    # kill all processes
    if pids[0]!="-":
        try: 
            for pid in pids: os.killpg(os.getpgid(pid), signal.SIGTERM)
        except:
            print 'SEEMS JOBS WHERE CLOSED ALREADY'
    # return
    pc.done()
    print "DONE"
    return targetFitness
    

# -------------------------------------------------------------------------------
# Evolutionary optimization: Generation of first population candidates
# -------------------------------------------------------------------------------
def generator(random, args):
    # generate initial values for candidates
    return [random.uniform(l, u) for l, u in zip(args.get('lower_bound'), args.get('upper_bound'))]

# -------------------------------------------------------------------------------
# Evolutionary optimization: Mutation of candidates
# -------------------------------------------------------------------------------
@mutator
def mutate(random, candidate, args):
    # if mutation_strenght is < 1, mutation will move closer to candidate
    # if mutation_strenght is >1, mutation will move further away from candidate
    # not bound required. otherwise: bounder = args.get('_ec').bounder
    mutant = [i for i in candidate]
    exponent = args.get('mutation_strength', 0.65)
    for i, (c, lo, hi) in enumerate(zip(candidate, args.get('lower_bound'), args.get('upper_bound'))):
        if random.random() <= args.get('mutation_rate', 0.1):
            if random.random() < 0.5:
                new_value = c + (hi - c) * (1.0 - random.random() ** exponent)
            else:
                new_value = c - (c - lo) * (1.0 - random.random() ** exponent)
            mutant[i] = new_value
        
    return mutant


# -------------------------------------------------------------------------------
# Batch class
# -------------------------------------------------------------------------------
class Batch(object):

    def __init__(self, cfgFile='cfg.py', netParamsFile='netParams.py', params=None, groupedParams=None, initCfg={}, seed=None):
        self.batchLabel = 'batch_'+str(datetime.date.today())
        self.cfgFile = cfgFile
        self.initCfg = initCfg
        self.netParamsFile = netParamsFile
        self.saveFolder = './' + self.batchLabel
        self.method = 'grid'
        self.runCfg = {}
        self.evolCfg = {}
        self.params = []
        self.seed = seed
        if params:
            for k,v in params.iteritems():
                self.params.append({'label': k, 'values': v})
        if groupedParams:
            for p in self.params:
                if p['label'] in groupedParams: p['group'] = True
    

    def save(self, filename):
        import os
        from copy import deepcopy
        basename = os.path.basename(filename)
        folder = filename.split(basename)[0]
        ext = basename.split('.')[1]
        
        # make dir
        if not os.path.exists(folder):
            try:
                os.mkdir(folder)
            except OSError:
                print ' Could not create', folder

        odict = deepcopy(self.__dict__)
        dataSave = {'batch': tupleToStr(odict)} 
        if ext == 'json':
            import json
            #from json import encoder
            #encoder.FLOAT_REPR = lambda o: format(o, '.12g')
            print('Saving batch to %s ... ' % (filename))
            with open(filename, 'w') as fileObj:
                json.dump(dataSave, fileObj, indent=4, sort_keys=True)


    def setCfgNestedParam(self, paramLabel, paramVal):
        if isinstance(paramLabel, tuple):
            container = self.cfg
            for ip in range(len(paramLabel)-1):
                if isinstance(container, specs.SimConfig):
                    container = getattr(container, paramLabel[ip])
                else:
                    container = container[paramLabel[ip]]
            container[paramLabel[-1]] = paramVal
        else:
            setattr(self.cfg, paramLabel, paramVal) # set simConfig params


    def saveScripts(self):
        import os
        # create Folder to save simulation
        if not os.path.exists(self.saveFolder):
            try:
                os.mkdir(self.saveFolder)
            except OSError:
                print ' Could not create %s' %(self.saveFolder)
        
        # save Batch dict as json
        self.save(self.saveFolder+'/'+self.batchLabel+'_batch.json')
        
        # copy this batch script to folder, netParams and simConfig
        os.system('cp ' + self.netParamsFile + ' ' + self.saveFolder + '/_netParams.py')
        os.system('cp ' + os.path.realpath(__file__) + ' ' + self.saveFolder + '/_batchScript.py')
        
        # save initial seed
        with open(self.saveFolder + '/_seed.seed', 'w') as seed_file:
            if not self.seed: self.seed = int(time())
            seed_file.write(str(self.seed))
            
        # import cfg
        cfgModuleName = os.path.basename(self.cfgFile).split('.')[0]
        cfgModule = imp.load_source(cfgModuleName, self.cfgFile)
        
        if hasattr(cfgModule, 'cfg'):
            self.cfg = cfgModule.cfg
        else:
            self.cfg = cfgModule.simConfig
            
        self.cfg.checkErrors = False  # avoid error checking during batch


    def openFiles2SaveStats(self):
        stat_file_name = '%s/%s_stats.cvs' %(self.saveFolder, self.batchLabel)
        ind_file_name = '%s/%s_stats_indiv.cvs' %(self.saveFolder, self.batchLabel)
        
        return open(stat_file_name, 'w'), open(ind_file_name, 'w')

    
    def createLogger(self):
        # Logger for evolutionary optimization
        logger = logging.getLogger('inspyred.ec')
        logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(self.saveFolder+'/inspyred.log', mode='w')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger


    def run(self):
        import os
        # create main sim directory and save scripts
        self.saveScripts()

        # -------------------------------------------------------------------------------
        # Evolutionary optimization
        # -------------------------------------------------------------------------------
        if self.method in ['grid','list']:
            import glob
            # set initial cfg initCfg
            if len(self.initCfg) > 0:
                for paramLabel, paramVal in self.initCfg.iteritems():
                    self.setCfgNestedParam(self.cfg, paramLabel, paramVal)
              

            # iterate over all param combinations
            if self.method == 'grid':
                groupedParams = False
                ungroupedParams = False
                for p in self.params:
                    if 'group' not in p: 
                        p['group'] = False
                        ungroupedParams = True
                    elif p['group'] == True: 
                        groupedParams = True

                if ungroupedParams:
                    labelList, valuesList = zip(*[(p['label'], p['values']) for p in self.params if p['group'] == False])
                else:
                    labelList = ()
                    valuesList = ()

                labelList, valuesList = zip(*[(p['label'], p['values']) for p in self.params if p['group'] == False])
                valueCombinations = list(product(*(valuesList)))
                indexCombinations = list(product(*[range(len(x)) for x in valuesList]))

                if groupedParams:
                    labelListGroup, valuesListGroup = zip(*[(p['label'], p['values']) for p in self.params if p['group'] == True])
                    valueCombGroups = izip(*(valuesListGroup))
                    indexCombGroups = izip(*[range(len(x)) for x in valuesListGroup])
                    labelList = labelListGroup+labelList
                else:
                    valueCombGroups = [(0,)] # this is a hack -- improve!
                    indexCombGroups = [(0,)]

            # if using pc bulletin board, initialize all workers
            if self.runCfg.get('type', None) == 'mpi_bulletin':
                for iworker in range(int(pc.nhost())):
                    pc.runworker()

            #if 1:
                #for iComb, pComb in zip(indexCombinations, valueCombinations):

            for iCombG, pCombG in zip(indexCombGroups, valueCombGroups):
                for iCombNG, pCombNG in zip(indexCombinations, valueCombinations):
                    if groupedParams: # temporary hack - improve
                        iComb = iCombG+iCombNG
                        pComb = pCombG+pCombNG

                    else:
                        iComb = iCombNG
                        pComb = pCombNG
                    
                    print iComb, pComb

                    for i, paramVal in enumerate(pComb):
                        paramLabel = labelList[i]
                        self.setCfgNestedParam(self.cfg, paramLabel, paramVal)

                        print str(paramLabel)+' = '+str(paramVal)
                        
                    # set simLabel and jobName
                    simLabel = self.batchLabel+''.join([''.join('_'+str(i)) for i in iComb])
                    jobName = self.saveFolder+'/'+simLabel  

                    # skip if output file already exists
                    if self.runCfg.get('skip', False) and glob.glob(jobName+'.json'):
                        print 'Skipping job %s since output file already exists...' % (jobName)
                    elif self.runCfg.get('skipCfg', False) and glob.glob(jobName+'_cfg.json'):
                        print 'Skipping job %s since cfg file already exists...' % (jobName)
                    elif self.runCfg.get('skipCustom', None) and glob.glob(jobName+self.runCfg['skipCustom']):
                        print 'Skipping job %s since %s file already exists...' % (jobName, self.runCfg['skipCustom'])
                    else:
                        # save simConfig json to saveFolder
                        self.cfg.simLabel = simLabel
                        self.cfg.saveFolder = self.saveFolder
                        cfgSavePath = self.saveFolder+'/'+simLabel+'_cfg.json'
                        self.cfg.save(cfgSavePath)
                        
                        # hpc torque job submission
                        if self.runCfg.get('type',None) == 'hpc_torque':

                            # read params or set defaults
                            sleepInterval = self.runCfg.get('sleepInterval', 1)
                            sleep(sleepInterval)
                            
                            nodes = self.runCfg.get('nodes', 1)
                            ppn = self.runCfg.get('ppn', 1)
                            script = self.runCfg.get('script', 'init.py')
                            mpiCommand = self.runCfg.get('mpiCommand', 'mpiexec')
                            walltime = self.runCfg.get('walltime', '00:30:00')
                            queueName = self.runCfg.get('queueName', 'default')
                            nodesppn = 'nodes=%d:ppn=%d'%(nodes,ppn)
                            custom = self.runCfg.get('custom', '')
                            numproc = nodes*ppn
                            
                            command = '%s -np %d nrniv -python -mpi %s simConfig=%s netParams=%s' % (mpiCommand, numproc, script, cfgSavePath, netParamsSavePath)  
                            # import job template from netpyne.utils.bashTemplate
                            jobString = bashTemplate('hpc_torque') % (jobName, walltime, queueName, nodesppn, jobName, jobName, custom, command)

                           # Send job_string to qsub
                            print 'Submitting job ',jobName
                            print jobString+'\n'

                            batchfile = '%s.pbs'%(jobName)
                            with open(batchfile, 'w') as text_file:
                                text_file.write("%s" % jobString)

                            proc = Popen(['qsub', batchfile], stderr=PIPE, stdout=PIPE)  # Open a pipe to the qsub command.
                            (output, input) = (proc.stdin, proc.stdout)


                        # hpc torque job submission
                        elif self.runCfg.get('type',None) == 'hpc_slurm':

                            # read params or set defaults
                            sleepInterval = self.runCfg.get('sleepInterval', 1)
                            sleep(sleepInterval)
                            
                            allocation = self.runCfg.get('allocation', 'csd403') # NSG account
                            nodes = self.runCfg.get('nodes', 1)
                            coresPerNode = self.runCfg.get('coresPerNode', 1)
                            email = self.runCfg.get('email', 'a@b.c')
                            folder = self.runCfg.get('folder', '.')
                            script = self.runCfg.get('script', 'init.py')
                            mpiCommand = self.runCfg.get('mpiCommand', 'ibrun')
                            walltime = self.runCfg.get('walltime', '00:30:00')
                            reservation = self.runCfg.get('reservation', None)
                            custom = self.runCfg.get('custom', '')
                            if reservation:
                                res = '#SBATCH --res=%s'%(reservation)
                            else:  
                                res = ''

                            numproc = nodes*coresPerNode
                            command = '%s -np %d nrniv -python -mpi %s simConfig=%s netParams=%s' % (mpiCommand, numproc, script, cfgSavePath, netParamsSavePath) 
                            # import job template from netpyne.utils.bashTemplate
                            jobString = bashTemplate('hpc_slurm') % (simLabel, allocation, walltime, nodes, coresPerNode, jobName, jobName, email, res, custom, folder, command)

                            # Send job_string to qsub
                            print 'Submitting job ',jobName
                            print jobString+'\n'

                            batchfile = '%s.sbatch'%(jobName)
                            with open(batchfile, 'w') as text_file:
                                text_file.write("%s" % jobString)

                            #subprocess.call
                            proc = Popen(['sbatch',batchfile], stdin=PIPE, stdout=PIPE)  # Open a pipe to the qsub command.
                            (output, input) = (proc.stdin, proc.stdout)


                        # run mpi jobs directly e.g. if have 16 cores, can run 4 jobs * 4 cores in parallel
                        # eg. usage: python batch.py
                        elif self.runCfg.get('type',None) == 'mpi_direct':
                            jobName = self.saveFolder+'/'+simLabel     
                            print 'Running job ',jobName
                            cores = self.runCfg.get('cores', 1)
                            folder = self.runCfg.get('folder', '.')
                            script = self.runCfg.get('script', 'init.py')
                            mpiCommand = self.runCfg.get('mpiCommand', 'ibrun')

                            command = '%s -np %d nrniv -python -mpi %s simConfig=%s netParams=%s' % (mpiCommand, cores, script, cfgSavePath, netParamsSavePath) 
                            
                            print command + '\n'
                            proc = Popen(command.split(' '), stdout=open(jobName+'.run','w'),  stderr=open(jobName+'.err','w'))
                            #print proc.stdout.read()
                            
                            
                        # pc bulletin board job submission (master/slave) via mpi
                        # eg. usage: mpiexec -n 4 nrniv -mpi batch.py
                        elif self.runCfg.get('type',None) == 'mpi_bulletin':
                            jobName = self.saveFolder+'/'+simLabel     
                            print 'Submitting job ',jobName
                            # master/slave bulletin board schedulling of jobs
                            pc.submit(runJob, self.runCfg.get('script', 'init.py'), cfgSavePath, netParamsSavePath)
                
                    sleep(1) # avoid saturating scheduler

            # wait for pc bulletin board jobs to finish
            try:
                while pc.working():
                    sleep(1)
                #pc.done()
            except:
                pass

            sleep(10) # give time for last job to get on queue    


        # -------------------------------------------------------------------------------
        # Evolutionary optimization
        # -------------------------------------------------------------------------------
        elif self.method=='evol':
            global ngen
            ngen = -1
            
            # log for simulation
            logger = self.createLogger()
            
            # create randomizer instance
            rand = Random()
            rand.seed(self.seed) 
            
            # create Inspyred.evolutionary_computation instance
            ea = EvolutionaryComputation(rand)
            # selects all elements in population
            ea.selector = default_selection
            # applied one after another in pipeline fashion
            ea.variator = [uniform_crossover, mutate]
            # replace all parents except for elit_num if fitness is bigger
            ea.replacer = generational_replacement
            # all elements will be called in secuence
            ea.observer = [stats_observer, file_observer]
            # create file handlers for observers
            stats_file, ind_stats_file = self.openFiles2SaveStats()
            # all elements will be combined via logical "or" operation
            ea.terminator = [generation_termination]
            
            # gather **kwargs
            kwargs = {'cfg': self.cfg}
            kwargs['statistics_file'] = stats_file
            kwargs['individuals_file'] = ind_stats_file
            kwargs['cfgSavePath'] = self.cfgFile
            kwargs['simDataFolder'] = self.saveFolder
            kwargs['netParamsSavePath'] = self.netParamsFile
            kwargs['setCfgNestedParam'] = self.setCfgNestedParam
            
            for key, value in self.evolCfg.iteritems(): 
                kwargs[key] = value
            for key, value in self.runCfg.iteritems(): 
                kwargs[key] = value
            
            # evolve
            final_pop = ea.evolve( generator=generator, evaluator=evaluator, 
                                bounder=Bounder, **kwargs)
            # close file
            stats_file.close()
            ind_stats_file.close()
            # print best and finish
            print('Best Solution: \n{0}'.format(str(max(final_pop))))
            print "JOB FINISHED"
