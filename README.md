# HF CONCEPT — accueil et catalogue V4

Prototype statique premium/discount pour les professionnels de l'horeca. Direction artistique blanc, graphite et bleu ; hero épuré, parcours par métier, équipement ou marque.

## Fonctionnalités
- Navigation responsive, recherche par nom et référence avec suggestions.
- Catalogue complet : familles, sous-catégories, marques, promotions, budget, tri et chargement progressif.
- Fiches produit avec galerie, description, caractéristiques, documents et lien source.
- Comparaison jusqu'à trois équipements.
- Mon projet : sélection persistante sur cet appareil, quantités, totaux HT/TTC et export texte.
- Navigation du catalogue conservée dans le fragment URL.

## Données
Import du site source Discount Horeca le 26 octobre 2026 : 1 364 fiches accessibles, sur 1 438 références découvertes via 282 pages de catégories. 61 anciennes URLs produit renvoient une erreur 404 et 13 ne conduisent plus à une fiche produit ; elles sont exclues. Rapport : data/import-report.json.

Les prix, remises, descriptions, références et caractéristiques proviennent des fiches source. Les images produit restent hébergées sur le site source. Les prix et indications de disponibilité sont un instantané, sans synchronisation temps réel. Les affectations aux métiers servent à guider la navigation et ne remplacent pas la vérification des spécifications.

14 marques disposent de fiches identifiées dans l'import. Maxima et Diversion restent présentées sur demande de conseil ; aucun produit ni exclusivité n'a été inventé.

## Exécution locale
Depuis la racine du dépôt :
```sh
python3 -m http.server 4173
```
Ouvrir http://localhost:4173. Un serveur HTTP est nécessaire pour charger les fichiers JSON.

## Actualiser le catalogue
Dépendance Python : lxml.
```sh
python3 scripts/import_catalog.py
python3 scripts/split_catalog.py
```
Relire le rapport d'import et vérifier les données avant publication. Les scripts utilisent dist/ si ce dossier existe, sinon la racine du dépôt.

## Validation
Syntaxe JavaScript vérifiée ; recherche, filtres, fiches, quantités et totaux testés ; présentation vérifiée sur ordinateur et mobile.

Ce prototype ne passe aucune commande et n'envoie aucun devis. La sélection reste locale au navigateur ; l'export texte permet de préparer une demande.
