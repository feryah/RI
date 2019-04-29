# -*- coding: utf-8 -*-
# ce script gère les requêtes utilisateur après indexation.py

import json

import glob
import sys
import re

from collections import defaultdict


    
def readAsDico(lg):
    """ ouvrir le fichier JSON comme dictionnaire """
    assert lg == "FR" or lg == "EN", "Problème : gestion du langage"
    if lg == "FR":
        with open("json/indexationFR.json", "r") as f:
            dico = json.load(f)
    elif lg == "EN":
        with open("json/indexationEN.json", "r") as f:
            dico = json.load(f)
    return dico

def normaliseRequete (req):
    """" Analyse de la requête et classification de ses tokens selon leur signe """
    
    global table_car
    requete=input(req) # Exemple de requête : +'Spider Cochon' -loup

    # les mots et leur 'signe' sont extraits de la requête dans 2 listes 'parallèles
    mots = []
    signes = []	
    
    if "'" in requete:
        #match = re.findall(r"([+-]+)(['A-Za-z\sA-Za-z']+)", requete)
        match = re.findall(r"([+-]*)([']*\w+\s*\w+[']*)", requete)
        
        for tup in match:
            signes.append(tup[0])
            tup = list(tup)
            tup[1] = re.sub (r"[']", r"", tup[1])
            mots.append(tup[1].translate(table_car))
    else:
        # nettoyage des caractères parasites autres que + ou -
        requete = re.sub (r"[^ _\w+-]", r"", requete)
        requete = re.sub (r"([+-])\s*", r"\1", requete)
        requete = re.sub (r"\s+", r" ", requete)
        for item in requete.split (' '):
        
    # le signe (+ ou -) est dissocié du token 
            match = re.findall(r'^([+-]*)([^+-]+)$', item)
            signes.append (match[0][0])
            mots.append (match[0][1].translate(table_car))
    
    
    tokens = mots
	
    # les tokens sont classés dans 3 listes des tokens en 3 listes
    tokCat = defaultdict(list)
    for i in range (len(tokens)):
        tokCat[signes[i]].append (tokens[i])

    return tokCat 


	
def scoreDocuments (docs, tokensNormalises, indexInverse):
    
    """ Evalue le nombre total de matchs de token par document """
      
    scores = defaultdict(int)
    for doc in docs:
        scores[doc] += 1

    return scores


def chercheDocumentsDeLaRequete(tokensNormalises, indexInverse):
    
    """ Cherche les documents demandés et renvoie les documents 'scorés' """
    
    docsTrouves = set()
    if '+' in tokensNormalises.keys ():
        # LES TOKENS OBLIGATOIRES PRENNENT LE PAS SUR LES FACULTATIFS 
        no = 0;
        for token in tokensNormalises['+']:
            # dès qu'un token obligatoire n'est pas dans l'index
            if token not in indexInverse.keys (): return set()
            
            docsToken = set(indexInverse[token])
            if (no == 0):
                docsTrouves = docsToken
                no = 1
            else :
                #docsTrouves = docsTrouves & docsToken
                docsTrouves = docsTrouves.intersection(docsToken)
    else :
        # CUMUL des documents des tokens FACULTATIFS
        for token in tokensNormalises['']:
            if token in indexInverse.keys ():

                docsToken = set(indexInverse[token])
                #docsTrouves = docsTrouves | docsToken
                docsTrouves = docsTrouves.union(docsToken)
                
                # SUPPRESSION des documents des tokens INTERDITS
    for token in tokensNormalises['-']:
        if token in indexInverse.keys ():

            docsToken = set(indexInverse[token])
            docsTrouves = docsTrouves - docsToken

    docsResultat = scoreDocuments (docsTrouves, tokensNormalises, indexInverse)
    
    return docsResultat

table_car = str.maketrans("àâèéêëîïôùûüÿç", "aaeeeeiiouuuyc")

reqLG = input("Language de la requête (EN/FR) : ")
dico = readAsDico(reqLG)

reqNorm = normaliseRequete("Taper une requête : ")

scorDocs = chercheDocumentsDeLaRequete(reqNorm, dico)

print(dict(scorDocs))


#testArgs()
#rep = sys.argv[1]+"/*/*.xml"
#rep = sys.argv[1]+"/*.xml"
#print("Chemin vers le corpus : {}".format(rep))



#for fichier in glob.glob(rep):
    #print("Fichier en cours d'indexation : {}".format(fichier))
    #id, tokens = readXML(fichier)
    #tfByDoc[id] = {}
    #for token in tokens:
        #if token not in tokens_freq:
            #tokens_freq[token] = [id]
        #else:
            #if id not in tokens_freq[token]:
                #tokens_freq[token].append(id)
        #if token not in tfByDoc[id].keys():
            #tfByDoc[id][token] = 1
        #else:
            #tfByDoc[id][token] += 1

#print(tfByDoc)

"""
with open("tfByDocFR.json", "w") as write_file:
    json.dump(tfByDoc, write_file, ensure_ascii=False)
"""