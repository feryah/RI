# -*- coding: utf-8 -*-
# ce script gère l'indexation du corpus donné

import json
import xml.etree.ElementTree as ET

import glob
import sys
import os
import re

import warnings
warnings.filterwarnings("ignore")
from treetaggerwrapper import TreeTagger

def testArgs():
    """
    gestion des arguments du script
    renvoie le chemin vers les corpus français et anglais si ces derniers existent à l'emplacement donné
    """
    sep = "-"*50
    message = "Usage : python3 {} <dossier comportant le corpus>".format(sys.argv[0])
    if len(sys.argv) != 2:
        print("{0}\nNombre d'arguments incorrect\n{1}\n{0}".format(sep,message))
        exit()
    elif not glob.glob(sys.argv[1]):
        print("{0}\n{2} est introuvable\n{1}\n{0}".format(sep,message,sys.argv[1]))
        exit()
    else:
        assert os.path.isdir(sys.argv[1]), "Problème : corpus introuvable"
        return sys.argv[1] + "/FR/*.xml", sys.argv[1] + "/EN/*.xml"

def regLG(fichier):
    """
    détermine si le fichier est en anglais ou français (pour treetagger et pour le json)
    :param fichier: le fichier en question
    :return: la langue (string)
    """
    match_lg = re.search("[^-]+-([A-Z]{2})\.xml", fichier)
    lg = match_lg.group(1).lower()
    assert lg == 'en' or lg == 'fr', "Problème : la langue du fichier n'est pas déterminée correctement"
    return lg

def tagText(doc, lg):
    """
    permet de tagger du texte avec TreeTagger
    attend une chaîne de caractères
    renvoie une liste d'éléments taggés sous ce format : ['je\tPRO:PER\tje', 'suis\tVER:pres\tsuivre|être']
    """
    assert doc, "Problème : l'élément à tagger est vide"
    tag_options = TreeTagger(TAGLANG=lg,TAGOPT="-token -lemma -sgml -no-unknown")
    tags = tag_options.tag_text(doc)
    return tags

def tokenText(triplet, lg):
    """
    à partir d'un triplet Treetagger (sous forme de string 'je\tPRO:PER\tje'),
    détermine si on doit conserver le token dans l'index et si oui sous quelle forme
    critères : on veut des lemmes désaccentués et uniquement des VER, ADJ, ou NOM
    renvoie le token à indexer ou None
    """
    global table_car
    tok, pos, lem = triplet.split('\t')
    
    if lg == 'fr':
        if 'VER' in pos or 'ADJ' in pos or 'NOM' in pos or 'NAM' in pos:
            return lem.translate(table_car).lower()
    
    elif lg == 'en':
        if pos.startswith('V') or pos.startswith('J') or pos.startswith('N'):
            return lem.lower()
    else:
        return None

def constructList(listPath):
    """
    crée une liste de termes à partir d'un fichier (dico)
    :param listPath: chemin vers un fichier
    :return: liste
    """
    ListTerms = []
    with open(listPath, 'r') as f:
        for line in f:
            line = line.strip()
            if line not in ListTerms:
                ListTerms.append(line)
    return ListTerms                
        
def findMultiWords(tokens, listTerms):
    """
    permet de trouver les expressions polylexicales d'un texte
    :param tokens: les tokens
    :param listTerms: la liste d'expressions
    :return: une liste des tokens, y compris des expressions polylexicales
    """
    result = []
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
        
def readXML(fichier):
    """
    permet de parcourir un fichier xml
    attend le nom d'un fichier xml
    renvoie l'identifiant du fichier (string) et une liste des tokens pertinents pour l'index inversé
    """

    lg = regLG(fichier)

    arbre = ET.parse(fichier)
    racine = arbre.getroot()
    id = racine[0].text
    tags = [tokenText(tag, lg) for tag in tagText(racine[1].text, lg) if tokenText(tag, lg)]

    if lg == 'en':
        listTerms = constructList("dics/dicoEN.txt")
        multiwordsList = findMultiWords(tags, listTerms)
        if len(multiwordsList) > 0:
            for w in multiwordsList:
                tags.append(w)

    elif lg == 'fr':
        listTerms = constructList("dics/dicoFR.txt")
        multiwordsList = findMultiWords(tags, listTerms)
        if len(multiwordsList) > 0:
            for w in multiwordsList:
                tags.append(w)
    return id, tags

def docFreqMots(cheminCorpus):
    docMots = {}
    for fichier in glob.glob(cheminCorpus):
        id, tokens = readXML(fichier)
        docMots[id] = {} #un dico {key(mot) : value(frequence)}
        for token in tokens:
            if token not in docMots[id].keys():
                docMots[id][token] = 1
            else:
                docMots[id][token] += 1
    return docMots

def indexCorpus(cheminCorpus):
    """
    processus d'indexation d'un répertoire
    :param cheminCorpus: répertoire
    :return: un dictionnaire
    """
    global dicoSyn
    tokens_freq = {}
    for fichier in glob.glob(cheminCorpus):

        print("Fichier en cours d'indexation : {}".format(glob.glob(fichier)))
        id, tokens = readXML(fichier)

        for token in tokens:
            if token not in tokens_freq:
                tokens_freq[token] = [id]
                for k, v in dicoSyn.items():
                    for e in v:
                        if k == token:
                            tokens_freq[e] = [id]

            else:
                if id not in tokens_freq[token]:
                    tokens_freq[token].append(id)
                    for k, v in dicoSyn.items():
                        for e in v:
                            if k == token:
                                tokens_freq[e].append(id)
    return tokens_freq

def toJSON(data, lg):
    """
    pour envoyer le résultat en json
    """
    if lg == "fr":
        with open("json/indexationFR.json", "w") as write_file:
            json.dump(data, write_file, ensure_ascii=False)
            
    if lg == "en":
        with open("json/indexationEN.json", "w") as write_file:
            json.dump(data, write_file, ensure_ascii=False)
            
        return write_file


cheminCorpusFR, cheminCorpusEN = testArgs()
print("Chemin vers le corpus français : {}".format(cheminCorpusFR))
print("Chemin vers le corpus anglais : {}".format(cheminCorpusEN))


table_car = str.maketrans("àâèéêëîïôùûüÿç", "aaeeeeiiouuuyc")

dicoSyn = {'mouton': ['brebis', 'agneau'], 'loup':['louve'], 'pre':['champ'], 'spider cochon':['harry crotteur'], 'sheep pen':['sheepfold']}

toJSON(indexCorpus(cheminCorpusFR), 'fr')
toJSON(indexCorpus(cheminCorpusEN), 'en')
