# -*- coding: utf-8 -*-
# TODO : 

#corriger le problème d'ouverture en lecture du fichier JSON en dico voir fonction readAsDico

import json
import xml.etree.ElementTree as ET

import glob
import sys
import re

import warnings
warnings.filterwarnings("ignore")
from treetaggerwrapper import TreeTagger
from collections import defaultdict

def usage():
    """
    gestion des arguments
    """
    sep = "-"*50
    message = "Usage : python3 {} <dossier comportant le corpus>".format(sys.argv[0])
    if len(sys.argv) != 2:
        print("{0}\nNombre d'arguments incorrect\n{1}\n{0}".format(sep,message))
        exit()
    elif not glob.glob(sys.argv[1]):
        print("{0}\n{2} est introuvable\n{1}\n{0}".format(sep,message,sys.argv[1]))
        exit()

def regLG():
    match_lg = re.search(".*([A-Z]{2})/", sys.argv[1])
    lg = match_lg.group(1)
    return lg

def tag_phrase(doc, lg):
    """
    permet de tagger du texte avec TreeTagger
    attend une chaîne de caractères
    renvoie une liste d'éléments taggés sous ce format : ['je\tPRO:PER\tje', 'suis\tVER:pres\tsuivre|être']
    """
    tag_options = TreeTagger(TAGLANG=lg,TAGOPT="-token -lemma -sgml -no-unknown")
    tags = tag_options.tag_text(doc)
    return tags

def tokenisation(triplet):
    """
    à partir d'un triplet Treetagger (sous forme de string 'je\tPRO:PER\tje'),
    détermine si on doit conserver le token dans l'index et si oui sous quelle forme
    critères : on veut des lemmes désaccentués et uniquement des VER, ADJ, ou NOM
    renvoie le token à indexer ou None
    """
    global table_car
    tok, pos, lem = triplet.split('\t')
    
    if regLG() == "FR":
        if 'VER' in pos or 'ADJ' in pos or 'NOM' in pos or 'NAM' in pos:
            return lem.translate(table_car)
    
    elif regLG() == "EN":
        if pos.startswith('V') or pos.startswith('J') or pos.startswith('N'):
            return lem
    else:
        return None

def constructList(listPath):
    ListTerms = []
    with open(listPath, 'r') as f:
        for line in f:
            line = line.strip()
            if line not in ListTerms:
                ListTerms.append(line)
    return ListTerms                
        
def findMultiWords(tokens, listTerms):
    result = [] #une liste des tokens, y compris des expressions polylexicales 
    index = 0
    max_index = len(tokens)
    while index < max_index:
        word = None
        for size in range(5, 0, -1):
            if index + size > max_index:
                continue
            pieces = tokens[index:(index + size)] #Un candidat polylexical d'une certaine taille
            piece = ""
            for x in pieces:
                piece = piece + ' ' + x #On met les tokens dans une seule chaîne de caractères "piece" pour faciliter la comparaisons avec le dico qu'on vient de créer
            piece = piece.strip(' ')
            if piece.lower() in listTerms:
                word = piece
                result.append(word)
                index = index + size
                break
        if word == None:
            index = index + 1
    return result
        
def lire_xml(fichier):
    """
    permet de parcourir un fichier xml
    attend le nom d'un fichier xml
    renvoie l'identifiant du fichier (string) et une lsite des tokens pertinents pour l'index inversé
    """
    # tester si fichier vraiment en xml
    match_lg = re.search("[^-]+-([A-Z]{2})\.xml", fichier)
    lg = match_lg.group(1).lower()
    assert lg == 'en' or lg == 'fr', "Problème : la langue du fichier n'est pas déterminée correctement"
    arbre = ET.parse(fichier)
    racine = arbre.getroot()
    id = racine[0].text
    tags = [tokenisation(tag) for tag in tag_phrase(racine[1].text, lg) if tokenisation(tag)]
    if lg == 'en':
        listTerms = constructList("/home/tim/Documents/RI/dicoEN.txt")
        multiwordsList = findMultiWords(tags, listTerms)
        if len(multiwordsList) > 0:
            for w in multiwordsList:
                tags.append(w)
    elif lg == 'fr':
        listTerms = constructList("/home/tim/Documents/RI/dicoFR.txt")
        multiwordsList = findMultiWords(tags, listTerms)
        if len(multiwordsList) > 0:
            for w in multiwordsList:
                tags.append(w)
    return id, tags

def to_json(data):
    """
    pour envoyer le résultat en json
    """
    if regLG() == "FR":
        with open("indexationFR.json", "w") as write_file:
            json.dump(data, write_file, ensure_ascii=False)
            
    if regLG() == "EN":
        with open("indexationEN.json", "w") as write_file:
            json.dump(data, write_file, ensure_ascii=False)
            
        return write_file
    
def readAsDico():
    """ ouvrir le fichier JSON comme dictionnaire """
    if regLG() == "FR":
        with open("/home/tim/Documents/RI/indexationFR.json", "r") as f:
            dico = json.load(f)
    if regLG() == "EN":
        with open("/home/tim/Documents/RI/indexationEN.json", "r") as f:
            dico = json.load(f)
        
        return dico
    


'''début gestionnaire de requêtes'''


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

    print (docs)
    return scores



def chercheDocumentsDeLaRequete (tokensNormalises, indexInverse):
    
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

usage()
#rep = sys.argv[1]+"/*/*.xml"
rep = sys.argv[1]+"/*.xml"
print("Chemin vers le corpus : {}".format(rep))

table_car = str.maketrans("àâèéêëîïôùûüÿç", "aaeeeeiiouuuyc")
tokens_freq = {}
tfByDoc = {}

dicoSyn = {'mouton': ['brebis', 'agneau'], 'loup':['louve'], 'pre':['champ'], 'Spider Cochon':['Harry Crotteur'], 'sheep pen':['sheepfold']}


for fichier in glob.glob(rep):
    id, tokens = lire_xml(fichier)
    
    for token in tokens:
        if token not in tokens_freq:
            tokens_freq[token] = [id]
            for k, v in dicoSyn.items():
                for e in v:
                    if k==token:
                        tokens_freq[e] = [id]
                    
        else:
            if id not in tokens_freq[token]:
                tokens_freq[token].append(id)
                for k, v in dicoSyn.items():
                    for e in v:
                        if k==token:
                            tokens_freq[e].append(id)
                
                
print(tokens_freq)

to_json(tokens_freq)

#dico = readAsDico()

#print(dico) #ça donne None, ???

reqNorm = normaliseRequete("Taper une requête :   ")

print(reqNorm)

docs=[]
for token, titres in tokens_freq.items():
    for titre in titres:
        for signe, liste in reqNorm.items():
            for mot in liste:
                if token==mot:
                    docs.append(titre)
                    

scorDocs = chercheDocumentsDeLaRequete (reqNorm, tokens_freq)


print(dict(scorDocs))


#scorDocs = chercheDocumentsDeLaRequete (reqNorm, dico) # marche pas quand c'est les données du fichier lues comme dico'


#print(dict(scorDocs))


#usage()
#rep = sys.argv[1]+"/*/*.xml"
#rep = sys.argv[1]+"/*.xml"
#print("Chemin vers le corpus : {}".format(rep))



#for fichier in glob.glob(rep):
    #print("Fichier en cours d'indexation : {}".format(fichier))
    #id, tokens = lire_xml(fichier)
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