#!/usr/bin/env python
import os
from StopsDilepton.samples.cmgTuples_FastSimT2tt_mAODv2_25ns_postProcessed import signals_T2tt
from StopsDilepton.samples.cmgTuples_FastSimT2bX_mAODv2_25ns_postProcessed import signals_T2bt, signals_T2bW

from StopsDilepton.samples.cmgTuples_FastSimT8bbllnunu_mAODv2_25ns_postProcessed import signals_T8bbllnunu_XCha0p5_XSlep0p05, signals_T8bbllnunu_XCha0p5_XSlep0p09, signals_T8bbllnunu_XCha0p5_XSlep0p5, signals_T8bbllnunu_XCha0p5_XSlep0p95
from StopsDilepton.samples.cmgTuples_FullSimTTbarDM_mAODv2_25ns_postProcessed import signals_TTbarDM

#signalEstimators = [s.name for s in signals_T8bbllnunu_XCha0p5_XSlep0p05]
#signalEstimators = [s.name for s in signals_T8bbllnunu_XCha0p5_XSlep0p09]
#signalEstimators = [s.name for s in signals_T8bbllnunu_XCha0p5_XSlep0p5]
#signalEstimators = [s.name for s in signals_T8bbllnunu_XCha0p5_XSlep0p95]
#signalEstimators = [s.name for s in signals_T2tt]
#signalEstimators = [s.name for s in signals_T2bt]
#signalEstimators = [s.name for s in signals_T2bW]
signalEstimators = [s.name for s in signals_TTbarDM]

import time

cmd = "submitBatch.py --title='LimitDM'"
#cmd = "echo"

for i, estimator in enumerate(signalEstimators):
#for i in range(480,493):
  #logfile    = "log/limit_" + estimator + ".log"
  #logfileErr = "log/limit_" + estimator + "_err.log"
  #os.system(cmd +" 'python run_limit.py --signal T2tt --fitAll              --only=%s'"%(str(i)))
  #if i%20==0: print
  #if "650_25" in estimator: print "HERE!!"
  #print i, estimator
  #st = estimator.split("_")
  #if int(st[-2]) < 650:
  os.system(cmd+" 'python run_limit.py --signal TTbarDM --fitAll            --only=%s'"%str(i))
#  os.system(cmd+" 'python run_limit.py --signal T2tt --fitAll            --only=%s'"%str(i))
#  os.system(cmd+" 'python run_limit.py --signal T8bbllnunu_XCha0p5_XSlep0p5--controlDYVV --only=%s'"%str(i))
#  os.system(cmd+" 'python run_limit.py --signal T8bbllnunu_XCha0p5_XSlep0p5--controlTTZ  --only=%s'"%str(i))
#  os.system(cmd+" 'python run_limit.py --signal T8bbllnunu_XCha0p5_XSlep0p5--fitAll      --only=%s'"%str(i))
#  time.sleep(1)

