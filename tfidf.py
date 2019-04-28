import os
import sys
import re
import pathlib
import math
from collections import defaultdict
from shutil import copy

def calculeTF_IDF (term_freq, tfByDoc) :

	# calcul du nombre de tokens dans chaque document 
	tailleDocs = defaultdict(int)
	for doc in tfByDoc.keys():
		for word in tfByDoc[doc]:
			tailleDocs[doc] += tailleDocs[doc][word]

	nbDocs = len (tailleDocs.keys())

	tfIdf = {}
	for token in term_freq.keys():
		# Le tf-idf du token est constitué
		tfIdfToken = {}
		nbDocsToken = len (term_freq[token])
		for noDoc in term_freq[token]:
			# ...pour chacun de ses document
			# calcul du TF-IDF 
			tf = tfByDoc[noDoc][token] / tailleDocs[noDoc]
			idf = math.log (nbDocs / nbDocsToken, 10)
			tfIdfToken[noDoc] = tf * idf

		tfIdf[token] = tfIdfToken

	return tfIdf