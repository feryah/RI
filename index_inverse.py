# -*- coding: utf-8 -*-
# TODO : 
# gérer les mots composés,
# éventuellement les synonymes sauf si on le fait au niveau de la requête,
## rajouter des assert ?

import json
import xml.etree.ElementTree as ET

import glob
import sys
import re

import warnings
warnings.filterwarnings("ignore")
from treetaggerwrapper import TreeTagger

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
    lem = lem.lower()
    
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
        listTerms = constructList("./dicoEN.txt")
        multiwordsList = findMultiWords(tags, listTerms)
        if len(multiwordsList) > 0:
            for w in multiwordsList:
                tags.append(w)
    elif lg == 'fr':
        listTerms = constructList("./dicoFR.txt")
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
    
    
def index_inverse(fichier):
    """
    Crée un Iindex-inversé du texte du document spécifié.
    {"mot1": ["Titre_du_doc1"], "mot2": ["Titre_du_doc2", "Titre_du_doc1",..."], ...},
    """
    inverse = {}
    id, tokens = lire_xml(fichier)
    for token in tokens:
        if token not in inverse:
            inverse[token] = [id]
        else:
            if id not in inverse[token]:
                inverse[token].append(id)
                
    return inverse


'''début gestionnaire de requêtes'''

def processQuery():
    
    queryG = []
    global table_car
    
    
    queryRaw=input('Enter your query - ')
    
    if regLG() == "FR":
        queryT=queryRaw.split(" ")
        for word in queryT:
            queryG.append(word.lower().translate(table_car))
    
    if regLG() == "EN":
        queryT=queryRaw.split(" ")
        for word in queryT:
            queryG.append(word.lower())
    
    
    return queryG



def obtainTermsFromDictionary(queryG, inverse):
    listC = []
    for word in queryG:
        for element in inverse.keys():
            if(word==element):
                listC.append(inverse.values())
    return listC

usage()
#rep = sys.argv[1]+"/*/*.xml"
rep = sys.argv[1]+"/*.xml"
print("Chemin vers le corpus : {}".format(rep))

table_car = str.maketrans("àâèéêëîïôùûüÿç", "aaeeeeiiouuuyc")
tokens_freq = {}
tfByDoc = {}

for fichier in glob.glob(rep):
    ind_inv = index_inverse(fichier)
    print("Fichier en cours d'indexation : {}".format(fichier))


    print(ind_inv)

    #to_json(ind_inv)

    #req = obtainTermsFromDictionary(processQuery(), ind_inv)
    #print(req)

usage()
#rep = sys.argv[1]+"/*/*.xml"
rep = sys.argv[1]+"/*.xml"
print("Chemin vers le corpus : {}".format(rep))



for fichier in glob.glob(rep):
    print("Fichier en cours d'indexation : {}".format(fichier))
    id, tokens = lire_xml(fichier)
    tfByDoc[id] = {}
    for token in tokens:
        if token not in tokens_freq:
            tokens_freq[token] = [id]
        else:
            if id not in tokens_freq[token]:
                tokens_freq[token].append(id)
        if token not in tfByDoc[id].keys():
            tfByDoc[id][token] = 1
        else:
            tfByDoc[id][token] += 1

print(tfByDoc)

"""
with open("tfByDocFR.json", "w") as write_file:
    json.dump(tfByDoc, write_file, ensure_ascii=False)
"""