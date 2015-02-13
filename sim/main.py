
from neuron import h, init # Import NEURON
from params import *
import network
import sys

for argv in sys.argv[1:]: # Skip first argument, which is file name
  arg = argv.replace(' ','').split('=') # ignore spaces and find varname and value
  harg = arg[0].split('.')+[''] # Separate out variable name; '' since if split fails need to still have an harg[1]
  if len(arg)==2:
    if hasattr(p,arg[0]) or hasattr(h,harg[1]): # Check that variable exists
      exec('p.'+argv) # Actually set variable            
      if p.nhost==0: # messages only come from Master
        print('  Setting %s=%r' %(arg[0],eval(arg[0])))
    else: 
      sys.tracebacklimit=0
      raise Exception('Reading args from commandline: Variable "%s" not found' % arg[0])
  elif argv=='-mpi':   ismpi = True
  else:                pass # ignore -python 

network.createNetwork()

# if pc.id()==0: 
#     pc.gid_clear()
#     print('\nSetting parameters...')


# ###############################################################################
# ### HOUSEKEEPING
# ###############################################################################

# ## Check for input arguments
# for arg in argv[1:]: # Skip first argument, which is file name
#     varname = arg.split('=') # Separate out variable name
#     if len(varname)==2: # Make sure it split properly, but if not, assume it's something else (e.g. a NEURON argument) and fail silently
#         if varname[0] in locals(): # Check that variable exists
#             exec(arg) # Actually set variable            
#             if pc.id()==0: print('  Setting %s' % arg)
#         else: raise Exception('Variable "%s" not found' % varname[0])

# ## Limit memory
# if limitmemory:
#     import resource, os
#     freemem = 0.95*float(os.popen("free -b").readlines()[1].split()[3]) # Get free memory, set maximum to 75%
#     resource.setrlimit(resource.RLIMIT_AS, (freemem, freemem)) # Limit memory usage
#     if pc.id()==0: print('  Note: RAM limited to %0.2f GB' % (freemem/1e9))
    
# ## Peform a mini-benchmarking test for future time estimates
# if pc.id()==0:
#     print('Benchmarking...')
#     benchstart = time()
#     for i in range(int(1.36e6)): tmp=0 # Number selected to take 0.1 s on my machine
#     performance = 1/(10*(time() - benchstart))*100
#     print('  Running at %0.0f%% default speed (%0.0f%% total)' % (performance, performance*nhosts))
 


# ## Wrapping up
# totaltime = time()-verystart # See how long it took in total
# print('\nDone; total time = %0.1f s.' % totaltime)
# if (plotraster==False and plotconn==False): h.quit() # Quit extra processes, or everything if plotting wasn't requested (since assume non-interactive)

