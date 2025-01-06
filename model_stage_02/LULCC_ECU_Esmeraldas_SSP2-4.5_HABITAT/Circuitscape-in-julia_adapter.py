# LPB-RAP - PHC module: Circuitscape in Julia adapter
# Author Sonja Holler
# Date 2024/01/27+

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
# required variables:
Circuitscape_time_step_configuration_ini = sys.argv[1]
print('Circuitscape_time_step_configuration_ini used:', Circuitscape_time_step_configuration_ini)
# =============================================================================


# =============================================================================
# Julia command
# =============================================================================
print('adding Circuitscape package in Julia')
jl.using("Pkg")
Pkg.add("Circuitscape")
#Pkg.test("Circuitscape")


# =============================================================================
# CALCULATE TIME STEP INI FILE in Circuitscape for Julia
# =============================================================================
print('Calculating PHC for time step landscape in Circuitscape for Julia')
start = time.time()
jl.using("Circuitscape")
Main.compute(Circuitscape_time_step_configuration_ini)
end = time.time()
module_end = time.time()
# calculation time for one time step landscape
print('Computation time total in minutes:')
print('Circuitscape:', (end - start)/60)
print('Module:', (module_end - module_start)/60)
