# -*- coding: utf-8 -*-
# ce script gère les requêtes utilisateur après indexation.py

import json

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

def readAsDicoFreqMots(lg):
    """ ouvrir le fichier JSON comme dictionnaire """
    assert lg == "FR" or lg == "EN", "Problème : gestion du langage"
    if lg == "FR":
        with open("json/docFreqMotsFR.json", "r") as f:
            dico = json.load(f)
    elif lg == "EN":
        with open("json/docFreqMotsEN.json", "r") as f:
            dico = json.load(f)
    return dico

def normaliseRequete(req):
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
            mots.append(tup[1].translate(table_car).lower())
    else:
        # nettoyage des caractères parasites autres que + ou -
        requete = re.sub (r"[^ _\w+-]", r"", requete)
        requete = re.sub (r"([+-])\s*", r"\1", requete)
        requete = re.sub (r"\s+", r" ", requete)
        for item in requete.split (' '):
        
    # le signe (+ ou -) est dissocié du token 
            match = re.findall(r'^([+-]*)([^+-]+)$', item)
            signes.append (match[0][0])
            mots.append (match[0][1].translate(table_car).lower())
    
    
    tokens = mots
    
    # les tokens sont classés dans 3 listes des tokens en 3 listes
    tokCat = defaultdict(list)
    for i in range (len(tokens)):
        tokCat[signes[i]].append (tokens[i])

    return tokCat 


    
def scoreDocuments(docs, tokensNormalises, docMots):
    
    """ Evalue le nombre total de matchs de token par document """
    wordsInResearch = set()
    for x in tokensNormalises.keys():
        if x == '-':
            continue
        else:
            for word in tokensNormalises[x]:
                wordsInResearch.add(word)
    result = {}
    for doc in docs:
        result[doc] = 0
        for word in wordsInResearch:
            if word in docMots[doc].keys():
                result[doc] = result[doc] + docMots[doc][word]
    import operator
    
    scores = sorted(result.items(), key=operator.itemgetter(1), reverse=True)

    return scores


def chercheDocumentsDeLaRequete(tokensNormalises, indexInverse, docMots):
    
    """ Cherche les documents demandés et renvoie les documents 'scorés' """
    
    docsTrouves = set()
    if '+' in tokensNormalises.keys ():
        # LES TOKENS OBLIGATOIRES PRENNENT LE PAS SUR LES FACULTATIFS 
        no = 0
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

    docsResultat = scoreDocuments(docsTrouves, tokensNormalises, docMots)
    
    return docsResultat

def printResults(liste):
    """
    imprime les résultats depuis une liste de tuples (doc, score)
    :param liste de tuples: liste de titres et de leurs scores
    :return: void
    """
    for tup in liste:
        for titre in tup:
        #print("Titre du document trouvé : {} ({} tokens trouvé(s))".format(titre, int(dict[titre])))
            print("Titre du document trouvé : {} ({} tokens trouvé(s))".format(titre, int(tup[1])))
table_car = str.maketrans("àâèéêëîïôùûüÿç", "aaeeeeiiouuuyc")

reqLG = input("Language de la requête (EN/FR) : ")
dicoIndex = readAsDico(reqLG)
dicoFreq = readAsDicoFreqMots(reqLG)

reqNorm = normaliseRequete("Taper une requête [ex. +'Spider Cochon' -loup] : ")

scorDocs = chercheDocumentsDeLaRequete(reqNorm, dicoIndex, dicoFreq)

printResults(scorDocs)