from StopsDilepton.tools.helpers import mZ, getVarValue, getObjDict
from math import *
import numbers

jetVars = ['eta','pt','phi','btagCSV', 'id']

def getJets(c, jetVars=jetVars, jetColl="Jet"):
    return [getObjDict(c, jetColl+'_', jetVars, i) for i in range(int(getVarValue(c, 'n'+jetColl)))]

def jetId(j, ptCut=30, absEtaCut=2.4, ptVar='pt'):
  return j[ptVar]>ptCut and abs(j['eta'])<absEtaCut and j['id']

def getGoodJets(c, ptCut=30, absEtaCut=2.4, jetVars=jetVars):
    return filter(lambda j:jetId(j, ptCut=ptCut, absEtaCut=absEtaCut), getJets(c, jetVars))

def isBJet(j):
    return j['btagCSV']>0.890

def getGoodBJets(c):
    return filter(lambda j:isBJet(j), getGoodJets(c))

def getGenLeps(c):
    return [getObjDict(c, 'genLep_', ['eta','pt','phi','charge', 'pdgId', 'sourceId'], i) for i in range(int(getVarValue(c, 'ngenLep')))]

def getGenParts(c):
    return [getObjDict(c, 'GenPart_', ['eta','pt','phi','charge', 'pdgId', 'motherId', 'grandmotherId'], i) for i in range(int(getVarValue(c, 'nGenPart')))]

genVars = ['eta','pt','phi','charge', 'status', 'pdgId', 'motherId', 'grandmotherId','nDaughters','daughterIndex1','daughterIndex2','nMothers','motherIndex1','motherIndex2'] 
def getGenPartsAll(c):
    return [getObjDict(c, 'genPartAll_', genVars, i) for i in range(int(getVarValue(c, 'ngenPartAll')))]

#https://twiki.cern.ch/twiki/bin/viewauth/CMS/SUSLeptonSF
#https://www.dropbox.com/s/fsfw0gummwsc61v/lepawareJECv2_bkg_wp_300915.pdf?dl=0
multiIsoWP = {'VL':{'mRelIso':0.25, 'ptRatiov2':0.67, 'ptRelv2':4.4},
              'L' :{'mRelIso':0.20, 'ptRatiov2':0.69, 'ptRelv2':6.0},
              'M' :{'mRelIso':0.16, 'ptRatiov2':0.76, 'ptRelv2':7.2},
              'T' :{'mRelIso':0.12, 'ptRatiov2':0.80, 'ptRelv2':7.2},
              'VT':{'mRelIso':0.09, 'ptRatiov2':0.84, 'ptRelv2':7.2},
              }
multiIsoWPs=multiIsoWP.keys()

def multiIsoLepString(wpMu, wpEle, i):
    assert all([wp in multiIsoWPs for wp in [wpMu, wpEle]]),  "Unknown MultiIso WP %s or %s. Use one of %s"%(wpMu, wpEle, ",".join(multiIsoWPs))
    if type(i)==type(()) or type(i)==type([]):
        return "&&".join([multiIsoLepString(wpMu, wpEle, j) for j in i])
    stri = str(i) if type(i)==type("") else i
    return "((abs(LepGood_pdgId["+stri+"])==13&&LepGood_miniRelIso["+stri+"]<"+str(multiIsoWP[wpMu]['mRelIso'])+"&&(LepGood_jetPtRatiov2["+stri+"]>"+str(multiIsoWP[wpMu]['ptRatiov2'])+"||LepGood_jetPtRelv2["+stri+"]>"+str(multiIsoWP[wpMu]['ptRelv2'])+"))"\
              +"|| (abs(LepGood_pdgId["+stri+"])==11&&LepGood_miniRelIso["+stri+"]<"+str(multiIsoWP[wpEle]['mRelIso'])+"&&(LepGood_jetPtRatiov2["+stri+"]>"+str(multiIsoWP[wpEle]['ptRatiov2'])+"||LepGood_jetPtRelv2["+stri+"]>"+str(multiIsoWP[wpEle]['ptRelv2'])+")))"

def leptonIsoSelectorString( iso ):
    if isinstance(iso, numbers.Number):
        return  "LepGood_miniRelIso<%s"%iso
    elif type(iso)==type(""):
        return "LepGood_miniRelIso<{mRelIso}&&(LepGood_jetPtRatiov2>{ptRatiov2}||LepGood_jetPtRelv2>{ptRelv2})".format(**multiIsoWP[iso])
    else:
        raise ValueError( "Don't know what to do with iso %r" % iso )

def multiIsoSelector(WP):
    assert WP in multiIsoWPs,  "Unknown MultiIso WP %s. Use one of %s"%(WP, ",".join(multiIsoWPs))
    def func(l):
        return \
            l["miniRelIso"]<multiIsoWP[WP]['mRelIso'] \
            and (l["jetPtRatiov2"]>multiIsoWP[WP]['ptRatiov2'] or l['jetPtRelv2']>multiIsoWP[WP]['ptRelv2'] )
    return func

def miniIsoSelector( miniRelIso ):
    assert isinstance(miniRelIso, numbers.Number), "Don't know what to do with miniRelIso %r"%miniRelIso
    def func(l):
        return  l["miniRelIso"] < miniRelIso
    return func

# MUONS
def muonSelector(iso, absEtaCut = 2.4, dxy = 0.05, dz = 0.1):

    if isinstance(iso, numbers.Number):
        iso_ = miniIsoSelector( iso )
    elif type(iso)==type(""):
        iso_ = multiIsoSelector( iso )
    else:
        raise ValueError( "Don't know what to do with iso %r"%iso )

    def func(l, ptCut = 20):
        return \
            l["pt"]>=ptCut\
            and abs(l["pdgId"])==13\
            and abs(l["eta"])<absEtaCut\
            and l["mediumMuonId"]>=1 \
            and iso_(l) \
            and l["sip3d"]<4.0\
            and abs(l["dxy"])<dxy\
            and abs(l["dz"])<dz

    return func

default_muon_selector = muonSelector( iso = 'VT', absEtaCut = 2.4)

def muonSelectorString(iso = 'VT', ptCut = 20, absEtaCut = 2.4, dxy = 0.05, dz = 0.1):
    string = [\
                   "LepGood_pt>=%s"%ptCut ,
                   "abs(LepGood_pdgId)==13" ,
                   "abs(LepGood_eta)<%s" % absEtaCut ,
                   "LepGood_mediumMuonId>=1" ,
                   "LepGood_sip3d<4.0" ,
                   "abs(LepGood_dxy)<%s" % dxy ,
                   "abs(LepGood_dz)<%s" % dz ,
                   leptonIsoSelectorString( iso )
             ]
    string = 'Sum$('+'&&'.join(string)+')'
    return string


# ELECTRONS

ele_MVAID =  {'VL': {(0,0.8):-0.16 , (0.8, 1.479):-0.65, (1.57, 999): -0.74},
              'T':  {(0,0.8):0.87 , (0.8, 1.479):0.60, (1.57, 999):  0.17}
}

def eleMVAIDSelector( eleId ):
    ele_mva_WP = ele_MVAID[eleId]
    def func(l):
        abs_ele_eta = abs(l["eta"])
        for abs_ele_bin, mva_threshold in ele_mva_WP.iteritems():
            if abs_ele_eta>=abs_ele_bin[0] and abs_ele_eta<abs_ele_bin[1] and l["mvaIdSpring15"] > mva_threshold: return True
        return False
    return func

def eleCutIDSelector( ele_cut_Id = 4):
    def func(l):
        return l["eleCutIdSpring15_25ns_v1"]>=ele_cut_Id 
    return func

def eleSelector(iso, eleId = 4, absEtaCut = 2.4, dxy = 0.05, dz = 0.1):
    if isinstance(iso, numbers.Number):
        iso_ = miniIsoSelector( iso )
    elif type(iso)==type(""):
        iso_ = multiIsoSelector( iso )
    else:
        raise ValueError( "Don't know what to do with iso %r" % iso )
    if isinstance(eleId, numbers.Number):
        id_ = eleCutIDSelector( eleId )
    elif type(eleId)==type(""):
        id_ = eleMVAIDSelector( eleId )
    else:
        raise ValueError( "Don't know what to do with eleId %r" % eleId )

    def func(l, ptCut = 20):
        return \
            l["pt"]>=ptCut\
            and abs(l["eta"])<absEtaCut\
            and abs(l["pdgId"])==11\
            and id_(l)\
            and iso_(l)\
            and l["convVeto"]\
            and l["lostHits"]==0\
            and l["sip3d"] < 4.0\
            and abs(l["dxy"]) < dxy\
            and abs(l["dz"]) < dz
    return func

default_ele_selector = eleSelector( iso = 'VT', eleId = 4, absEtaCut = 2.4 )

def eleIDSelectorString( eleId ):
    if isinstance(eleId, numbers.Number):
        return "LepGood_eleCutIdSpring15_25ns_v1>=%i" % eleId 
    elif type(eleId)==type(""):
        return eleMVAString( eleId ) 
    else:
        raise ValueError( "Don't know what to do with eleId %r" % eleId )

def eleMVAString( eleId ):
    ele_mva_WP = ele_MVAID[eleId]
    abs_ele_eta = "abs(LepGood_eta)"
    strings = []
    for abs_ele_bin, mva_threshold in ele_mva_WP.iteritems():
        strings.append("({abs_ele_eta}>={low_abs_ele_eta}&&{abs_ele_eta}<{high_abs_ele_eta}&&LepGood_mvaIdSpring15>{mva_threshold})".format(\
            abs_ele_eta=abs_ele_eta, 
            low_abs_ele_eta = abs_ele_bin[0],
            high_abs_ele_eta=abs_ele_bin[1], 
            mva_threshold = mva_threshold))

    return "("+'||'.join(strings)+')'

def eleSelectorString(iso = 'VT', eleId = 4, ptCut = 20, absEtaCut = 2.4, dxy = 0.05, dz = 0.1):
    string = [\
                   "LepGood_pt>=%s" % ptCut ,
                   "abs(LepGood_eta)<%s" % absEtaCut ,
                   "abs(LepGood_pdgId)==11" ,
                   "LepGood_convVeto",
                   "LepGood_lostHits==0",
                   "LepGood_sip3d<4.0" ,
                   "abs(LepGood_dxy)<%s" % dxy ,
                   "abs(LepGood_dz)<%s" % dz ,
                   leptonIsoSelectorString( iso ),
                   eleIDSelectorString( eleId ),
             ]
    return 'Sum$('+'&&'.join(string)+')'

leptonVars=['eta','pt','phi','dxy', 'dz','tightId', 'pdgId', 'mediumMuonId', 'miniRelIso', 'sip3d', 'mvaIdSpring15', 'convVeto', 'lostHits', 'jetPtRelv2', 'jetPtRatiov2', 'eleCutIdSpring15_25ns_v1']

def getLeptons(c, collVars=leptonVars):
    return [getObjDict(c, 'LepGood_', collVars, i) for i in range(int(getVarValue(c, 'nLepGood')))]
def getOtherLeptons(c, collVars=leptonVars):
    return [getObjDict(c, 'LepOther_', collVars, i) for i in range(int(getVarValue(c, 'nLepOther')))]
def getMuons(c, collVars=leptonVars):
    return [getObjDict(c, 'LepGood_', collVars, i) for i in range(int(getVarValue(c, 'nLepGood'))) if abs(getVarValue(c,"LepGood_pdgId",i))==13]
def getElectrons(c, collVars=leptonVars):
    return [getObjDict(c, 'LepGood_', collVars, i) for i in range(int(getVarValue(c, 'nLepGood'))) if abs(getVarValue(c,"LepGood_pdgId",i))==11]

def getGoodMuons(c, ptCut = 20, collVars=leptonVars, mu_selector = default_muon_selector):
    return [l for l in getMuons(c, collVars) if mu_selector(l, ptCut = ptCut)]
def getGoodElectrons(c, ptCut = 20, collVars=leptonVars, ele_selector = default_ele_selector):
    return [l for l in getElectrons(c, collVars) if ele_selector(l, ptCut = ptCut)]
def getGoodLeptons(c, ptCut=20, collVars=leptonVars, mu_selector = default_muon_selector, ele_selector = default_ele_selector):
    return [l for l in getLeptons(c, collVars) if (abs(l["pdgId"])==11 and ele_selector(l, ptCut = ptCut)) or (abs(l["pdgId"])==13 and mu_selector(l, ptCut = ptCut))]

def getGoodAndOtherLeptons(c, ptCut=20, collVars=leptonVars, mu_selector = default_muon_selector, ele_selector = default_ele_selector):
    good_lep = getLeptons(c, collVars)
    other_lep = getOtherLeptons(c, collVars)
    for l in other_lep: #dirty trick to find back the full lepton if it was in the 'other' collection
        l['index']+=1000
    res = [l for l in good_lep+other_lep if (abs(l["pdgId"])==11 and ele_selector(l, ptCut = ptCut)) or (abs(l["pdgId"])==13 and mu_selector(l, ptCut = ptCut))]
    res.sort( key = lambda l:-l['pt'] )
    return res

tauVars=['eta','pt','phi','pdgId','charge', 'dxy', 'dz', 'idDecayModeNewDMs', 'idCI3hit', 'idAntiMu','idAntiE','mcMatchId']

def getTaus(c, collVars=tauVars):
    return [getObjDict(c, 'TauGood_', collVars, i) for i in range(int(getVarValue(c, 'nTauGood')))]

def looseTauID(l, ptCut=20, absEtaCut=2.4):
    return \
        l["pt"]>=ptCut\
        and abs(l["eta"])<absEtaCut\
        and l["idDecayModeNewDMs"]>=1\
        and l["idCI3hit"]>=1\
        and l["idAntiMu"]>=1\
        and l["idAntiE"]>=1\

def getGoodTaus(c, collVars=tauVars):
    return [l for l in getTaus(c,collVars=collVars) if looseTauID(l)]

idCutBased={'loose':1 ,'medium':2, 'tight':3}
photonVars=['eta','pt','phi','mass','idCutBased','pdgId']
photonVarsMC = photonVars + ['mcPt']
def getPhotons(c, collVars=photonVars, idLevel='loose'):
    return [getObjDict(c, 'gamma_', collVars, i) for i in range(int(getVarValue(c, 'ngamma')))]
def getGoodPhotons(c, ptCut=50, idLevel="loose", isData=True, collVars=None):
    if collVars is None: collVars = photonVars if isData else photonVarsMC
    return [p for p in getPhotons(c, collVars) if p['idCutBased'] >= idCutBased[idLevel] and p['pt'] > ptCut and p['pdgId']==22]
