import ROOT
from StopsDilepton.tools.helpers import getObjFromFile
import os

# Logging
import logging
logger = logging.getLogger(__name__)

e_file   = '$CMSSW_BASE/src/StopsDilepton/tools/data/leptonSFData/egammaEffi.txt_SF2D.root'
e_key    = "EGamma_SF2D"
m_file   = '$CMSSW_BASE/src/StopsDilepton/tools/data/leptonSFData/muon_tracking_sf.root'
m_key    = "ratio_eta"

class leptonHIPEfficiency:
    def __init__(self):

        self.e_sf = getObjFromFile(os.path.expandvars(e_file),   e_key)
        assert self.e_sf, "Could not load ele SF histo %s from file %s."%( e_key, e_file )

        self.e_ptMax = self.e_sf.GetYaxis().GetXmax()
        self.e_etaMax = self.e_sf.GetXaxis().GetXmax()
        self.e_etaMin = self.e_sf.GetXaxis().GetXmin()

        self.m_sf = getObjFromFile(os.path.expandvars(m_file),   m_key)
        assert self.m_sf, "Could not load muon SF histo %s from file %s."%( m_key, m_file )

        self.m_etaMax = self.m_sf.GetXaxis().GetXmax()
        self.m_etaMin = self.m_sf.GetXaxis().GetXmin()

    def getSF(self, pdgId, pt, eta):

        if abs(pdgId)==11:
            if not eta<=self.e_etaMax:
                logger.warning( "Supercluster eta out of bounds: %3.2f (need %3.2f <= eta <=% 3.2f)", eta, self.e_etaMin, self.e_etaMax )
                eta = self.e_etaMax
            if not eta>=self.e_etaMin:
                logger.warning( "Supercluster eta out of bounds: %3.2f (need %3.2f <= eta <=% 3.2f)", eta, self.e_etaMin, self.e_etaMax )
                eta = self.e_etaMin

            if pt>self.e_ptMax: pt=self.e_ptMax - 1 

            val = self.e_sf.GetBinContent( self.e_sf.FindBin(eta, pt) )
            valErr = self.e_sf.GetBinError( self.e_sf.FindBin(eta, pt) )

            return (val, valErr)

        elif abs(pdgId)==13:
            if not eta<=self.m_etaMax:
                logger.warning( "Muon eta out of bounds: %3.2f (need %3.2f <= eta <=% 3.2f)", eta, self.m_etaMin, self.m_etaMax )
                eta = self.m_etaMax
            if not eta>=self.m_etaMin:
                logger.warning( "Muon eta out of bounds: %3.2f (need %3.2f <= eta <=% 3.2f)", eta, self.m_etaMin, self.m_etaMax )
                eta = self.m_etaMin

            val = self.m_sf.Eval( eta )
            valErr = 0. # self.m_sf.GetBinError( self.m_sf.FindBin(eta) )

            return (val, valErr)

        else:
            raise ValueError( "Lepton pdgId %i neither electron or muon"%pdgId )


