#!/usr/bin/env python
''' Analysis script for standard plots
'''
#
# Standard imports and batch mode
#
import ROOT, os
ROOT.gROOT.SetBatch(True)
import itertools
import pickle
from math                                import sqrt, cos, sin, pi
import array

# RootTools
from RootTools.core.standard             import *

# StopsDilepton
from StopsDilepton.tools.user            import plot_directory
from StopsDilepton.tools.helpers         import deltaPhi, map_level
from Analysis.Tools.metFilters            import getFilterCut
from StopsDilepton.tools.cutInterpreter  import cutInterpreter
from StopsDilepton.tools.GaussianFit     import GaussianFit
from Analysis.Tools.QuantileMatcher      import QuantileMatcher

#
# Arguments
# 
import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',           action='store',      default='INFO',          nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE', 'NOTSET'], help="Log level for logging")
argParser.add_argument('--small',                                   action='store_true',     help='Run only on a small subset of the data?', )
argParser.add_argument('--fine',                                    action='store_true',     help='Fine binning?', )
argParser.add_argument('--noPUReweighting',                         action='store_true',     help='No PU reweighting?', )
argParser.add_argument('--mode',               action='store',      default="mumu",          nargs='?', choices=["mumu", "ee", "SF"], help="Lepton flavor")
argParser.add_argument('--overwrite',                               action='store_true',     help='Overwrite?', )
argParser.add_argument('--plot_directory',     action='store',      default='recoil_v5.3/')
argParser.add_argument('--era',                action='store', type=str,      default="2016")
argParser.add_argument('--selection',          action='store',      default='lepSel-btag0-relIso0.12-looseLeptonVeto-mll20-dPhiJet0-dPhiJet1-onZ')
args = argParser.parse_args()

#
# Logger
#
import StopsDilepton.tools.logger as logger
import RootTools.core.logger as logger_rt
logger    = logger.get_logger(   args.logLevel, logFile = None)
logger_rt = logger_rt.get_logger(args.logLevel, logFile = None)

if args.small:                        args.plot_directory += "_small"
if args.fine:                        args.plot_directory += "_fine"
#
# Make samples, will be searched for in the postProcessing directory
#
from Analysis.Tools.puReweighting import getReweightingFunction

if "2016" in args.era:
    year = 2016
elif "2017" in args.era:
    year = 2017
elif "2018" in args.era:
    year = 2018

logger.info( "Working in year %i", year )

if year == 2016:
    from StopsDilepton.samples.nanoTuples_Summer16_postProcessed import *
    from StopsDilepton.samples.nanoTuples_Run2016_17Jul2018_postProcessed import *
    mc             = [ Top_pow_16, TTXNoZ_16, TTZ_16, multiBoson_16, DY_LO_16]
elif year == 2017:
    from StopsDilepton.samples.nanoTuples_Fall17_postProcessed import *
    from StopsDilepton.samples.nanoTuples_Run2017_31Mar2018_postProcessed import *
    mc             = [ Top_pow_17, TTXNoZ_17, TTZ_17, multiBoson_17, DY_LO_17]
elif year == 2018:
    from StopsDilepton.samples.nanoTuples_Autumn18_postProcessed import *
    from StopsDilepton.samples.nanoTuples_Run2018_PromptReco_postProcessed import *
    mc             = [ Top_pow_18, TTXNoZ_18, TTZ_18, multiBoson_18, DY_LO_18]

try:
    data_sample = eval(args.era)
except Exception as e:
    logger.error( "Didn't find %s", args.era )
    raise e

for sample in mc: sample.style = styles.fillStyle(sample.color)

postfix = ""
if args.noPUReweighting:
    postfix = "_noPU"

output_directory = os.path.join(plot_directory, args.plot_directory+postfix, args.era, args.selection )

# Text on the plots
tex = ROOT.TLatex()
tex.SetNDC()
tex.SetTextSize(0.04)
tex.SetTextAlign(11) # align right

# Text on the plots
tex2 = ROOT.TLatex()
tex2.SetNDC()
tex2.SetTextSize(0.03)
tex2.SetTextAlign(11) # align right

def get_quantiles( histo, quantiles = [1-0.9545, 1-0.6826, 0.5, 0.6826, 0.9545]):
    thresholds = array.array('d', [ROOT.Double()] * len(quantiles) )
    histo.GetQuantiles( len(quantiles), thresholds, array.array('d', quantiles) )
    return thresholds 

def defDrawObjects( plotData, dataMCScale, lumi_scale ):
    lines = [
      (0.15, 0.95, 'CMS Preliminary' if plotData else 'CMS Simulation'), 
      (0.45, 0.95, 'L=%3.1f fb{}^{-1} (13 TeV) Scale %3.2f'% ( lumi_scale, dataMCScale ) ) if plotData else (0.45, 0.95, 'L=%3.1f fb{}^{-1} (13 TeV)' % lumi_scale)
    ]
    return [tex.DrawLatex(*l) for l in lines] 

def drawPlots(plots, mode, dataMCScale, drawObjects = None):
  for log in [False, True]:
    plot_directory_ = os.path.join(output_directory, mode + ("_log" if log else ""))
    for plot in plots:
      if not max(l[0].GetMaximum() for l in plot.histos): continue # Empty plot
      if mode == "all": plot.histos[1][0].legendText = "Data"
      if mode == "SF":  plot.histos[1][0].legendText = "Data (SF)"

      plotting.draw(plot,
	    plot_directory = plot_directory_,
	    ratio = {'yRange':(0.1,1.9)},
	    logX = False, logY = log, sorting = True,
	    yRange = (0.03, "auto") if log else (0.001, "auto"),
	    scaling = {0:1},
	    legend = (0.15,0.88-0.04*sum(map(len, plot.histos)),0.65,0.88),
	    drawObjects = defDrawObjects( True, dataMCScale , lumi_scale ) + ( drawObjects if drawObjects is not None else [] ) ,
        copyIndexPHP = True,
      )

#
# Read variables and sequences
#
read_variables = ["weight/F", "l1_eta/F" , "l1_phi/F", "l2_eta/F", "l2_phi/F", "JetGood[pt/F,eta/F,phi/F]", "dl_mass/F", "dl_eta/F", "dl_mt2ll/F", "dl_mt2bb/F", "dl_mt2blbl/F",
                  "met_pt/F", "met_phi/F", "MET_significance/F", "metSig/F", "ht/F", "nBTag/I", "nJetGood/I"]

# default offZ for SF
offZ = "&&abs(dl_mass-91.1876)>15" if not (args.selection.count("onZ") or args.selection.count("allZ") or args.selection.count("offZ")) else ""
def getLeptonSelection( mode ):
  if   mode=="mumu": return "nGoodMuons==2&&nGoodElectrons==0&&isOS&&isMuMu" + offZ
  elif mode=="mue":  return "nGoodMuons==1&&nGoodElectrons==1&&isOS&&isEMu"
  elif mode=="ee":   return "nGoodMuons==0&&nGoodElectrons==2&&isOS&&isEE" + offZ
  elif mode=="SF":   return "nGoodMuons+nGoodElectrons==2&&isOS&&(isEE||isMuMu)" + offZ

# qT + ETmiss + u = 0
u_para = "-met_pt*cos(met_phi-dl_phi)"        # u_para is actually (u+qT)_para = -ET.n_para
u_perp = "-met_pt*cos(met_phi-(dl_phi-pi/2.))"# u_perp = -ET.n_perp (where n_perp is n with phi->phi-pi/2) 

#nJetGood_binning = [1, 10 ]
qt_binning    = [0, 50, 100, 150, 200, 300, 400 ]
nvtx_binning   = [ 0, 20, 30, 40, 100 ]
u_para_binning   = [ i for i in range(-200, 201) ] if args.fine else [ i*5 for i in range(-40, 41) ]

#nJetGood_bins = [ (nJetGood_binning[i],nJetGood_binning[i+1]) for i in range(len(nJetGood_binning)-1) ]
qt_bins = [ (qt_binning[i],qt_binning[i+1]) for i in range(len(qt_binning)-1) ]
nvtx_bins      = [ (nvtx_binning[i],nvtx_binning[i+1]) for i in range(len(nvtx_binning)-1) ]

#
# Loop over channels
#

data_sample.name           = "data"
data_sample.style          = styles.errorStyle(ROOT.kBlack)

# Data weight & cut 
weightString =  "weight"
data_sample.setSelectionString([getFilterCut(isData=True, year=year), getLeptonSelection(args.mode), cutInterpreter.cutString(args.selection)])
data_sample.setWeightString( weightString )

# MC weight & cut
for sample in mc:
  if args.noPUReweighting:
    weightString =  "weight*reweightDilepTrigger*reweightLeptonSF*reweightBTag_SF*reweightLeptonTrackingSF"
  else:
    weightString =  "weight*reweightPU36fb*reweightDilepTrigger*reweightLeptonSF*reweightBTag_SF*reweightLeptonTrackingSF"

stack = Stack(mc, data_sample)

lumi_scale                 = data_sample.lumi/1000
data_sample.scale          = 1.
for sample in mc:
    sample.scale          = lumi_scale

# small 
if args.small:
    for sample in stack.samples:
        sample.normalization = 1.
        sample.reduceFiles( factor = 40 )
        sample.scale /= sample.normalization

pickle_file = os.path.join(output_directory, 'recoil_%s.pkl'%args.mode )
if not os.path.exists( output_directory ): 
    os.makedirs( output_directory )
if not os.path.isfile( pickle_file ) or args.overwrite:
    # Make 3D plot to get u_para/u_perp for in nJet and qt bins
    h3D_u_para = {}
    h3D_u_perp = {}
    for sample in stack.samples:
        h3D_u_para[sample.name] = sample.get3DHistoFromDraw("PV_npvsGood:dl_pt:"+u_para, [u_para_binning,qt_binning,nvtx_binning], binningIsExplicit=True)
        h3D_u_perp[sample.name] = sample.get3DHistoFromDraw("PV_npvsGood:dl_pt:"+u_perp, [u_para_binning,qt_binning,nvtx_binning], binningIsExplicit=True)
        h3D_u_para[sample.name].Scale(sample.scale)
        h3D_u_perp[sample.name].Scale(sample.scale)

    # Projections and bookkeeping
    u_para_proj = {}
    u_perp_proj = {}
    for prefix, u_proj, h3D_u in  [ [ "para", u_para_proj, h3D_u_para], [ "perp", u_perp_proj, h3D_u_perp ] ]:
        for h_name, h in h3D_u.iteritems():
            u_proj[h_name] = {}
            for nvtx_bin in nvtx_bins:
                u_proj[h_name][nvtx_bin] = {}
                i_jet_min = h.GetZaxis().FindBin(nvtx_bin[0]) 
                i_jet_max = h.GetZaxis().FindBin(nvtx_bin[1]) 
                for qt_bin in qt_bins:
                    i_qt_min = h.GetYaxis().FindBin(qt_bin[0]) 
                    i_qt_max = h.GetYaxis().FindBin(qt_bin[1]) 
                    u_proj[h_name][nvtx_bin][qt_bin] = h.ProjectionX("Proj_%s_%s_%i_%i_%i_%i"%( h_name, prefix, i_qt_min, i_qt_max-1, i_jet_min, i_jet_max-1), i_qt_min, i_qt_max-1, i_jet_min, i_jet_max-1) 
    pickle.dump( [u_para_proj, u_perp_proj], file( pickle_file, 'w' ) )
    logger.info( "Written pkl %s", pickle_file )
else:
    logger.info( "Loading pkl %s", pickle_file )
    u_para_proj, u_perp_proj = pickle.load( file( pickle_file ) )

fitResults = {}
for nvtx_bin in nvtx_bins:
    fitResults[nvtx_bin] = {}
    for qt_bin in qt_bins:
        fitResults[nvtx_bin][qt_bin] = {}
        for prefix, u_proj in  [ [ "para", u_para_proj], [ "perp", u_perp_proj ] ]:
            fitResults[nvtx_bin][qt_bin][prefix] = {'mc':{},'data':{}}
            # Get histos
            histos =  map_level( lambda s: u_proj[s.name][nvtx_bin][qt_bin], stack, 2 )
            # Transfer styles & text
            for i_l, l in enumerate(stack):
                for i_s, s in enumerate(l):
                    histos[i_l][i_s].style      = s.style
                    histos[i_l][i_s].legendText = s.texName

#            name = "u_%s_nJet_%i_%i_qt_%i_%i"%( prefix, nvtx_bin[0], dl_phi_bin[1], qt_bin[0], qt_bin[1] )
#            if name!="u_para_nJet_0_1_qt_150_200":continue

            # make plot
            name = "u_%s_nvtx_%i_%i_qt_%i_%i"%( prefix, nvtx_bin[0], nvtx_bin[1], qt_bin[0], qt_bin[1] )
            plot =  Plot.fromHisto( name = name, 
                    histos = histos, 
                    texX = "u_{#parallel}" if prefix == "para" else "u_{#perp}" ) 
            ## fit
            h_mc   = plot.histos_added[0][0].Clone()
            h_data = plot.histos_added[1][0].Clone()
            if h_mc.Integral()>0:
                h_mc.Scale(h_data.Integral()/h_mc.Integral())


            fitResults[nvtx_bin][qt_bin][prefix]['mc']['TH1F']   = h_mc 
            fitResults[nvtx_bin][qt_bin][prefix]['data']['TH1F'] = h_data 
 
            q_mc   = tuple(get_quantiles( h_mc ))
            q_data = tuple(get_quantiles( h_data ))
            median_shift = q_data[2]-q_mc[2]
            sigma1_ratio = (q_data[3]-q_data[1])/(q_mc[3]-q_mc[1]) if q_mc[3]-q_mc[1]!=0 else 0
            sigma2_ratio = (q_data[4]-q_data[0])/(q_mc[4]-q_mc[0]) if q_mc[4]-q_mc[0]!=0 else 0

            drawObjects = []
            drawObjects.append( tex2.DrawLatex(0.5, 0.86, '#Delta(med): %+3.1f   1#sigma: %4.3f  2#sigma  %4.3f' % ( median_shift, sigma1_ratio, sigma2_ratio) ) )

            # draw
            drawPlots( [ plot ],  mode = args.mode, dataMCScale = -1, drawObjects = drawObjects )

pickle_file = os.path.join(output_directory, 'recoil_fitResults_%s.pkl'%args.mode )
pickle.dump( fitResults, file( pickle_file, 'w' ) )
logger.info( "Written pkl %s", pickle_file )
