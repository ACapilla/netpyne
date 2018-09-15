"""
sim/load.py

Functions related to loading

Contributors: salvadordura@gmail.com
"""

import sys
from collections import OrderedDict
from ..specs import Dict, ODict
from .. import specs
from . import utils
from . import setup

#------------------------------------------------------------------------------
# Load data from file
#------------------------------------------------------------------------------
def _loadFile (filename):
    from .. import sim
    import os

    def _byteify(data, ignore_dicts = False):
        # if this is a unicode string, return its string representation
        if isinstance(data, unicode):
            return data.encode('utf-8')
        # if this is a list of values, return list of byteified values
        if isinstance(data, list):
            return [ _byteify(item, ignore_dicts=True) for item in data ]
        # if this is a dictionary, return dictionary of byteified keys and values
        # but only if we haven't already byteified it
        if isinstance(data, dict) and not ignore_dicts:
            return OrderedDict({
                _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
                for key, value in data.iteritems()
            })
        # if it's anything else, return it in its original form
        return data

    if hasattr(sim, 'cfg') and sim.cfg.timing: sim.timing('start', 'loadFileTime')
    ext = os.path.basename(filename).split('.')[1]

    # load pickle file
    if ext == 'pkl':
        import pickle
        print('Loading file %s ... ' % (filename))
        with open(filename, 'rb') as fileObj:
            if sys.version_info[0] == 2:
                data = pickle.load(fileObj)
            else:
                data = pickle.load(fileObj, encoding='latin1')

    # load dpk file
    elif ext == 'dpk':
        import gzip
        print('Loading file %s ... ' % (filename))
        #fn=sim.cfg.filename #.split('.')
        #gzip.open(fn, 'wb').write(pk.dumps(dataSave)) # write compressed string
        print('NOT IMPLEMENTED!')

    # load json file
    elif ext == 'json':
        import json
        print('Loading file %s ... ' % (filename))
        with open(filename, 'r') as fileObj:
            data = json.load(fileObj, object_hook=_byteify)

    # load mat file
    elif ext == 'mat':
        from scipy.io import loadmat
        print('Loading file %s ... ' % (filename))
        dataraw = loadmat(filename, struct_as_record=False, squeeze_me=True)
        data = utils._mat2dict(dataraw)
        #savemat(sim.cfg.filename+'.mat', replaceNoneObj(dataSave))  # replace None and {} with [] so can save in .mat format
        print('Finished saving!')

    # load HDF5 file (uses very inefficient hdf5storage module which supports dicts)
    elif ext == 'saveHDF5':
        #dataSaveUTF8 = _dict2utf8(replaceNoneObj(dataSave)) # replace None and {} with [], and convert to utf
        import hdf5storage
        print('Loading file %s ... ' % (filename))
        #hdf5storage.writes(dataSaveUTF8, filename=sim.cfg.filename+'.hdf5')
        print('NOT IMPLEMENTED!')

    # load CSV file (currently only saves spikes)
    elif ext == 'csv':
        import csv
        print('Loading file %s ... ' % (filename))
        writer = csv.writer(open(sim.cfg.filename+'.csv', 'wb'))
        #for dic in dataSave['simData']:
        #    for values in dic:
        #        writer.writerow(values)
        print('NOT IMPLEMENTED!')

    # load Dat file(s)
    elif ext == 'dat':
        print('Loading file %s ... ' % (filename))
        print('NOT IMPLEMENTED!')
        # traces = sim.cfg.recordTraces
        # for ref in traces.keys():
        #     for cellid in sim.allSimData[ref].keys():
        #         dat_file_name = '%s_%s.dat'%(ref,cellid)
        #         dat_file = open(dat_file_name, 'w')
        #         trace = sim.allSimData[ref][cellid]
        #         print("Saving %i points of data on: %s:%s to %s"%(len(trace),ref,cellid,dat_file_name))
        #         for i in range(len(trace)):
        #             dat_file.write('%s\t%s\n'%((i*sim.cfg.dt/1000),trace[i]/1000))

    else:
        print('Format not recognized for file %s'%(filename))
        return

    if hasattr(sim, 'rank') and sim.rank == 0 and hasattr(sim, 'cfg') and sim.cfg.timing:
        sim.timing('stop', 'loadFileTime')
        print('  Done; file loading time = %0.2f s' % sim.timingData['loadFileTime'])


    return data


#------------------------------------------------------------------------------
# Load simulation config from file
#------------------------------------------------------------------------------
def loadSimCfg (filename, data=None, setLoaded=True):
    if not data: data = _loadFile(filename)
    print('Loading simConfig...')
    if 'simConfig' in data:
        if setLoaded:
            setup.setSimCfg(data['simConfig'])
        else:
            return specs.SimConfig(data['simConfig'])
    else:
        print('  simConfig not found in file %s'%(filename))
    pass


#------------------------------------------------------------------------------
# Load netParams from cell
#------------------------------------------------------------------------------
def loadNetParams (filename, data=None, setLoaded=True):
    if not data: data = _loadFile(filename)
    print('Loading netParams...')
    if 'net' in data and 'params' in data['net']:
        if setLoaded:
            setup.setNetParams(data['net']['params'])
        else:
            return specs.NetParams(data['net']['params'])
    else:
        print('netParams not found in file %s'%(filename))

    pass


#------------------------------------------------------------------------------
# Load cells and pops from file and create NEURON objs
#------------------------------------------------------------------------------
def loadNet (filename, data=None, instantiate=True, compactConnFormat=False):
    from .. import sim

    if not data: data = _loadFile(filename)
    if 'net' in data and 'cells' in data['net'] and 'pops' in data['net']:
        if sim.rank == 0:
            sim.timing('start', 'loadNetTime')
            print('Loading net...')
            if compactConnFormat: 
                compactToLongConnFormat(data['net']['cells'], compactConnFormat) # convert loaded data to long format 
            sim.net.allPops = data['net']['pops']
            sim.net.allCells = data['net']['cells']
        if instantiate:
            # calculate cells to instantiate in this node
            if isinstance(instantiate, list):
                cellsNode = [data['net']['cells'][i] for i in xrange(int(sim.rank), len(data['net']['cells']), sim.nhosts) if i in instantiate]
            else:
                cellsNode = [data['net']['cells'][i] for i in xrange(int(sim.rank), len(data['net']['cells']), sim.nhosts)]
            if sim.cfg.createPyStruct:
                for popLoadLabel, popLoad in data['net']['pops'].iteritems():
                    pop = sim.Pop(popLoadLabel, popLoad['tags'])
                    pop.cellGids = popLoad['cellGids']
                    sim.net.pops[popLoadLabel] = pop
                for cellLoad in cellsNode:
                    # create new CompartCell object and add attributes, but don't create sections or associate gid yet
                    # TO DO: assumes CompartCell -- add condition to load PointCell
                    cell = sim.CompartCell(gid=cellLoad['gid'], tags=cellLoad['tags'], create=False, associateGid=False)
                    try:
                        if sim.cfg.saveCellSecs:
                            cell.secs = Dict(cellLoad['secs'])
                        else:
                            createNEURONObjorig = sim.cfg.createNEURONObj
                            sim.cfg.createNEURONObj = False  # avoid creating NEURON Objs now; just needpy struct
                            cell.create()
                            sim.cfg.createNEURONObj = createNEURONObjorig
                    except:
                        if sim.cfg.verbose: print(' Unable to load cell secs')

                    try:
                        cell.conns = [Dict(conn) for conn in cellLoad['conns']]
                    except:
                        if sim.cfg.verbose: print(' Unable to load cell conns')

                    try:
                        cell.stims = [Dict(stim) for stim in cellLoad['stims']]
                    except:
                        if sim.cfg.verbose: print(' Unable to load cell stims')

                    sim.net.cells.append(cell)
                print('  Created %d cells' % (len(sim.net.cells)))
                print('  Created %d connections' % (sum([len(c.conns) for c in sim.net.cells])))
                print('  Created %d stims' % (sum([len(c.stims) for c in sim.net.cells])))

                # only create NEURON objs, if there is Python struc (fix so minimal Python struct is created)
                if sim.cfg.createNEURONObj:
                    if sim.cfg.verbose: print("  Adding NEURON objects...")
                    # create NEURON sections, mechs, syns, etc; and associate gid
                    for cell in sim.net.cells:
                        prop = {'secs': cell.secs}
                        cell.createNEURONObj(prop)  # use same syntax as when creating based on high-level specs
                        cell.associateGid()  # can only associate once the hSection obj has been created
                    # create all NEURON Netcons, NetStims, etc
                    sim.pc.barrier()
                    for cell in sim.net.cells:
                        try:
                            cell.addStimsNEURONObj()  # add stims first so can then create conns between netstims
                            cell.addConnsNEURONObj()
                        except:
                            if sim.cfg.verbose: ' Unable to load instantiate cell conns or stims'

                    print('  Added NEURON objects to %d cells' % (len(sim.net.cells)))

            if sim.rank == 0 and sim.cfg.timing:
                sim.timing('stop', 'loadNetTime')
                print('  Done; re-instantiate net time = %0.2f s' % sim.timingData['loadNetTime'])
    else:
        print('  netCells and/or netPops not found in file %s'%(filename))


#------------------------------------------------------------------------------
# Load netParams from cell
#------------------------------------------------------------------------------
def loadSimData (filename, data=None):
    from .. import sim

    if not data: data = _loadFile(filename)
    print('Loading simData...')
    if 'simData' in data:
        sim.allSimData = data['simData']
    else:
        print('  simData not found in file %s'%(filename))

    pass


#------------------------------------------------------------------------------
# Load all data in file
#------------------------------------------------------------------------------
def loadAll (filename, data=None, instantiate=True, createNEURONObj=True):
    from .. import sim 

    if not data: data = _loadFile(filename)
    loadSimCfg(filename, data=data)
    sim.cfg.createNEURONObj = createNEURONObj  # set based on argument
    loadNetParams(filename, data=data)
    if hasattr(sim.cfg, 'compactConnFormat'): 
        connFormat = sim.cfg.compactConnFormat
    else:
        print 'Error: no connFormat provided in simConfig'
        sys.exit()
    loadNet(filename, data=data, instantiate=instantiate, compactConnFormat=connFormat)
    loadSimData(filename, data=data)


#------------------------------------------------------------------------------
# Convert compact (list-based) to long (dict-based) conn format
#------------------------------------------------------------------------------
def compactToLongConnFormat(cells, connFormat):
    
    formatIndices = {key: connFormat.index(key) for key in connFormat}
    try:
        for cell in cells:
            for iconn, conn in enumerate(cell['conns']):
                cell['conns'][iconn] = {key: conn[index] for key,index in formatIndices.iteritems()}
        return cells
    except:
        print("Error converting conns from compact to long format")
        return cells