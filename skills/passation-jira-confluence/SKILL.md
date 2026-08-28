---
name: passation-jira-confluence
description: 'Rédige et contrôle un lot de passation (.md + .json) destiné à être appliqué à Jira ou Confluence par une extension navigateur. Use when the user asks to create, update or verify a "document de passation", "lot de passation", or to apply decisions to a Jira backlog / Confluence specifications via the browser extension.'
---

# Passation Jira / Confluence

**But :** produire un lot de passation fiable — un `.md` lisible et un `.json` machine, strictement cohérents — puis le contrôler avant livraison, afin qu'aucune écriture erronée ne parte dans Jira ou Confluence.

## RÈGLES CRITIQUES

- Un lot = **deux fichiers indissociables**, fournis ensemble : `… (pour extension Claude).md` et `… - operations.json`. Ils doivent dire exactement la même chose.
- **Ne jamais livrer sans avoir exécuté les contrôles de la section CONTRÔLES.** Ils ne sont pas optionnels.
- **Ne jamais réécrire un lot déjà appliqué** ni un compte rendu : ce sont des enregistrements datés. Une correction passe par un nouveau lot.
- Le `.md` étant régénéré par script, prévenir l'utilisateur que toute retouche manuelle sera perdue — ou basculer ce fichier en édition en place.

## STRUCTURE DU `.md`

1. Titre et chapeau — objet, cible (Jira ou Confluence), composant ou espace.
2. `## 0. Méthode` — API, format du champ, ordre d'application.
3. `## 0 bis. Précautions d'application` — **obligatoire**, voir ci-dessous.
4. Détail des changements — un identifiant par changement (`[C01]`, `[R01]`…), avec CHERCHER / REMPLACER PAR, ou la règle à ajouter.
5. Points validés / points en attente — séparés, et révisés à chaque nouvelle décision.

## BLOC « PRÉCAUTIONS D'APPLICATION » — à inclure dans tout lot

1. **Ordre impératif** — toutes les opérations globales d'abord, puis les modifications ciblées. Les textes ajoutés ne doivent jamais être retraités par les opérations globales.
2. **Remplacement sensible à la casse** — ne remplacer que les libellés à majuscule initiale (noms de statuts, d'écrans, de boutons). La même expression en minuscules dans une phrase est du français courant : la laisser.
3. **Exceptions explicites** — tout texte citant volontairement une ancienne valeur porte `excludeFromGlobalOperations: true`.
4. **`find` introuvable** — ne pas bloquer : signaler et poursuivre. Lister dans le lot les absences attendues et normales.
5. **`find` multiple** — s'arrêter et demander confirmation avant d'écrire.
6. **Dry-run obligatoire** — présenter le décompte par opération, attendre le feu vert, puis écrire.

Pour Confluence, ajouter :

7. **Numérotation** — les `BR` sont indicatifs : relever le dernier réellement présent dans la section et poursuivre à partir de lui, en conservant l'ordre donné.
8. **Résolution des pages** — une page sans `pageId` se résout par son titre, sous le `parentPageId` indiqué ; si elle est absente, s'arrêter et le signaler.

## CONTRÔLES — à exécuter avant toute livraison

Lancer `scripts/controle_passation.py` (voir ce dossier) :

```bash
python scripts/controle_passation.py <chemin.json> <chemin.md> [autre.md …]        --historique <dossier des lots antérieurs>
```

**Toujours passer `--historique`** : c'est ce qui permet les contrôles 5 et 6, les plus utiles.

| # | Contrôle | Ce qu'il détecte |
|---|---|---|
| 1 | Cohérence `.json` ↔ `.md` | un `with` / `find` / `description` / `Summary` présent dans le JSON mais absent du `.md` |
| 2 | Piège des valeurs citées | un texte ajouté qui cite une ancienne valeur qu'un remplacement global inverserait |
| 3 | Numérotation | trous ou collisions dans les identifiants ajoutés |
| 4 | Précautions | absence du bloc « Précautions » ou de la consigne de dry-run |
| 5 | Sections périmées | un point listé « en attente / à valider » alors que le lot le tranche |
| 6 | Cohérence inter-lots | un libellé fixé par un lot antérieur **déjà appliqué**, remplacé de fait par le lot courant sans opération de retrait |

Le contrôle 6 tient compte des `globalOperations` : un remplacement global couvre l'ancien texte partout, il ne déclenche donc pas d'alerte.

Reste **à la main**, le script ne pouvant pas les juger :
- la **pertinence** des textes rédigés (le contrôle 5 signale les suspects, pas les formulations inexactes) ;
- le **caractère caduc d'un lot entier** : si une décision rend inutile un lot préparé mais non appliqué, le déplacer dans `Caduc/` avec une note expliquant pourquoi.

## PIÈGES CONNUS

| Piège | Parade |
|---|---|
| Un `edit` ajouté à la structure n'apparaît pas dans le `.md`, écrit à la main avec des index | contrôle `.json` ↔ `.md` |
| Un texte ajouté cite les anciennes valeurs → le remplacement global l'inverse et le sens devient contraire à la décision | `excludeFromGlobalOperations` + ordre impératif |
| Marque-place en gras : le `find` ne prend pas les astérisques → marquage résiduel qui casse le rendu | inclure le marquage wiki dans le `find` |
| Expression en minuscules confondue avec un libellé | remplacement sensible à la casse |
| Trou ou collision dans la numérotation des règles | contrôle de contiguïté |
| Champ inexistant dans le projet (`Epic Link`, `External component`) | faire résoudre par l'extension depuis un ticket existant, ou retirer le champ |

## FORMAT DU `.json`

```
meta        : cible, composant/espace, formalisme, methode{api, ordre, precautions[]}, counts
globalOperations : replaceTextGlobal (find, with, scope, reason)
operations / modifications : par ticket (issueKey) ou par page (pageId | title+parentPageId)
             edits/operations : replaceText, deleteLine, appendToDescription,
                                addRule, removeRule, setRuleDescription, setSummary…
creations   : createPage / create (fields)
```

Conserver le formalisme des US : `*En tant que*` / `*Je veux*` / `*Afin de*` + `*Critère d'acceptance :*`, critères rédigés **en phrases** et non en listes à puces, marquage wiki markup verbatim.
