"""
init.py

Initial script to import, simulate and plot raster of SONATA example 300_cells


Contributors: salvadordura@gmail.com
"""

from netpyne import sim
from netpyne.conversion import sonataImport
import h5py
import json
import numpy as np
from matplotlib import pyplot as plt


rootFolder = '/u/salvadord/Documents/ISB/Models/sonata/examples/300_cells/'
outFolder = '/u/salvadord/Documents/ISB/Models/netpyne_repo/examples/sonata_300_cells/'
sonataConfigFile = rootFolder+'config.json'

# Options
importSonataModel = 1
saveForGUI = 0
saveJsonPsection = 1
saveJsonConns = 0
runPlot = 0
compare = 0

# Improt SONATA model and instantiate in netpyne
if importSonataModel:
    sonataImporter = sonataImport.SONATAImporter()
    sonataImporter.importNet(sonataConfigFile, replaceAxon=True, setdLNseg=True)


# code to save network to json so can read from NetPyNE-UI
if saveForGUI:
    sim.cfg.saveJson = True
    #for k,v in sim.net.params.popParams.items():
    #    v['numCells'] = 20
    sim.cfg.saveDataInclude = ['netParams', 'net'] # 'simConfig', 
    newCells = [c for c in sim.net.cells if c.gid not in sim.net.pops['external_virtual_100'].cellGids]  # if c.gid == 1
    sim.net.cells = newCells
    del sim.net.pops['external_virtual_100']
    # remove axon
    for k in sim.net.params.cellParams:
        try:
            del sim.net.params.cellParams[k]['secs']['axon_0']
            del sim.net.params.cellParams[k]['secs']['axon_1']
            for c in sim.net.cells:
                del c.secs['axon_0']
                del c.secs['axon_1']
        except:
            pass
    # remove conns
    for c in sim.net.cells:
        c.conns = []
    # save
    sim.saveData(filename='sonata_300cells')


# save json with psection
if saveJsonPsection:
    import json
    data = {}
    remove = ['cell', 'regions','species', 'point_processes', 'hoc_internal_name', 'name', 'morphology']
    removeMorph = ['parent', 'trueparent']
    for icell, c in enumerate(sim.net.cells):
        try:
            data[icell] = {}
            for isec, sec in enumerate(c.secs.values()):
                name = str(sec['hObj'].name()).split('.')[-1]
                data[icell][name] = sec['hObj'].psection()
                for x in remove:
                    del data[icell][name][x]
                # for key in removeMorph:
                #     if key in data[icell][name]['morphology']:
                #         del data[icell][name]['morphology'][key]
                        # data[icell][name]['morphology'][key] = str(data[icell][name]['morphology'][key])
        except:
            print('Error processing %d'%(icell))

    with open('300cells_secs_netpyne.json', 'w') as f:
        json.dump(data, f)


# save json with psection
if saveJsonConns:
    import json
    data = {}
    data_wrong = []
    
    from neuron import h
    conns = list(h.List('NetCon'))
    
    for conn in conns:
        try:
            preGid = conn.precell().gid
            postGid = conn.postcell().gid
            sec_loc = str(conn.postseg()).split('>.')[1]
            sec = sec_loc.split('(')[0]
            loc = sec_loc.split('(')[1][:-1]
            weight = conn.weight[0]
            delay = conn.delay
            synTau1 = conn.syn().tau1
            synTau2 = conn.syn().tau2

            data['%s_%s_%s_%s' % (str(preGid), str(postGid), sec, str(loc))] = [weight, delay, synTau1, synTau2]
        except:
            data_wrong.append([str(conn.precell()), str(conn.postseg())])

    with open('300cells_conns_netpyne.json', 'w') as f:
        json.dump(data, f)


# run simulation and plot raster+traces
if runPlot:
    sim.cfg.recordTraces = {'V_soma':{'sec':'soma_0','loc':0.5,'var':'v'}}
    sim.cfg.recordCells = range(9)
    sim.cfg.analysis['plotTraces'] = {}  # needed for 9 cell example
    sim.cfg.cache_efficient = True
    sim.setupRecording()
    sim.simulate()
    includePops = [p for p in sim.net.pops if p not in ['external_virtual_100']]
    fig = sim.analysis.plotRaster(include=includePops, spikeHist='subplot', spikeHistBin=10, figSize=(14,8), dpi=300, saveFig='model_output_raster_axonv2_dl_300cells.png', marker='.', markerSize=3)
    #fig = sim.analysis.plotTraces(figSize=(10,14), oneFigPer='trace', include=range(10), saveFig='model_output_traces_axonv2_dl_300cells.png')


# Compare with SONATA data
if compare:
    # store netpyne traces
    netpyneTraces = []
    netpyneTracesList = []
    for c in sim.cfg.recordCells:
        netpyneTraces.append(np.array(sim.simData['V_soma']['cell_' + str(c)]))
        netpyneTracesList.append(list(sim.simData['V_soma']['cell_' + str(c)]))

    with open(outFolder+'netpyne_traces_300cells.json', 'w') as f:
        json.dump(netpyneTracesList, f)


    # load traces from bmtk HDF5
    dataFile=rootFolder+'output/membrane_potential.h5'
    h5data = h5py.File(dataFile, 'r')
    bmtkTraces = np.array(h5data['data'])  # shape (30000, 9)


    # store netpyne spikes
    netpyneSpkt = np.array(sim.simData.spkt)
    netpyneSpkid = np.array(sim.simData.spkid)


    # load spiks from bmtk HDF5
    dataFile=rootFolder+'output/spikes.h5'
    h5data = h5py.File(dataFile, 'r')
    bmtkSpkt = np.array(h5data['spikes']['timestamps']) 
    bmtkSpkid = np.array(h5data['spikes']['gids']) 


    # plot both traces overlayed
    recordStep = sim.cfg.recordStep
    timeRange = [0, sim.cfg.duration]
    fontsiz=8
    ylim = [-100, 40]
    figSize = (10,10)
    fig = plt.figure(figsize=figSize)  # Open a new figure

    for gid in sim.cfg.recordCells:
        netpyneTrace = netpyneTraces[gid][int(timeRange[0] / recordStep):int(timeRange[1] / recordStep)]
        bmtkTrace = bmtkTraces[:,gid][int(timeRange[0]/recordStep):int(timeRange[1]/recordStep)]
        t = np.arange(timeRange[0], timeRange[1]+recordStep, recordStep)
        plt.subplot(len(sim.cfg.recordCells), 1, gid+1)
        plt.ylabel('V (mV)', fontsize=fontsiz)
        plt.plot(t[:len(netpyneTrace)], netpyneTrace, linewidth=1.5, color='red', label='Gid %d'%(int(gid))+', NetPyNE')
        plt.plot(t[:len(bmtkTrace)], bmtkTrace, linewidth=1.0, color='green', label='Gid %d'%(int(gid))+', BioNet')  # linestyle=':'
        plt.xlabel('Time (ms)', fontsize=fontsiz)
        plt.xlim(timeRange)
        plt.ylim(ylim)
        plt.grid(True)
        plt.legend(loc='upper right', bbox_to_anchor=(1.25, 1.0))
    plt.ion()
    plt.tight_layout()
    plt.savefig(outFolder+'comparison_traces_270-280.png')
    plt.show()


    # plot both spike times overlayed
    recordStep = sim.cfg.recordStep
    timeRange = [0, sim.cfg.duration]
    fontsiz=8
    ylim = [0,299]
    figSize = (10,6)
    fig = plt.figure(figsize=figSize)  # Open a new figure

    plt.ylabel('Gid', fontsize=fontsiz)
    plt.scatter(netpyneSpkt, netpyneSpkid, s=1.5, color='red', label='NetPyNE')
    plt.scatter(bmtkSpkt, bmtkSpkid, s=0.5, color='green', label='BioNet')  # linestyle=':'
    plt.xlabel('Time (ms)', fontsize=fontsiz)
    plt.xlim(timeRange)
    plt.legend(loc='upper right', bbox_to_anchor=(1.25, 1.0))
    plt.ylim(ylim)
    plt.ion()
    plt.tight_layout()
    plt.savefig(outFolder+'comparison_raster.png', dpi=300)
    plt.show()