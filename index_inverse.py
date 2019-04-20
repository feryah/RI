import json
import xml.etree.ElementTree as ET

import glob
import sys

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

def tag_phrase(doc):
    """
    permet de tagger du texte avec TreeTagger
    attend une chaîne de caractères
    renvoie une liste d'éléments taggés sous ce format : ['je\tPRO:PER\tje', 'suis\tVER:pres\tsuivre|être']
    """
    tag_options = TreeTagger(TAGLANG='fr',TAGOPT="-token -lemma -sgml -no-unknown")
    tags = tag_options.tag_text(doc)
    return tags

def lire_xml(fichier):
    """
    permet de parcourir un fichier xml
    attend le nom d'un fichier xml
    renvoie un dictionnaire contenant nom de balise et son contenu texte (provisoire)
    """
    # tester si fichier vraiment en xml
    arbre = ET.parse(fichier)
    racine = arbre.getroot()
    dict = { child.tag : child.text for child in racine }
    return dict

usage()
rep = sys.argv[1]+"/*/*.xml"
print("Chemin vers le corpus : {}".format(rep))

for fichier in glob.glob(rep):
    print("Fichier en cours d'indexation : {}".format(fichier))
    print(lire_xml(fichier))
