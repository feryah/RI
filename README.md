# Recherche d'informations : projet final (M2 TAL, Inalco, 2018-2019)

## Résumé
Projet réalisé par Milena Chaîne, Boyu Niu et Ferial Yahiaoui. 
Il consiste à indexer en python un corpus de documents XML (sous la forme d'un index inversé), puis de créer un gestionnaire de requêtes booléennes simples sur cet index.

## Arborescence et scripts
 - `dics` contient les dictionnaires de mots composés que l'indexeur va rechercher
 - `json`contient les fichiers d'indexation JSON
 - `miniCorpusXML`contient notre mini-corpus de travail
 - `indexation.py`permet de générer les indexs en JSON. Il peut donc être lancé une seule fois, sous ce format `python indexation.py miniCorpusXML`
 - `requetes.py`permet d'effectuer une requête booléenne sur un index JSON. On le lance ainsi `python requetes.py`
