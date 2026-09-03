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
6. **Ticket gelé** — avant toute écriture, relever le statut du ticket. Un ticket **en cours de développement** n'est plus modifiable : voir la section « TICKET GELÉ » ci-dessous. Ne jamais modifier silencieusement un ticket dans cet état.
7. **Dry-run obligatoire** — présenter le décompte par opération **et le statut de chaque ticket visé**, attendre le feu vert, puis écrire.

Pour Confluence, ajouter :

8. **Numérotation** — les `BR` sont indicatifs : relever le dernier réellement présent dans la section et poursuivre à partir de lui, en conservant l'ordre donné.
9. **Résolution des pages** — une page sans `pageId` se résout par son titre, sous le `parentPageId` indiqué ; si elle est absente, s'arrêter et le signaler.

## TICKET GELÉ — un ticket en développement ne se modifie pas

**Règle.** Un ticket entré en développement est figé : l'équipe travaille sur la description telle qu'elle était au moment de la prise en charge. La modifier après coup ferait diverger le développement en cours de sa spécification, sans que personne ne le voie.

**Ce qu'il faut faire à la place.** Créer une **US de complément** :

| | |
|---|---|
| **Titre** | celui du ticket d'origine, suivi de « — complément » |
| **Lien** | rattachée au ticket d'origine (`relates to`) |
| **Type, composant, épopée** | recopiés du ticket d'origine |
| **Description** | uniquement les modifications qui auraient été apportées, avec un rappel de ce qu'elles remplacent ou complètent |
| **Statut initial** | `New` |

**Ce qui est attendu du document de passation.** Chaque opération visant un ticket doit prévoir les deux issues : la modification directe si le ticket est encore ouvert, la création d'un complément s'il est gelé. Le `.md` porte le texte de la description de complément, prêt à être repris tel quel — on ne demande pas à l'extension de le rédiger.

**Ce qui est attendu de l'extension.** Relever le statut avant d'écrire, l'annoncer au dry-run, et basculer sur la création du complément sans demander d'arbitrage : la règle est posée ici.

*Pourquoi cette règle : une modification appliquée à un ticket en cours de développement est invisible pour qui a déjà commencé à travailler dessus. Le complément, lui, apparaît comme un nouvel élément à traiter.*

## CONTRÔLES — à exécuter avant toute livraison

Lancer `scripts/controle_passation.py` (voir ce dossier) :

```bash
python scripts/controle_passation.py <chemin.json> <chemin.md> [autre.md …] \
    --historique <dossier des lots antérieurs> \
    --backlog    <backlog consolidé.md> \
    --cr         <dossier des comptes-rendus> \
    --lisezmoi   <LISEZMOI - Index des passations.md> \
    --source     <document de travail .md ou .docx>
```

**Passer les cinq options.** Chacune débloque un contrôle qui ne peut pas s'exécuter sans elle, et ce sont les plus utiles : le script le rappelle en fin de rapport pour toute option manquante.

| # | Contrôle | Ce qu'il détecte | Option |
|---|---|---|---|
| 1 | Cohérence `.json` ↔ `.md` | un `with` / `find` / `description` / `Summary` présent dans le JSON mais absent du `.md` | — |
| 2 | Piège des valeurs citées | un texte ajouté qui cite une ancienne valeur qu'un remplacement global inverserait | — |
| 3 | Numérotation | trous ou collisions dans les identifiants ajoutés | — |
| 4 | Précautions | absence du bloc « Précautions », de la consigne de dry-run, ou — pour un lot qui modifie des tickets — de la règle du **ticket gelé** | — |
| 5 | Sections périmées | un point listé « en attente / à valider » alors que le lot le tranche | — |
| 6 | Cohérence inter-lots | un libellé fixé par un lot antérieur **déjà appliqué**, remplacé de fait par le lot courant sans opération de retrait | `--historique` |
| 7 | **Couverture** | un objet d'interface **nommé dans une décision mais sujet d'aucune US** — cité de partout, spécifié nulle part | `--backlog` |
| 8 | **Points en suspens** | une mention « à valider / à confirmer / à arbitrer » d'un CR qui ne figure pas dans les points ouverts de l'index | `--cr` + `--lisezmoi` |
| 9 | **Propagation** | un critère **rédigé dans le document de travail mais jamais passé** à Jira ou Confluence — l'écart entre ce qu'on a écrit et ce qu'on a livré | `--source` |

Le contrôle 6 tient compte des `globalOperations` : un remplacement global couvre l'ancien texte partout, il ne déclenche donc pas d'alerte.

Le contrôle 7 ignore les objets que le lot **retire** (« ne doit pas proposer de bouton « X » », « le bouton « X » soit supprimé ») : un objet supprimé n'a pas besoin d'US. Il compte comme couverture les US **créées par le lot lui-même**.

Le contrôle 9 compare les identifiants de la source — `[A1]`, `[E10]`, `[PCO] - Accueil#BR013` — à ceux que portent le lot courant **et** tous les lots de `--historique`. Il lit indifféremment un `.md` et un `.docx`. C'est le pendant du contrôle 7 : celui-ci vérifie la couverture **à l'intérieur** d'un lot, le 9 vérifie qu'un ajout fait **ailleurs** a bien été livré.

*Cas qui l'a motivé : les critères `[E10]` et `[E11]` du rapport « Mise à jour du ROME » avaient été ajoutés au document d'analyse — §4.E et l'US du §6 — sans qu'aucun lot ne les porte. Même angle mort que le panneau d'aide sur les statuts : un document de travail enrichi, un backlog qui ne suit pas.*

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
| **Un ticket pris en développement est modifié silencieusement** — le dev travaille sur une description qui a changé sous lui | contrôle 4 (mention du statut gelé) + US de complément |
| **Une décision porte sur un objet qui n'a pas d'US** — elle est rattachée au ticket le plus proche au lieu de faire lever « aucune US ne couvre ça » | contrôle 7 (`--backlog`) |
| **Un critère ajouté au document de travail n'est jamais passé à Jira** — l'analyse est à jour, le backlog non | contrôle 9 (`--source`) |
| **Un point « à valider » d'un CR est transcrit fidèlement puis oublié** — il disparaît dans le compte-rendu sans devenir un point ouvert suivi | contrôle 8 (`--cr` + `--lisezmoi`) |

### Le cas qui a motivé les contrôles 7 et 8

Le panneau « Aide concernant le statut des demandes » a été cité douze fois dans les décisions — il **faisait autorité sur les libellés de statuts** — sans qu'aucune US ne le décrive. Il apparaissait dans le CR du 28/07 (« Proposition à valider : Aide statuts ; Panel ajouté à l'écran à valider »), dans le tableau de wording du même CR, et dans le support du point UX.

Le mécanisme de l'oubli : **la propagation était un appariement, pas un contrôle de couverture.** Chaque décision était rattachée au ticket existant le plus proche ; celles qui portaient sur le panneau ont atterri sur l'US des statuts, faute de mieux. Une décision sans ticket d'accueil était absorbée par son voisin au lieu de déclencher une alerte.

**Règle qui en découle : un objet d'interface qui sert de référence dans une décision doit lui-même être spécifié quelque part.** S'il ne l'est pas, créer l'US avant de propager la décision.

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
