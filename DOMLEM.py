#!/usr/bin/env python
'''
########################################################################
MODULE:		DOMLEM.py
AUTHOR:		Gianluca Massei - Antonio Boggia
PURPOSE:	The script implements Dominance Rough Set Approach algorithm 
			named  DOMLEM (S. Greco, B. Matarazzo, R. Slowinski)
COPYRIGHT:	c) 2012 Gianluca Massei and Antonio Boggia. This program is 
			free software under the GNU General Public License (>=v2).
########################################################################
'''


import sys,os
import collections
from time import time, ctime



def collect_examples(data):
	'''Collect examples values and put them in a matrix (list of lists)'''
	matrix=[]
	data=[r for r in data if not '?' in r] #filter objects with " ?"
	start=(data.index(['**EXAMPLES'])+1)
	end=data.index(['**END'])
	for i in range(start, end):
		data[i]=(map(float, data[i]))
		matrix.append(data[i])
	#matrix=[list(i) for i in set(tuple(j) for j in matrix)] #remove duplicate example ---TODO---
	key=range(1,len(matrix)+1)
	examples=dict(zip(key,matrix))
	return examples
	
	
def collect_attributes(data):
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
		r['id']=j
		j=j+1
	return header
	
	
def file2infosystem(isf):
	'''Read *.isf file and copy it's values in Infosystem dictionary'''
	data=[]
	try:
		infile=open(isf,'r')
		rows=infile.readlines()
		for line in rows:
			line=(line.split())
			if (len(line)>0 ):
				data.append(line)
		infile.close()
		infosystem={'attributes':collect_attributes (data),'examples':collect_examples(data)}
	except TypeError:
		print "\n\n Computing error or input file %s is not readeable. Exiting" % isf
		sys.exit(0)
	return infosystem
	
def union_classes(infosystem):
	"Find upward and downward union for all classes and put it in a dictionary"
	decision_class=[]
	all_class=[]
	matrix=infosystem['examples']
	for k,v in matrix.iteritems():
		decision_class.append(int(v[-1]))
	decision_class=list(set(decision_class))
	return decision_class
	

def downward_union_classes(infosystem,decision_class):
	"For each decision class, downward union corresponding to a decision class\
	is composed of this class and all worse classes (<=)"
	downward_union=[]
	matrix=infosystem['examples']
	for c in decision_class:
		tmplist={k:v for k,v in matrix.iteritems() if int(v[-1])<=c} 
		downward_union.append(tmplist)
	return downward_union

def upward_union_class (infosystem,decision_class):
	"For each decision class, upward union corresponding to a decision class \
	is composed of this class and all better classes.(>=)"
	upward_union=[]
	matrix=infosystem['examples']
	for c in decision_class:
		tmplist={k:v for k,v in matrix.iteritems() if int(v[-1])>=c}
		upward_union.append(tmplist)
	return upward_union

###############################
def is_better (r1,r2, preference):
	"Check if r1 is better than r2"
	return all((( x >=y and p=='gain') or (x<=y and p=='cost')) for x,y, p in zip(r1,r2, preference) )

def is_worst (r1,r2, preference):
	"Check if r1 is worst than r2"
	return all((( x <=y and p=='gain') or (x>=y and p=='cost')) for x,y, p in zip(r1,r2, preference) )
 #################################

def dominating_set(infosystem):
	"Find P-dominating set"
	matrix=infosystem['examples']
	preference=[s['preference'] for s in infosystem['attributes'] ]
	dominating=[]
	for key,value in matrix.iteritems():
		examples=[{k:v} for k,v in matrix.iteritems() if  is_better(v[:-1], value[:-1], preference[:-1])]
		dominating.append({'object':key, 'examples':examples})
	return dominating #objects dominating obj key

def dominated_set(infosystem):
	"Find P-Dominated set"
	matrix=infosystem['examples']
	preference=[s['preference'] for s in infosystem['attributes'] ]
	dominated=[]
	for key,value in matrix.iteritems():
		examples=[{k:v} for k,v in matrix.iteritems() if  is_worst(v[:-1], value[:-1], preference[:-1])]
		dominated.append({'object':key, 'examples':examples})
	return dominated #objects dominated obj key

def lower_approximation(union_class, dominance, decision_class):
	"Find Lower approximation and return a dictionaries list"
	c=0
	lower=[]
	single=dict()
	for union in union_class:
		temp=[]
		union_set=set(union.keys())
		for d in dominance:
			dominance_set=set(sum([k.keys() for k in d['examples']],[])) #extract keys object
			if union_set.issuperset(dominance_set):
				temp.append(d['object'])
		single={'class':decision_class[c], 'objects':temp} #dictionary for lower approximation  
		lower.append(single) #insert all Lower approximation in a list-
		c+=1
	return lower


def upper_approximation(union_class, dominance, decision_class):
	"Find Upper approximation and return a dictionaries list"
	c=0
	upper=[]
	single=dict()
	for union in union_class:
		temp=[]
		union_set=set(union.keys())  #single union class
		for d in dominance:
			dominance_set=set(sum([k.keys() for k in d['examples']],[])) #extract keys object
			if len(dominance_set & set(union_set)) >0:
			   temp.append(d['object'])
		single={'class':decision_class[c],'objects':list(set(temp))}
		upper.append(single)
		c+=1
	return upper


def Boundaries (UppApprox, LowApprox):
	"Find Boundaries like doubtful regions"
	Boundary=[]
	single=dict()
	for i in range(len(UppApprox)):
		single={'class':i, 'objects':list (set(UppApprox[i]['objects'])-set(LowApprox[i]['objects']) )}
		Boundary.append(single)
	return Boundary


def AccuracyOfApproximation(UppApprox, LowApprox):
	"""Define the accuracy of approximation of Upward and downward approximation class"""
	return len(LowApprox)/len(UppApprox)


def QualityOfQpproximation(DownwardBoundary,  infosystem):
	"""Defines the quality of approximation of the partition Cl or, briefly, the quality of sorting"""
	UnionBoundary=set()
	U=set([i[0] for i in infosystem['examples']])
	for b in DownwardBoundary:
		UnionBoundary=set(UnionBoundary) | set(b['objects'])
	return float(len(U-UnionBoundary)) / float(len(U))
	
#######################################################################

def filter_infosystem(INFOSYS,keys):
	'''filter INFOSYS with list of keys'''
	return dict((k,v) for k,v in INFOSYS.items() if k in keys)   
		
		
def flatten(x):
	'''make a two dimensional irregular list in a simple flat list
	(from http://stackoverflow.com/questions/2158395/
	flatten-an-irregular-list-of-lists-in-python)'''
	if isinstance(x, collections.Iterable):
		return [a for i in x for a in flatten(i)]
	else:
		return [x]


def element_cover(INFOSYS,elem,rule_type):	#elem is a 'singleton' in a complex
	'''find objects covered by single element'''
	if rule_type=="one":
		if elem['preference']=='gain':
			return dict((key,value) for key,value in INFOSYS.items() if value[elem['criterion']]>=elem['condition'])
		else:
			return dict((key,value) for key,value in INFOSYS.items() if value[elem['criterion']]<=elem['condition'])
	elif rule_type=="three":
		if elem['preference']=='gain':
			return dict((key,value) for key,value in INFOSYS.items() if value[elem['criterion']]<=elem['condition'])
		else:
			return dict((key,value) for key,value in INFOSYS.items() if value[elem['criterion']]>=elem['condition'])
	else:
		return 0		

	
def complex_cover(INFOSYS,e,rule_type):
	'''find objects covered by complex e'''
	covered=[[element_cover(INFOSYS,elem,rule_type)] for elem in e]
	covered=[o.keys() for row in covered for o in row]
	if len(covered)>0:
		return list(reduce(set.intersection,map(set,covered))) #Reduce apply intersection of two arguments cumulatively to the items of iterable.
	else:
		return []


def rules_cover(INFOSYS,E,rule_type):
	'''find objects covered by rules'''
	covered=[complex_cover(INFOSYS,e,rule_type) for e in E]
	return list(set(flatten(covered)))
		
	
def remove_objects(INFOSYS,keys):
	'''remove objects in list objects from INFOSYS'''
	for obj in keys:
		del INFOSYS[obj]
	return INFOSYS
		 
		 
def evaluate_first_index(G,INFOSYS,e,rule_type):
	'''Calculate first misure between simple condition'''
	covered=complex_cover(INFOSYS,e,rule_type)
	if len(covered)>0:
		first=float(len(set(G) & (set(covered))))/float(len(set(covered))) #first
	else:
		first=0
	return first
		
		
def evaluate_second_index(G,INFOSYS,e,rule_type):
	'''Calculate second misure between simple condition'''
	covered=complex_cover(INFOSYS,e,rule_type)
	if len(covered)>0:
		second=float(len(set(G) & (set(covered)))) #second
	else:
		second=0
	return second


def evaluate(G,INFOSYS,e,rule_type):
	''' evaluete best elementary condition'''
	return evaluate_first_index(G,INFOSYS,e,rule_type),evaluate_second_index(G,INFOSYS,e,rule_type)
	
	
def find_best_elementary(G,INFOSYS,e,check,best,rule_type):
	'''find best elementary condition'''
	tempCheck=e[:]
	tempCheck.append(check)
	firstCheck,secondCheck=evaluate(G,INFOSYS,tempCheck,rule_type)
	tempBest=e[:]
	tempBest.append(best)
	if (best['criterion']==None or best['condition']==None):
		firstBest=secondBest=0
	else:
		firstBest,secondBest=evaluate(G,INFOSYS,tempBest,rule_type)
	if (firstCheck>firstBest) or (firstCheck==firstBest and secondCheck>=secondBest):
		return check
	else:
		return best	

def check_rules(EXAMPLES,e,B,rule_type):
	'''For each elementary condition e in E, check if [rule - {e}] subset or equal B then E := E ? {e}'''
	temp=e[:]
	for check in temp:
		temp.pop(temp.index(check))
		cover=complex_cover(EXAMPLES,temp,rule_type)
		if (len(temp)!=0 and set(cover).issubset(set(B))):
			e.pop(e.index(check))
	return e
	

def find_rules(EXAMPLES,approximation,header,rule_type):
	'''find roules from INFOSYS'''
	B=approximation['objects'][:]
	#print 'approximation [B]', B
	G=B[:]
	E=[] #RULES
	preference=[h['preference'] for h in header]
	criteria=[h['preference'] for h in header][:-1] #last criteria is decision field
	static_examples=EXAMPLES.copy()#copy original INFOSYS in a 'STATIC' dictionary
	while (len(G)!=0):
			e=[] #starting complex
			S=G[:] #set of objects currently covered by e
			while ((len(e)==0) or (set(complex_cover(EXAMPLES,e,rule_type)).issubset(set(B)))==False):
				best={'criterion':None,'condition':None,'sign':None,'class':None,'label':None,'rule_type':None,\
				'preference':None,'covered':None} #best candidate for elementary condition - start as empty
				for c in range(len(criteria)):
					Cond=[r[c] for r in [(EXAMPLES[k]) for k in S]] #for each positive object from S create an elementary condition
					for elem in Cond:
						check={'criterion':c,'condition':elem, 'preference':preference[c],'rule_type':rule_type,\
						'class':approximation['class']}
						best=find_best_elementary(G,EXAMPLES,e,check,best,rule_type)
				e.append(best)    #add the best condition to the complex  
				covered=element_cover(EXAMPLES,best,rule_type) #N.B. EXAMPLE/static_examples
				S=list(set(S) & (set(covered.keys())))			
			e=check_rules(static_examples,e,B,rule_type)
			E.append(e)
			#remove examples covered by RULE
			G=list((set(B))-(set(rules_cover(static_examples,E,rule_type)))) # N.B. rules_cover function act on original set of examples
	return E		

def format_rules(rules,RULES,header):
	"""Fill rules properties for a readable and complete forms"""
	for E in rules:
		for e in E:
			for h in header:
				if e['criterion']==h['id']:
					e['label']=h['name']
	for E in rules:
		for e in E:
			if(e['rule_type']=='one'):
				e['type']='AT LEAST'
				if e['preference']=='gain':
					e['sign']='>='
				else:
					e['sign']='<='
			elif(e['rule_type']=='three'):
				e['type']='AT MOST'
				if e['preference']=='gain':
					e['sign']='<='
				else:
					e['sign']='>='
			else:
				print " ERROR! "
		RULES.append(E)
	return RULES	
	
def print_rules(RULES,infosystem):
	"""Print rls output file"""
	EXAMPLES=infosystem['examples']
	j=1
	currentDIR = unicode(os.path.abspath( os.path.dirname(__file__)))
	outfile=open(currentDIR+"\\rules.rls","w")
	#outfile.write("\n##  AT LEAST {>= Class} - Type 1 rules and  AT MOST {<= Class} - Type 3 rules\n")
	outfile.write('\t[RULES:]\n')
	for E in RULES:
		outfile.write("%d: IF [" % j, )
		for e in E:
			outfile.write("(%s %s %s )" % (e['label'], e['sign'],e['condition'] ))
		outfile.write("] THEN  %s CLASS %s  \tSupport:%s\n" % ( e['type'], e['class'],complex_cover(EXAMPLES,E,e['rule_type'])))
		j+=1
	"""outfile.write("\n\nBased on DOMLEM algoritm implemented in python. \
	\nAn algorithm for induction of decision rules consistent with the dominance principle \
	\n ( Greco S., Matarazzo, B., Slowinski R., Stefanowski J., 2000) \n")"""
	outfile.write("Time:%s" % (ctime()))
	outfile.close()
	return 0

def compareRules(E1,E2):
	"""compare two rules for minimality check"""
	check=0
	if (len(E1)==len(E2)):
		for e1,e2 in zip(E1,E2):
			check=0
			if (e1['preference']=='gain') and (e1['sign']==e2['sign'] and e1['label']==e2['label'] \
				and e1['condition']==e2['condition'] and e1['class']>e2['class']):
					check=1
			elif (e1['preference']=='cost') and (e1['sign']==e2['sign'] and e1['label']==e2['label'] \
				and e1['condition']==e2['condition'] and e1['class']<e2['class']):
					check=1
			else:
				check=check
	return check
			 
			 
def minimality(RULES):
	"""check minimality for all rules"""
	minRULES=[E for E in RULES]
	for E1 in RULES:
			for E2 in RULES:
				chek=compareRules(E1,E2)
				if chek==1:
					
					minRULES.remove(E2)
	return minRULES
	
def main():
	"""main function for stand alone program"""
	try:
		start=time()
		print 'start:', ctime(time())

		currentDIR = unicode(os.path.abspath( os.path.dirname(__file__)))
		infosystem=file2infosystem(currentDIR+"\\example.isf")
		#infosystem=file2infosystem('example.isf')
		decision_class=union_classes(infosystem)
		downward_union_classes(infosystem,decision_class)

		up_class=upward_union_class(infosystem,decision_class)
		dw_class=downward_union_classes(infosystem,decision_class)

		dominating=dominating_set(infosystem)
		dominated=dominated_set(infosystem)

		##    upward union class
		lower_appx_up=lower_approximation(up_class, dominating, decision_class) #lower approximation of upward union for type 1 rules
		upper_appx_up=upper_approximation(up_class, dominated, decision_class)  #upper approximation of upward union

		##    downward union class
		lower_appx_dw=lower_approximation(dw_class, dominated, decision_class) # lower approximation of  downward union for type 3 rules
		upper_appx_dw=upper_approximation(dw_class, dominating, decision_class ) # upper approximation of  downward union
			
		header=infosystem['attributes']
		RULES=[]
	##  *** AT MOST {<= Class} - Type 3 rules ***"
		for lower in lower_appx_dw[:-1]:
			EXAMPLES=infosystem['examples'].copy()
			rules=find_rules(EXAMPLES,lower,header,"three")
			RULES=format_rules(rules,RULES,header)
	## *** AT LEAST {>= Class} - Type 1 rules *** "
		for lower in lower_appx_up[1:]:
			EXAMPLES=infosystem['examples'].copy()
			rules=find_rules(EXAMPLES,lower,header,"one")
			RULES=format_rules(rules,RULES,header)

			
		RULES=minimality(RULES)
		print_rules(RULES,infosystem)
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

"""Since a decision rule represents an implication, by a minimal decision rule we under-
stand such an implication that there is no other implication with an antecedent
of at least the same weakness and a consequent of at least the same strength."""
