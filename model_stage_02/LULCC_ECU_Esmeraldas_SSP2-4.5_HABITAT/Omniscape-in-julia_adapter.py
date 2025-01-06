# LPB-RAP - PHC module: Omniscape in Julia adapter
# Author Sonja Holler
# Date 2024/02/01+

# =============================================================================
# Import
# =============================================================================
import os, sys
import time
# track time for module execution
module_start = time.time()

from julia.api import Julia
jl = Julia(compiled_modules=False)
from julia import Base
from julia import Main
from julia import Pkg

# =============================================================================
# Julia command
# =============================================================================
print('adding Omniscape package in Julia')
jl.using("Pkg")
Pkg.add("Omniscape")

# =============================================================================
# required variables: OMNISCAPE TIME STEP INI
Omniscape_time_step_configuration_ini = sys.argv[1]
print('Omniscape_time_step_configuration_ini used:', Omniscape_time_step_configuration_ini)
# =============================================================================


# =============================================================================
# CALCULATE TIME STEP INI FILE in Circuitscape for Julia
# =============================================================================
print('Calculating habitat connecticity for time step landscape in Omniscape for Julia:')
start = time.time()
jl.using("Omniscape")
Main.run_omniscape(Omniscape_time_step_configuration_ini)
end = time.time()
module_end = time.time()
# calculation time for one time step landscape
print('Computation time total in minutes:')
print('Omniscape:', (end - start)/60)
print('Module:', (module_end - module_start)/60)

