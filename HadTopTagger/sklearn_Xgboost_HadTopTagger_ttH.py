import sys , time
#import sklearn_to_tmva
import sklearn
from sklearn import datasets
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.cross_validation import train_test_split
import pandas
#from pandas import HDFStore,DataFrame
import math
#import sklearn_to_tmva
#import xgboost2tmva
#import skTMVA
import matplotlib
matplotlib.use('agg')
#matplotlib.use('PS')   # generate postscript output by default
import matplotlib.pyplot as plt
from matplotlib import cm as cm
import numpy as np

import pickle

from sklearn.externals import joblib
import root_numpy
from root_numpy import root2array, rec2array, array2root, tree2array

import xgboost as xgb
import catboost as catboost #import CatBoostRegressor

from sklearn.model_selection import GridSearchCV
from sklearn.metrics import classification_report
from sklearn.metrics import roc_curve, auc
import ROOT
from tqdm import trange
import glob


inputPath='structured/'

# run: python sklearn_Xgboost_csv_evtLevel_ttH.py --channel '1l_2tau' --variables "noHadTopTaggerVar" --bdtType "evtLevelTTV_TTH"  >/dev/null 2>&1
# we have many trees 
# https://stackoverflow.com/questions/38238139/python-prevent-ioerror-errno-5-input-output-error-when-running-without-stdo

"""
from optparse import OptionParser
parser = OptionParser()
parser.add_option("--channel ", type="string", dest="channel", help="The ones whose variables implemented now are:\n   - 1l_2tau\n   - 2lss_1tau\n It will create a local folder and store the report*/xml", default='T')
parser.add_option("--variables", type="string", dest="variables", help="  Set of variables to use -- it shall be put by hand in the code, in the fuction trainVars(all)\n Example to 2ssl_2tau   \n                              all==True -- all variables that should be loaded (training + weights) -- it is used only once\n                               all==False -- only variables of training (not including weights) \n  For the channels implemented I defined 3 sets of variables/each to confront at limit level\n  trainvar=allVar -- all variables that are avaible to training (including lepton IDs, this is here just out of curiosity) \n  trainvar=oldVar -- a minimal set of variables (excluding lepton IDs and lep pt's)\n  trainvar=notForbidenVar -- a maximal set of variables (excluding lepton IDs and lep pt's) \n  trainvar=notForbidenVarNoMEM -- the same as above, but excluding as well MeM variables", default=1000)
parser.add_option("--bdtType", type="string", dest="bdtType", help=" evtLevelTT_TTH or evtLevelTTV_TTH", default='T')
parser.add_option("--hypOpt", action="store_true", dest="hypOpt", help="Runs hyp. optimiyation with GridSearchCV in XGBoost (of course you need to tune which ones to run on in the code, look for GridSearchCV) \n  It does not output any report than print the result of the ROC AUC in the screen.", default=False)
parser.add_option("--doXML", action="store_true", dest="doXML", help="Do save not write the xml file", default=False)
(options, args) = parser.parse_args()
#""" 

#channel="2lss_1tau"
channel="HadTopTagger" #options.channel #"1l_2tau"
if channel=='1l_2tau':channelInTree='1l_2tau_OS_Tight'


bdtType="CSV_screening" #options.bdtType #"evtLevelTT_TTH"
trainvar="allVar_lessBKG" #options.variables # 
inputTree="TCVARSbfilter"
target="bWj1Wj2_isGenMatched"
#trainvar="oldVar" 
#trainvar="notForbidenVar"
#trainvar="notForbidenVarNoMEM"

import shutil,subprocess
proc=subprocess.Popen(['mkdir '+channel],shell=True,stdout=subprocess.PIPE)
out = proc.stdout.read()

def save_model(model):
    # saving model
    json_model = model.to_json()
    open('model_architecture.json', 'w').write(json_model)
    # saving weights
    model.save_weights('model_weights.h5', overwrite=True)
	# https://stackoverflow.com/questions/40396042/how-to-save-scikit-learn-keras-model-into-a-persistence-file-pickle-hd5-json-ya

def trainVars(all):
        return [
		'CSV_b',  
		'alphaKinFit', 
		'dR_Wj1Wj2', 
		'dR_bW', 
		#'dR_bWj1', 
		#'dR_bWj2',  
		'm_Wj1Wj2', 
		#'m_Wj1Wj2_div_m_bWj1Wj2', 
		#'m_bWj1', 
		'm_bWj1Wj2', 
		#'m_bWj2', 
		#'max_dR_div_expRjet', 
		'nllKinFit', 
		'pT_Wj1',  
		'pT_Wj1Wj2', 
		'pT_Wj2', 
		'pT_b', 
		'pT_bWj1Wj2', 
		'qg_Wj1', 
		'qg_Wj2'
		#'qg_b'
		#'statusKinFit'
		]
####################################################################################################
## Load data 

features=[
		'CSV_b',  
		'alphaKinFit', 
		'dR_Wj1Wj2', 
		'dR_bW', 
		#'dR_bWj1', 
		#'dR_bWj2',  
		'm_Wj1Wj2', 
		#'m_Wj1Wj2_div_m_bWj1Wj2', 
		#'m_bWj1', 
		'm_bWj1Wj2', 
		#'m_bWj2', 
		#'max_dR_div_expRjet', 
		'nllKinFit', 
		'pT_Wj1',  
		'pT_Wj1Wj2', 
		'pT_Wj2', 
		'pT_b', 
		'pT_bWj1Wj2', 
		'qg_Wj1', 
		'qg_Wj2'
		#'qg_b'
		#'statusKinFit'
		]
# TTWJetsToLNu_fastsim  TTZToLLNuNu_fastsim 
print ("Date: ", time.asctime( time.localtime(time.time()) ))
my_cols_list=trainVars(True)+['key',target,'file'] #,'tau_frWeight','lep1_frWeight','lep1_frWeight'
# those last are only for channels where selection is relaxed (2lss_1tau) === solve later
data = pandas.DataFrame(columns=my_cols_list)
if bdtType=="evtLevelTT_TTH" : keys=['ttHToNonbb','TTTo2L2Nu','TTToSemilepton']
if bdtType=="evtLevelTTV_TTH" : keys=['ttHToNonbb','TTZToLLNuNu','TTWJetsToLNu']
if 1>0 :
		#print (list[ii],inputTree)
		tfile = ROOT.TFile("structured/structured_histograms_harvested_stage1_hadTopTagger_ttHToNonbb_fastsim_p2_less.root")
		tree = tfile.Get(inputTree)
		print tree.GetEntries()
		#tree.GetEntry(0) 
		#print tree.CSV_Wj1
		if tree is not None :
			chunk_arr = tree2array(tree) #,  start=start, stop = stop)
			#print chunk_arr
			chunk_df = pandas.DataFrame(chunk_arr,dtype=np.float64) #
			chunk_df['key']='ttHToNonbb'
			chunk_df["totalWeight"] = 1
			#print chunk_df["CSV_Wj1"]
			#chunk_df[target]=target
			#chunk_df['file']=list[ii].split("_")[10]
			#if channel=="2lss_1tau" : data["totalWeight"] = data.evtWeight * data.tau_frWeight * data.lep1_frWeight * data.lep2_frWeight 
			#if channel=="1l_2tau" : data["totalWeight"] = data.evtWeight 
			data=data.append(chunk_df, ignore_index=True)
		else : print ("file "+list[ii]+"was empty")
		tfile.Close()
print (data.columns.values.tolist())
#####################################
### drop 9/10 of original sample 
removeN=9*len(data.loc[data[target] == 0] )/10  
drop_indices = np.random.choice(data.loc[data[target] == 0].index, int(removeN), replace=False)
data.loc[data[target] == 0] = data.loc[data[target] == 0].drop(drop_indices)

n = len(data)
nS = len(data.loc[data[target] == 0])
nB = len(data.loc[data[target] == 1])
print "length of sig, bkg: ", nS, nB
print ("weigths", data.loc[data[target]==0]["totalWeight"].sum() , data.loc[data[target]==1]["totalWeight"].sum() )
################################################################################# 
print ("Date: ", time.asctime( time.localtime(time.time()) ))
## Balance datasets
#https://stackoverflow.com/questions/34803670/pandas-conditional-multiplication
print ("norm", data.loc[data[target]==0]["totalWeight"].sum(),data.loc[data[target]==1]["totalWeight"].sum())
for tar in [0,1] : data.loc[data[target]==tar, ['totalWeight']] *= 100000/data.loc[data[target]==tar]["totalWeight"].sum()

weights="totalWeight"
#print data.loc[data[target]==1]["totalWeight"]
#print data.loc[data[target]==0,["totalWeight","file"]]
# print data.loc[data['totalWeight']==np.nan, ['nJet','run','lumi','evt']] .values 

# drop events with NaN weights
#data.dropna(thresh=0)
data.dropna(subset=["totalWeight"],inplace = True) # data 

#print data[data[target]==0]["totalWeight"]
#print data[data[target]==1]["totalWeight"]

nS = len(data.loc[data[target].values == 0])
nB = len(data.loc[data[target].values == 1])
print "length of sig, bkg without NaN: ", nS, nB
#################################################################################
### Plot histograms
hist_params = {'normed': True, 'bins': 18, 'alpha': 0.4}
plt.figure(figsize=(30, 30))
for n, feature in enumerate(trainVars(False)):
    # add sub plot on our figure
	plt.subplot(4,4, n+1)
    # define range for histograms by cutting 1% of data from both ends
	min_value, max_value = np.percentile(data[feature], [1, 99]) 
	print (min_value, max_value,feature) 
	values, bins, _ = plt.hist(data.ix[data[target].values == 0, feature].values , weights= data.ix[data[target].values == 0, weights].values ,  
                               range=(min_value, max_value), 
							   label="BKG", **hist_params )
	values, bins, _ = plt.hist(data.ix[data[target].values == 1, feature].values, weights= data.ix[data[target].values == 1, weights].values , 
                               range=(min_value, max_value), label='Signal', **hist_params)
	areaSig = sum(np.diff(bins)*values) 
	#print areaBKG, " ",areaBKG2 ," ",areaSig
	if n == 0 : plt.legend(loc='best')
	plt.title(feature)
plt.savefig(channel+"/"+bdtType+"_"+trainvar+"_Variables_BDT.pdf")
plt.clf()
#########################################################################################
traindataset, valdataset  = train_test_split(data, test_size=0.5, random_state=7)
print (traindataset[trainVars(False)].columns.values.tolist())
#############################################################################################
## Training parameters 
print ("Date: ", time.asctime( time.localtime(time.time()) ))
hypOpt=False
if hypOpt==True :
	param_grid = {
				#'n_estimators': [1200,1500],
				#'min_child_weight': [10,20,30],
				'max_depth': [2,4,6],  
				'learning_rate': [0.01,0.02,0.03]
				}
	scoring = "roc_auc"
	early_stopping_rounds = None
	cv=3
	cls = xgb.XGBClassifier()
	fit_params = { "eval_set" : [(traindataset[trainVars(False)].values,traindataset[target])],
                           "eval_metric" : "roc_auc",
                           "early_stopping_rounds" : early_stopping_rounds }
	gs = GridSearchCV(cls, param_grid, scoring, fit_params, cv = cv, verbose = 1) 
	gs.fit(traindataset[trainVars(False)].values,traindataset[target])
	for i, param in enumerate(gs.cv_results_["params"]): 
		print("params : {} \n    cv auc = {}  +- {} ".format(param,gs.cv_results_["mean_test_score"][i],gs.cv_results_["std_test_score"][i]))
	print(gs.best_params_)
	print(gs.best_score_)
	gs = dm.grid_search_cv(clf, param_grid = param_grid,early_stopping_rounds = None)

"""
if trainvar=="oldVar" : cls = xgb.XGBClassifier(n_estimators = 2000, max_depth = 2, min_child_weight = 1, learning_rate = 0.01) #,max_depth=20,n_estimators=50,learning_rate=0.5)
if trainvar=="notForbidenVar" : cls = xgb.XGBClassifier(n_estimators = 2000, max_depth = 2, min_child_weight = 2, learning_rate = 0.01) #,max_depth=20,n_estimators=50,learning_rate=0.5)
if trainvar=="notForbidenVarNoMEM" : cls = xgb.XGBClassifier(n_estimators = 2000, max_depth = 2, min_child_weight = 2, learning_rate = 0.01)  #,max_depth=20,n_estimators=50,learning_rate=0.5)
if trainvar=="allVar" : 
"""
cls = xgb.XGBClassifier(n_estimators = 300, max_depth = 2, min_child_weight = 2, learning_rate = 0.01)  #,max_depth=20,n_estimators=50,learning_rate=0.5)

cls.fit(
	traindataset[features].values,  
	traindataset[target].astype(np.bool),  
	sample_weight= (traindataset[weights].astype(np.float64)),
	eval_set=[(traindataset[trainVars(False)].values,  traindataset[target].astype(np.bool),traindataset[weights].astype(np.float64)),
	(valdataset[trainVars(False)].values,  valdataset[target].astype(np.bool), valdataset[weights].astype(np.float64))] ,  
	verbose=True ,eval_metric="auc"
	)

print ("XGBoost trained") 
proba = cls.predict_proba(traindataset[features].values  )
fpr, tpr, thresholds = roc_curve(traindataset[target], proba[:,1] )
train_auc = auc(fpr, tpr, reorder = True) 
print("XGBoost train set auc - {}".format(train_auc)) 
proba = cls.predict_proba(valdataset[features].values)
fprt, tprt, thresholds = roc_curve(valdataset[target], proba[:,1] )
test_auct = auc(fprt, tprt, reorder = True)
print("XGBoost test set auc - {}".format(test_auct))
doXML=True
if doXML==True :
	# save the model in file 'xgb.model.dump'
	#model = cls.booster().get_dump(fmap='', with_stats=False) #.get_dump() #pickle.dumps(cls)
	#model2 = cls.booster().get_score(fmap='', importance_type='weight')
	pklpath=channel+"/"+channel+"_XGB_"+trainvar+"_"+bdtType+".pkl"
	pickle.dump(cls, open(pklpath, 'wb'))
	"""
	pickle.dump(model2, open(pklpath, 'wb'))
	#print json.dump(model2, ensure_ascii=False, sort_keys=True, indent=4, default=lambda x: None)
	with open(pklpath, 'rb') as fpkl, open('%s.json' % pklpath, 'w') as fjson:
		pkldata = pickle.load(fpkl)
		#model.save_model('0001.model')
		json.dump(pkldata, fjson, ensure_ascii=False, sort_keys=True, indent=4, default=lambda x: None)
	"""
	#print json.dumps(model, sort_keys=True)
	#xgboost2tmva.convert_model(model, trainVars(False), inputPath+"/"+channel+"_XGB_"+trainvar+"_"+bdtType+".xml")
	#parse in command line: xmllint --format TMVABDT_2lss_1tau_XGB_wMEMallVars.xml
print ("Date: ", time.asctime( time.localtime(time.time()) ))
##################################################
"""
if trainvar=="oldVar" :  clc = catboost.CatBoostClassifier(iterations=1800, depth=4, learning_rate=0.01, loss_function='Logloss',gradient_iterations=3,od_pval=0.01, verbose=True)
if trainvar=="notForbidenVar" : clc = catboost.CatBoostClassifier(iterations=2000, depth=2, learning_rate=0.01, loss_function='Logloss',od_pval=0.01, verbose=False)
if trainvar=="notForbidenVarNoMEM" : clc = catboost.CatBoostClassifier(iterations=1000, depth=3, learning_rate=0.01, loss_function='Logloss',gradient_iterations=3,od_pval=0.01, verbose=False)
if trainvar=="allVar" : 
"""
clc = catboost.CatBoostClassifier(iterations=20, depth=2, learning_rate=0.01, loss_function='Logloss',gradient_iterations=3,od_pval=0.01, verbose=False)

clc.fit(
	traindataset[trainVars(False)].values,  
	traindataset[target].values
	#sample_weight= np.absolute((traindataset[weights].astype(np.float64))),
	#eval_set=[(traindataset[trainVars(False)].values,  traindataset[target].astype(np.bool),traindataset[weights].astype(np.float64)),
	#(valdataset[trainVars(False)].values,  valdataset[target].astype(np.bool), valdataset[weights].astype(np.float64))] 
	)
#model = pickle.dumps(clc) # clc.get_dump() #
#xgboost2tmva.convert_model(model, trainVars(False), "TMVABDT_2lss_1tau_CB_wMEMallVars.xml")
# xmllint --format TMVABDT_2lss_1tau_XGB_wMEMallVars.xml
print ("CatBoost trained") 
proba = clc.predict_proba(traindataset[trainVars(False)].values  )
fprc, tprc, thresholds = roc_curve(traindataset[target], proba[:,1] )
train_aucc = auc(fprc, tprc, reorder = True) 
print("CatBoost train set auc - {}".format(train_aucc)) 
proba = clc.predict_proba(valdataset[trainVars(False)].values)
fprtc, tprtc, thresholds = roc_curve(valdataset[target], proba[:,1] )
test_auctc = auc(fprtc, tprtc, reorder = True)
print("CatBoost test set auc - {}".format(test_auctc))
##################################################
"""
clf = GradientBoostingClassifier(max_depth=3,learning_rate=0.01,n_estimators=100,verbose=True,min_samples_leaf=10,min_samples_split=10)
clf.fit(traindataset[trainVars(False)].values,  
	traindataset[target].values,  
	sample_weight= (traindataset[weights].astype(np.float64))
	)
# this works, we just do not need
#sklearn_to_tmva.gbr_to_tmva(clf,data[trainVars(False)],trainVars(False),channel+"_GB_wMEMallVars.xml",coef=2)
print ("GradientBoosting trained")
proba = clf.predict_proba(traindataset[trainVars(False)].values  )
fprf, tprf, thresholdsf = roc_curve(traindataset[target], proba[:,1] )
train_aucf = auc(fprf, tprf, reorder = True) 
print("GradientBoosting train set auc - {}".format(train_aucf)) 
proba = clf.predict_proba(valdataset[trainVars(False)].values)
fprtf, tprtf, thresholdsf = roc_curve(valdataset[target], proba[:,1] )
test_auctf = auc(fprtf, tprtf, reorder = True)
print("GradientBoosting test set auc - {}".format(test_auctf)) 
"""
##################################################
fig, ax = plt.subplots()
## ROC curve
#ax.plot(fprf, tprf, lw=1, label='GB train (area = %0.3f)'%(train_aucf))
#ax.plot(fprtf, tprtf, lw=1, label='GB test (area = %0.3f)'%(test_auctf))
ax.plot(fpr, tpr, lw=1, label='XGB train (area = %0.3f)'%(train_auc))
ax.plot(fprt, tprt, lw=1, label='XGB test (area = %0.3f)'%(test_auct))
ax.plot(fprc, tprc, lw=1, label='CB train (area = %0.3f)'%(train_aucc))
ax.plot(fprtc, tprtc, lw=1, label='CB test (area = %0.3f)'%(test_auctc))
ax.set_ylim([0.0,1.0])
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate')
ax.legend(loc="lower right")
ax.grid()
fig.savefig("{}/{}_{}_roc.png".format(channel,bdtType,trainvar))
fig.savefig("{}/{}_{}_roc.pdf".format(channel,bdtType,trainvar))
###########################################################################
## feature importance plot

fig, ax = plt.subplots()
f_score_dict =cls.booster().get_fscore()
f_score_dict = {features[int(k[1:])] : v for k,v in f_score_dict.items()}
feat_imp = pandas.Series(f_score_dict).sort_values(ascending=True)
feat_imp.plot(kind='barh', title='Feature Importances')
fig.tight_layout()
fig.savefig("{}/{}_{}_XGB_importance.png".format(channel,bdtType,trainvar))
fig.savefig("{}/{}_{}_XGB_importance.pdf".format(channel,bdtType,trainvar))
print (len(trainVars(True)),len(trainVars(False)),len(f_score_dict.items()))
###########################################################################
#print (list(valdataset))
hist_params = {'normed': True, 'bins': 20 , 'histtype':'step'}
plt.clf()
y_pred = cls.predict_proba(valdataset.ix[valdataset[target].values == 0, trainVars(False)].values)[:, 1] #  
y_predS = cls.predict_proba(valdataset.ix[valdataset[target].values == 1, trainVars(False)].values)[:, 1] # 
plt.figure('XGB',figsize=(6, 6)) 
values, bins, _ = plt.hist(y_pred , label="TT (XGB)", **hist_params)
values, bins, _ = plt.hist(y_predS , label="signal", **hist_params )
#plt.xscale('log')
#plt.yscale('log')
plt.legend(loc='best')
plt.savefig(channel+'/'+bdtType+'_'+trainvar+'_XGBclassifier.pdf')  
###########################################################################
plt.clf()
y_pred = clc.predict_proba(valdataset.ix[valdataset[target].values == 0, trainVars(False)].values)[:, 1] #  
y_predS = clc.predict_proba(valdataset.ix[valdataset[target].values == 1, trainVars(False)].values)[:, 1] # 
plt.figure('CB',figsize=(6, 6)) 
values, bins, _ = plt.hist(y_pred , label="TT (CB)", **hist_params)
values, bins, _ = plt.hist(y_predS , label="signal", **hist_params )
#plt.xscale('log')
#plt.yscale('log')
plt.legend(loc='best')
plt.savefig(channel+'/'+bdtType+'_'+trainvar+'_CBclassifier.pdf')  
###########################################################################
"""
plt.clf()
y_pred = clf.predict_proba(valdataset.ix[valdataset[target].values == 0, trainVars(False)].values)[:, 1] #  
y_predS = clf.predict_proba(valdataset.ix[valdataset[target].values == 1, trainVars(False)].values)[:, 1] # 
plt.figure( 'GB',figsize=(6, 6)) 
values, bins, _ = plt.hist(y_pred , label="TT (GB)", **hist_params)
values, bins, _ = plt.hist(y_predS , label="signal", **hist_params )
#plt.xscale('log')
#plt.yscale('log')
plt.legend(loc='best')
plt.savefig(channel+'/'+bdtType+'_'+trainvar+'_GBclassifier.pdf')  
"""
########################################################################
# plot correlation matrix
"""
print (len(trainVars(False)))
for ii in [1,2] :
	if ii == 1 :
		datad=data.ix[data[target].values == 1]
		label="signal"
	else :
		datad=data.ix[data[target].values == 0]
		label="BKG"
	data = datad[trainVars(False)] #.loc[:,trainVars(False)] #dataHToNobbCSV[[features]]
	correlations = data.corr()
	fig = plt.figure()
	
	ax = fig.add_subplot(111) 
	#ax.xticks(rotation=90)
	#ax.plot()
	cax = ax.matshow(correlations, vmin=-1, vmax=1)
	ticks = np.arange(0,len(trainVars(False)),1)
	ax.set_xticks(ticks)
	ax.set_yticks(ticks)
	ax.set_xticklabels(trainVars(False),rotation=45)
	ax.set_yticklabels(trainVars(False),rotation=-45)
	fig.colorbar(cax)
	plt.savefig("{}/{}_{}_corr_{}.png".format(channel,bdtType,trainvar,label))
	plt.savefig("{}/{}_{}_corr_{}.pdf".format(channel,bdtType,trainvar,label))
	ax.clear()
"""
###################################################################

#save the training to file for later use
#filename = 'sklearn_2lss_1tau_maxDepth3_8Var_frWt_wMEMall.pkl'
#obj=pickle.dump(cls, open(filename, 'wb'))
