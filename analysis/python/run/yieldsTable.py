#!/usr/bin/env python
import os
import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument("--onlyStat",       action='store_true', default=False,          help="show only stat errors?")
argParser.add_argument("--agg",            action='store_true', default=False,          help="use agg regions?")
args = argParser.parse_args()

from StopsDilepton.samples.cmgTuples_FastSimT2tt_mAODv2_25ns_postProcessed import T2tt_750_1, T2tt_600_300
from StopsDilepton.analysis.SetupHelpers    import allChannels, channels
from StopsDilepton.analysis.estimators      import setup, constructEstimatorList, MCBasedEstimate
from StopsDilepton.analysis.DataObservation import DataObservation
from StopsDilepton.analysis.SumEstimate     import SumEstimate
if args.agg: from StopsDilepton.analysis.regions import regionsAgg as regions
else:        from StopsDilepton.analysis.regions import regionsO   as regions
from StopsDilepton.analysis.Cache           import Cache


# Logging
import StopsDilepton.tools.logger as logger
logger = logger.get_logger("INFO", logFile = None )
import RootTools.core.logger as logger_rt
logger_rt = logger_rt.get_logger("INFO", logFile = None )

setup.verbose = False
signalSetup   = setup.sysClone(sys = {'reweight':['reweightLeptonFastSimSF']})


estimators       = constructEstimatorList(["TTJets-DD","TTZ","DY", 'multiBoson', 'other'])
summedEstimate   = SumEstimate(name="sum")
signalEstimators = [ MCBasedEstimate(name=s.name, sample={channel:s for channel in channels}) for s in [T2tt_750_1, T2tt_600_300]]

observation = DataObservation(name='Data', sample=setup.sample['Data'])

for e in estimators + [summedEstimate, observation] + signalEstimators:
    e.initCache(setup.defaultCacheDir())

from StopsDilepton.tools.u_float import u_float
from math import sqrt


texdir  = os.path.join(setup.analysis_results, setup.prefix(), 'tables')

try:    os.makedirs(texdir)
except: pass

allChannels = ["all","SF","EMu"]
for channel in allChannels:
  try:    os.makedirs(os.path.join(texdir, channel))
  except: pass

  yieldTexfile = os.path.join(texdir, channel, "yields_onlyStat.tex" if args.onlyStat else "yields" + ('_agg' if args.agg else '') + ".tex")
  print "Writing to " + yieldTexfile
  with open(yieldTexfile, "w") as yieldTable:
    yieldTable.write("\\begin{tabular}{c||" + "c|"*len(estimators) + "|c||c||c} \n")
    yieldTable.write("  signal region & " + "& ".join([e.getTexName(channel, rootTex=False) for e in estimators]) + "& expected & T2tt(700,1) & T2tt(600,300) & observed \\\\ \n")
    yieldTable.write("  \\hline \n")

    ttJetsErr = None
    ttzErr    = None
    dyErr     = None
                 
    for i, r in enumerate(regions[1:]):
      yieldTable.write(" $" + str(i) + "$ ")
      
      for e in estimators + [summedEstimate]:

        expected = int(100*e.cachedEstimate(r, channel, setup).val+0.5)/100.
        stat     = int(100*e.cachedEstimate(r, channel, setup).sigma+0.99)/100.

        if e.name.count('DY'): expected *= 1.31
        if e.name.count('DY'): stat     *= 1.31
        if e.name.count('multiboson'): expected *= 1.19
        if e.name.count('multiboson'): stat     *= 1.19

        if args.onlyStat: 
          yieldTable.write(" &&  %.2f &$\pm$& %.2f && " % (expected, stat))
        else:  # Still pre-fit uncertainties here
          if e.name.count("TTJets"):
            lowMt2ll = 1 if args.agg else 6
            unc1 = (0.25 if i < lowMt2ll else 0.55)*0.15
            unc2 = (0.50 if i < lowMt2ll else 0.44)*0.30
            unc3 = (0.25 if i < lowMt2ll else 0.01)*0.50
            unc  = sqrt(unc1**2+unc2**2+unc3**2)

            ttJetsErr     = expected*unc                       # these should be absolute errors, because we will propagate it also to the sum
          if e.name.count("TTZ"):        ttzErr        = expected*sqrt(0.2**2+0.15**2)
          if e.name.count("DY"):         dyErr         = expected*0.19
          if e.name.count("multiBoson"): multiBosonErr = expected*0.17
          if e.name.count("other"):      ttxErr        = expected*0.25

          errors   = [stat/expected if expected > 0 else 0]
          errors.append(e.PUSystematic(         r, channel, setup).val)
          errors.append(e.unclusteredSystematic(r, channel, setup).val)
          errors.append(e.leptonSFSystematic(   r, channel, setup).val)
          errors.append(e.triggerSystematic(    r, channel, setup).val)
          errors.append(e.JERSystematic(        r, channel, setup).val)
          errors.append(e.JECSystematic(        r, channel, setup).val)
          errors.append(e.topPtSystematic(      r, channel, setup).val)
          errors.append(e.btaggingSFbSystematic(r, channel, setup).val)
          errors.append(e.btaggingSFlSystematic(r, channel, setup).val)
          if e.name.count("sum") or e.name.count("TTJets"):     errors.append(ttJetsErr/expected     if expected > 0 else 0) # Now to relative errors in order to combine with other errors
          if e.name.count("sum") or e.name.count("TTZ"):        errors.append(ttzErr/expected        if expected > 0 else 0)
          if e.name.count("sum") or e.name.count("DY"):         errors.append(dyErr/expected         if expected > 0 else 0)
          if e.name.count("sum") or e.name.count("other"):      errors.append(ttxErr/expected        if expected > 0 else 0)
          if e.name.count("sum") or e.name.count("multiBoson"): errors.append(multiBosonErr/expected if expected > 0 else 0)

          totalError = sqrt(sum([err*err for err in errors]))
          yieldTable.write(" && %.2f &$\pm$& %.2f &&" % (expected, totalError*expected))              # And back to absolute error
 
      signal   = signalEstimators[0].cachedEstimate(r, channel, signalSetup).val
      signal2  = signalEstimators[1].cachedEstimate(r, channel, signalSetup).val
      observed = observation.cachedObservation(r, channel, setup).val
      yieldTable.write(" & %.2f " % signal)
      yieldTable.write(" & %.2f " % signal2)
      yieldTable.write(" & %d \\\\ \n" % observed)

    yieldTable.write("\\end{tabular} \n")
    yieldTable.write("\\caption{Yields and uncertainties for each background and their sum in channel " + channel + (" (stat only)" if args.onlyStat else "") + "} \n")
