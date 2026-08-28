---
name: redaction-user-stories
description: 'Formalisme de rédaction des user stories et des critères d''acceptance du projet (PCO / OPUR, Jira TE_OPUR). Use when writing, rewriting or reviewing a user story, acceptance criteria, "critères d''acceptance", or the description of a Jira ticket for this project.'
---

# Rédaction des user stories

**But :** rédiger des US et des critères d'acceptance homogènes avec l'existant du backlog TE_OPUR, exploitables par un développeur et par un testeur sans avoir à deviner le contexte.

## RÈGLE CARDINALE

> **Un critère d'acceptance est une phrase complète qui dit QUAND le comportement se produit et CE QUI est attendu.**

Un critère qui donne un contenu (un message, un libellé, une valeur) sans dire **dans quelle situation il apparaît** est incomplet, même si le contenu est exact.

## STRUCTURE D'UNE US

```
*En tant que* <rôle>

*Je veux* <ce que je veux faire>

{*}Afin de{*} <bénéfice recherché>

*Critère d'acceptance :*

En tant que <rôle>, lorsque <contexte précis : écran, onglet, parcours, état>, je veux <comportement attendu>.
Je veux <comportement complémentaire>.
Je veux pouvoir <action possible>.
Lorsque <déclencheur>, je veux <comportement>.
Si <condition>, <comportement attendu>.
```

- Le triplet est en **wiki markup Jira** : `*En tant que*`, `*Je veux*`, `{*}Afin de{*}` (la forme `{*}…{*}` gère l'élision devant une voyelle). Marquage **conservé verbatim**.
- `*Critère d'acceptance :*` — au **singulier**, suivi de deux points.
- Rôles employés dans ce projet : « partenaire OPCO / contributeur », « contributeur », « administratrice du ROME ».

## LES CRITÈRES

1. **Le premier critère pose le contexte**, en une phrase :
   *« En tant que contributeur, lorsque je suis dans l'onglet "Caractéristiques" du parcours de modification d'une fiche Métier, je veux pouvoir saisir et sélectionner un secteur NAF. »*
2. **Les suivants héritent de ce contexte** et enchaînent en « Je veux… », « Je veux pouvoir… », « Je veux que… ».
3. **Un changement de situation se réintroduit** par « Lorsque… », « Si… », « Dès lors que… ».
4. **Une phrase = un comportement vérifiable.** Le testeur doit pouvoir écrire le cas de test sans poser de question.
5. **Jamais de listes à puces ni d'étiquettes.** Le contenu attendu s'intègre dans la phrase.

### Formulation d'un message ou d'un libellé

Ne pas se contenter de livrer le texte : dire **où**, **quand**, et **ce qui l'accompagne**.

❌ *« Pop-up de confirmation : ATTENTION, la substitution d'un item entraînera… — Boutons : Oui / Non. »*

✅ *« Je veux que, lorsque je clique sur « Substituer » depuis la modification d'un item publié, une boîte de dialogue s'ouvre et affiche « ATTENTION, la substitution d'un item entraînera la suppression de ses liens avec sa fiche. Souhaitez-vous tout de même poursuivre votre action ? », avec les boutons « Oui » et « Non », le mot « ATTENTION » en gras. »*

Pour une variante singulier / pluriel, faire **deux phrases** conditionnées :
*« Je veux que, lorsqu'un seul item est sélectionné, le message soit « … ». »*
*« Je veux que, lorsque plusieurs items sont sélectionnés, le message soit « … ». »*

## ANTI-PATTERNS

| À éviter | Pourquoi | À la place |
|---|---|---|
| `Pop-up de validation : <texte>` | étiquette, pas de contexte ni de déclencheur | « Je veux que, lorsque je valide ma sélection, une boîte de dialogue affiche… » |
| `Singulier : … / Pluriel : …` | ce n'est pas une phrase, la condition est implicite | deux phrases « lorsqu'un seul… » / « lorsque plusieurs… » |
| `Boutons : Oui / Non.` | fragment détaché du comportement | intégrer : « …, avec les boutons « Oui » et « Non ». » |
| Listes à puces de contenus | non testable, contexte perdu | une phrase par comportement |
| « Le système doit… » | le backlog est écrit du point de vue de l'utilisateur | « Je veux que… » |
| Critère qui décrit la solution technique | l'US décrit le besoin | décrire le comportement observable |

*(Les spécifications Confluence, elles, s'écrivent à la troisième personne : « L'application doit… ». C'est un autre document, ne pas confondre.)*

## CAS PARTICULIER — US d'arbitrage

Quand l'US sert à **obtenir une décision** et non à spécifier un comportement, dérouler les cas de figure avec un champ à compléter, chaque critère portant l'identifiant du cas dans la grille d'arbitrage :

```
[A2] Lorsqu'un item est créé sans être rattaché à une fiche ROME, je veux que le rapport <comportement attendu : ………>
```

## VOCABULAIRE DU PROJET

- **fiche Métier** (M majuscule) — jamais « fiche emploi » ni « fiche métier ». Ne pas modifier « fiche ROME ».
- **rubrique** = un onglet du parcours ; **sous-rubrique** = une liste d'items éditables à l'intérieur.
- **Libellés de boutons** : forme courte (« Créer une fiche »), l'intitulé complet allant dans le titre du bloc — guidelines UX France Travail.
- **Statuts** : les libellés affichés dans le panneau d'aide font foi — Validation de création en attente, Création refusée, Attribution en attente, En édition, Arbitrage en attente, En renvoi (n/3), Validée, Rejetée, Attribution refusée.
- Citer les libellés d'interface entre guillemets français « … ».
- **Apostrophe** : la prose des US emploie l'apostrophe **droite** (`'`), conformément au backlog. L'apostrophe typographique (`’`) n'apparaît que **dans les libellés d'interface cités**, lorsqu'elle fait partie du texte à livrer.
- Quand un libellé cité porte déjà sa ponctuation finale, ne pas ajouter de point après le guillemet fermant : *« … les offres. »* et non *« … les offres. ».*

## CONTRÔLE AVANT LIVRAISON

- [ ] Le triplet est présent, en wiki markup, avec `{*}Afin de{*}` si élision.
- [ ] `*Critère d'acceptance :*` au singulier.
- [ ] Le premier critère pose le contexte (écran, onglet, parcours, état).
- [ ] Chaque critère est une phrase complète, sans puce ni étiquette.
- [ ] Chaque message ou libellé est rattaché à un déclencheur explicite.
- [ ] Les variantes (singulier/pluriel, selon statut, selon rôle) font l'objet de phrases distinctes et conditionnées.
- [ ] Le vocabulaire du projet est respecté.
- [ ] Un testeur pourrait écrire les cas de test sans poser de question.
