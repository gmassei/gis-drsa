#!/usr/bin/env python
###############################################################################
#
# MODULE:	pyRough.py
# AUTHOR:	Gianluca Massei - Antonio Boggia
# PURPOSE:	The script implements Dominance Rough Set Approach algorithm named  DOMLEM (S. Greco, B. Matarazzo, R. Slowinski)
# COPYRIGHT:	c) 2010 Gianluca Massei, Antonio Boggia. This program is free software under the GNU General Public License (>=v2).
#
###############################################################################
#Require numpy

import sys
import copy
#import numpy as np
from time import time, ctime
import pickle


def collect_attributes (data):
	"Collects the values of header files isf, puts them in an array of dictionaries"
	header=[]
	attribute=dict()
	j=0
	start=(data.index(['**ATTRIBUTES'])+1)
	end=(data.index(['**PREFERENCES'])-1)
	for r in range(start, end):
		attribute={'name':data[r][1].strip('+:')}
		header.append(attribute)
	decision=data[end-1][1]
	end=(data.index(['**EXAMPLES']))

	start=(data.index(['**PREFERENCES'])+1)
	for r in header:
		r['preference']=data[start+j][1]
		j=j+1
	return header


def collect_examples (data):
	"Collect examples values and put them in a matrix (dictionary of lists) "

	matrix=[]
	data=[r for r in data if not '?' in r] #filter objects with " ?"
	start=(data.index(['**EXAMPLES'])+1)
	end=data.index(['**END'])
	for i in range(start, end):
		data[i]=(map(float, data[i]))
		matrix.append(data[i])
	i=1
	for r in matrix:
		r.insert(0, str(i))
		i=i+1
	#matrix=[list(i) for i in set(tuple(j) for j in matrix)] #remove duplicate example
	return matrix


def FileToInfoSystem(isf):
	"Read *.isf file and copy it's values in Infosystem dictionary"
	data=[]
	try:
		infile=open(isf,'r')
		rows=infile.readlines()
		for line in rows:
			line=(line.split())
			if (len(line)>0 ):
				data.append(line)
		infile.close()
		infosystem={'attributes':collect_attributes(data),'examples':collect_examples(data)}
	except TypeError:
		print "\n\n Computing error or input file %s is not readeable. Exiting" % isf
		sys.exit(0)

	return infosystem

def UnionOfClasses (infosystem):
	"Find upward and downward union for all classes and put it in a dictionary"
	DecisionClass=[]
	AllClasses=[]
	matrix=infosystem['examples']
	for r in matrix:
		DecisionClass.append(int(r[-1]))
	DecisionClass=list(set(DecisionClass))
	for c in range(len(DecisionClass)):
		tmplist=[r for r in matrix if int(r[-1])==DecisionClass[c]]
		AllClasses.append(tmplist)  
	print "all:%s \n dec:%s" % (AllClasses,DecisionClass)
	return AllClasses,DecisionClass
	
	
def DownwardUnionsOfClasses (infosystem):
	"For each decision class, downward union corresponding to a decision class\
	is composed of this class and all worse classes (<=)"

	DownwardUnionClass=[]
	DecisionClass=[]
	matrix=infosystem['examples']
	for r in matrix:
		DecisionClass.append(int(r[-1]))
	DecisionClass=list(set(DecisionClass))
	for c in DecisionClass:
		tmplist=[r for r in matrix if int(r[-1])<=c]
		print tmplist
		DownwardUnionClass.append(tmplist)
		#label=[row[0] for row in tmplist]
	return DownwardUnionClass


def UpwardUnionsOfClasses (infosystem):
	"For each decision class, upward union corresponding to a decision class \
	is composed of this class and all better classes.(>=)"

	UpwardUnionClass=[]
	DecisionClass=[]
	matrix=infosystem['examples']
	for r in matrix:
		DecisionClass.append(int(r[-1]))
	DecisionClass=list(set(DecisionClass))
	for c in DecisionClass:
		tmplist=[r for r in matrix if int(r[-1])>=c]
		UpwardUnionClass.append(tmplist)
		#label=[row[0] for row in tmplist]
	return UpwardUnionClass


###############################
def is_better (r1,r2, preference):
	"Check if r1 is better than r2"
	return all((( x >=y and p=='gain') or (x<=y and p=='cost')) for x,y, p in zip(r1,r2, preference) )


def is_worst (r1,r2, preference):
	"Check if r1 is worst than r2"
	return all((( x <=y and p=='gain') or (x>=y and p=='cost')) for x,y, p in zip(r1,r2, preference) )
 #################################


def DominatingSet (infosystem):
	"Find P-dominating set"
	matrix=infosystem['examples']
	preference=[s['preference'] for s in infosystem['attributes'] ]
	Dominating=[]
	for row in matrix:
		examples=[r  for r in matrix if  is_better(r[1:-1], row[1:-1], preference[:-1]) ]
		Dominating.append({'object':row[0], 'dominance':[i[0] for i in examples], 'examples':examples})
	return Dominating

def DominatedSet (infosystem):
	"Find P-Dominated set"
	matrix=infosystem['examples']
	preference=[s['preference'] for s in infosystem['attributes'] ]
	Dominated=[]
	for row in matrix:
		examples=[r  for r in matrix if  is_worst(r[1:-1], row[1:-1], preference[:-1]) ]
		Dominated.append({'object':row[0], 'dominance':[i[0] for i in examples], 'examples':examples})
	return Dominated


def LowerApproximation (UnionClasses,  Dom, DecisionClass):
	"Find Lower approximation and return a dictionaries list"
	c=0
	LowApprox=[]
	single=dict()
	for union in UnionClasses:
		tmp=[]
		UClass=set([row[0] for row in union] )
		for d in Dom:
			if (UClass.issuperset(set(d['dominance']))): #if Union class is a superse of dominating/dominated set, =>single Loer approx.
				tmp.append(d['object'])
		single={'class':DecisionClass[c], 'objects':tmp} #dictionary for lower approximation  -- 
		LowApprox.append(single) #insert all Lower approximation in a list
		c+=1
	return LowApprox


def UpperApproximation (UnionClasses,  Dom, DecisionClass):
	"Find Upper approximation and return a dictionaries list"
	c=0
	UppApprox=[]
	single=dict()
	for union in UnionClasses:
		UnClass=[row[0] for row in union]  #single union class
		s=[]
		for d in Dom:
		   if len(set(d['dominance']) & set(UnClass)) >0:
			   s.append(d['object'])
		single={'class':DecisionClass[c],'objects':list(set(s))}
		UppApprox.append(single)
		c+=1

	return UppApprox


def Boundaries (UppApprox, LowApprox):
	"Find Boundaries like doubtful regions"
	Boundary=[]
	single=dict()
	for i in range(len(UppApprox)):
		single={'class':i, 'objects':list (set(UppApprox[i]['objects'])-set(LowApprox[i]['objects']) )}
		Boundary.append(single)

	return Boundary


def AccuracyOfApproximation(UppApprox, LowApprox):
	"Define the accuracy of approximation of Upward and downward approximation class"
	return len(LowApprox)/len(UppApprox)


def QualityOfQpproximation(DownwardBoundary,  infosystem):
	"Defines the quality of approximation of the partition Cl or, briefly, the quality of sorting"
	UnionBoundary=set()
	U=set([i[0] for i in infosystem['examples']])
	for b in DownwardBoundary:
		UnionBoundary=set(UnionBoundary) | set(b['objects'])
	return float(len(U-UnionBoundary)) / float(len(U))


def FindObjectCovered (rules, matrix):
	"Find objects covered by a single rule and return\
	all related examples covered"

	examples=[r['objectsCovered'] for  r in rules ]

	if len(examples)>0:
		examples = reduce(set.intersection,map(set,examples))  #functional approach: intersect all lists if example is not empty
		examples = list(set(examples) & set([r[0] for r in matrix]))
	return examples #all examples covered from a single rule


def Evaluate (elem,rules,G,selected):
	"Calcolate first and second evaluate index, according with original DOMLEM Algorithm"
	tmpRules=copy.deepcopy(rules)
	tmpElem=copy.deepcopy(elem)
	tmpRules.append(tmpElem)
	Object=FindObjectCovered(tmpRules,selected)
	if(float(len(Object)))>0:
			 firstEvaluate=float(len(set(G) & set(Object))) / float(len(Object))
			 secondEvaluate=float(len(set(G) & set(Object)))
	else:
			 firstEvaluate=0
			 secondEvaluate=0
	return firstEvaluate,secondEvaluate



def FindBestCondition (best, elem, rules, selected, G):
	"Choose the best condition"

	firstElem,secondElem=Evaluate(elem,rules,G,selected)
	firstBest,secondBest=Evaluate(best,rules,G,selected)

	if (firstElem>firstBest) or (firstElem==firstBest and secondElem>=secondBest):
		best=copy.deepcopy(elem)
	else:
		best=best

	return best


def CheckRule(rule,B):
	"For each elementary condition e in rule, check if [rule - {e}] subset or equal B then E := E ? {e}"
	example=[c['objectsCovered'] for c in rule]
	for e in rule:
		temp=copy.deepcopy(rule)
		temp.pop(temp.index(e))
		if len(temp)!=0:
			examples = reduce(set.intersection,map(set,[t['objectsCovered'] for t in temp]))  #functional approach: intersect all lists if example is not empty
			if (set(examples).issubset(set(B))):
				rule.pop(rule.index(e))
	return rule

def Type_one_rule (c,  e,  preference,  matrix):
	elem={'criterion':c,'condition':e, 'sign':preference[c-1],'class':'', \
	'objectsCovered':[r[0] for r in matrix if (((r[c] >= e ) and (preference[c-1] == 'gain')) \
																			  or ((r[c] <= e ) and (preference[c-1] == 'cost' )))],'label':''}
	return elem

def Type_three_rule (c,  e,  preference,  matrix):
	elem={'criterion':c,'condition':e, 'sign':preference[c-1],'class':'', \
	'objectsCovered':[r[0] for r in matrix if (((r[c] <= e ) and (preference[c-1] == 'gain')) \
														or ((r[c] >= e ) and (preference[c-1] == 'cost' )))],'label':''}
	return elem

def FindRules (B, infosystem, type_rule):
	"Search rule from a family of lower approximation of upward unions \
	of decision classes"
	start=time()
	G=copy.deepcopy(B)        #a set of objects from the given approximation
	E=[]        #a set  of rules covering set B (is a list of dictionary)
	all_obj_cov_by_rules=[] #all objects covered by all rules in E

	matrix=copy.deepcopy(infosystem['examples'])
	criteria_num=len(infosystem['attributes'])
	preference=[s['preference'] for s in infosystem['attributes'] ] #extract preference label
	selected=copy.deepcopy(matrix) #storage reduct matrix by single elementary condition
	num_rules=0 #total rules number for each lower approximation

	while (len(G)!=0 ):
		rule=[]     #starting comples (single rule built from elementary conditions -E- )
		S=copy.deepcopy(G)         #set of objects currently covered by rule
		control=0
		while (len(rule)==0 or (set(obj_cov_by_rules)).issubset(B)==False):
			obj_cov_by_rules=[] #set covered by rules
			best={'criterion':'','condition':'','sign':'','class':'','objectsCovered':'','label':'', 'type':''} #best candidate for elementary condition - start as empty
			for c in range(1,criteria_num):
				Cond=[r[c] for r in matrix if  r[0] in S] #for each positive object from S create an elementary condition
				for e in Cond:
					if type_rule=='one':
						elem= Type_one_rule (c,  e,  preference,  matrix)
					elif type_rule=='three':
						elem= Type_three_rule (c,  e,  preference,  matrix)
					else:
						elem={'criterion':'','condition':'','sign':'','class':'','objectsCovered':'','label':'', 'type':''}
					best=FindBestCondition(best, elem, rule, selected, G)
			rule.append(best)   #add the best condition to the complex
##            obj_cov_by_rules=[r['objectsCovered'] for  r in rule ]
			obj_cov_by_rules=list((reduce(set.intersection,map(set,[r['objectsCovered'] for  r in rule ])))) #reduce():Apply function of two arguments cumulatively to the items of iterable, from left to right, so as to reduce the iterable to a single value.	
			S=list(set(S) & set(best['objectsCovered'] ))
			control+1
		rule=CheckRule(rule,B)

		E.append(rule) #add the induced rule

		all_obj_cov_by_rules=list(set(all_obj_cov_by_rules) | set(obj_cov_by_rules))
		G=list(set(B)-set(all_obj_cov_by_rules)) #remove example coverred by all finded rule -- this operation is a set difference
		selected=[o  for o in selected if  not  o[0]  in all_obj_cov_by_rules] #reduct matrix, remove object coverred by all finded rule

	return E

def Minimality(E):
	"Check if there is no other implication with an antecedent of at least the same \
	 weakness (in other words, rule using a subset of elementary conditions \
	 or/and weaker elementary conditions) and a consequent of at least the \
	 same strength (in other words, rule assigning objects to the same union or\
	 sub -union of classes) ---TODO---"
	M=[r for r in E ]
	for r in E:
		for c in r:
			print " class: %s cond: %s %s %s" % (c['class'], c['criterion'], c['sign'],c['condition'])
	return E


def FormatRules(RULES,E,type,app,attributes):
	"Make rules in readable and complete forms"
	for e in E:
		for i in e:
			i['class']=app['class']
			i['label']=attributes[i['criterion']-1]['name']

			if(type=='one'):
				i['type']='at last'
				if (attributes[i['criterion']-1]['preference']=='gain'):
					i['sign']='>='
				else:
					i['sign']='<='
			elif(type=='three'):
				i['type']='at most'
				if (attributes[i['criterion']-1]['preference']=='gain'):
					i['sign']='<='
				else:
					i['sign']='>='
			else:
				print " ERROR! "
		RULES.append(e)
	return RULES


def Domlem(Lu,Ld, infosystem):
	"DOMLEM algoritm \
	(An algorithm for induction of decision rules consistent with the dominance\
	principle - Greco S., Matarazzo, B., Slowinski R., Stefanowski J., 2000)"
	attributes=infosystem['attributes']

	RULES=[]

##  *** AT MOST {<= Class} - Type 3 rules ***"
	for app in Ld[:-1]:
		B=app['objects']
		E=FindRules(B, infosystem, 'three')
##        Minimality(E)
		RULES=FormatRules(RULES,E,'three',app,attributes)

	F=open("geo","w")
	pickle.dump(RULES,F)
	F.close()

## *** AT LEAST {>= Class} - Type 1 rules *** "
	for app in Lu[1:]:
		B=app['objects']
		E=FindRules (B, infosystem, 'one')
##        Minimality(E)
		RULES=FormatRules(RULES,E,'one',app,attributes)

	return RULES


def PrintRules(RULES):
	"Print rls output file"

	i=1
	outfile=open("rule.rls","w")
	outfile.write('[RULES:]\n')

	for R in RULES:
		outfile.write("%d: " % i, )
		for e in R:
				outfile.write("( %s %s %s )" % (e['label'], e['sign'],e['condition'] ))
		obj_cov_by_rules=list((reduce(set.intersection,map(set,[e['objectsCovered'] for  e in R ]))))
		outfile.write("=> ( class %s , %s ) \t{%s}\n" % ( e['type'], e['class'],(map(int,obj_cov_by_rules))))
		i+=1
	outfile.close()

	return 0


def main():
	"main function for stand alone program"

	try:
		start=time()
		print 'start:', ctime(time())
	####################################################################

	####################################################################
	##    infosystem=FileToInfoSystem("/home/gianluca/Documenti/modelli_GIS/RoughSet/Example_collaudo/Buses.isf")
	##    infosystem=FileToInfoSystem("/home/gianluca/.wine/drive_c/Programmi/4eMka2/Examples/exampDOMLEM.isf")
	##    infosystem=FileToInfoSystem("Examples\BusesMOD.isf")
	##    infosystem=FileToInfoSystem("/home/gianluca/Documenti/modelli_GIS/RoughSet/Example_collaudo/Countries-Crit-5.isf")
		infosystem=FileToInfoSystem("example.isf")
		AllClasses,DecisionClass=UnionOfClasses(infosystem)
		DownwardUnionClass=DownwardUnionsOfClasses(infosystem)
		UpwardUnionClass=UpwardUnionsOfClasses(infosystem)
		for d in DownwardUnionClass:
			print 'downward',d
			
		for d in UpwardUnionClass:
			print 'upward',d
		Dominating=DominatingSet(infosystem)
		Dominated=DominatedSet(infosystem)
	##    upward union class
		Lu=LowerApproximation(UpwardUnionClass, Dominating, DecisionClass) #lower approximation of upward union for type 1 rules
		Uu=UpperApproximation(UpwardUnionClass,Dominated, DecisionClass ) #upper approximation of upward union
		UpwardBoundary=Boundaries(Uu, Lu)
	##    downward union class
		Ld=LowerApproximation(DownwardUnionClass, Dominated, DecisionClass)# lower approximation of  downward union for type 3 rules
		Ud=UpperApproximation(DownwardUnionClass,Dominating, DecisionClass ) # upper approximation of  downward union
		DownwardBoundary=Boundaries(Ud, Ld)

		QualityOfQpproximation(DownwardBoundary,  infosystem)
		RULES=Domlem(Lu,Ld, infosystem)
		PrintRules(RULES)
		end=time()
		print "Time -> %.4f s" % (end-start)
		return 0
	except TypeError:
		print "\n\t Computing error. Exiting"
		sys.exit(0)

###########execute the script##########################
if __name__=='__main__':
	main()
#######################################################

