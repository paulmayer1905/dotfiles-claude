# -*- coding: utf-8 -*-
"""Contrôle d'un lot de passation avant livraison.

Usage :
    python controle_passation.py <operations.json> <delta.md> [autre.md ...]
                                 [--historique <dossier_des_lots_anterieurs>]

Contrôles :
  1. cohérence .json -> .md (tout texte porteur de sens du JSON figure dans le MD)
  2. piège des valeurs citées (un texte ajouté cite une valeur remplacée globalement)
  3. numérotation des identifiants ajoutés (contiguïté)
  4. présence du bloc « Précautions » et de la consigne de dry-run
  5. sections rédactionnelles périmées (un point listé « en attente » est traité par le lot)
  6. cohérence inter-lots (une décision antérieure appliquée est-elle contredite sans retrait ?)

Sortie : rapport lisible + code retour 1 si au moins un point est à corriger.
"""
import sys, os, json, re, glob, unicodedata

CLES_TEXTE = ('with', 'find', 'description', 'Description', 'Summary')
CLES_LISTE = ('notes', 'objectifs', 'elementsAction')
OPS_RETRAIT = ('deleteLine', 'removeRule', 'removeSection', 'replaceText', 'setRuleDescription')
VIDES = {'les', 'des', 'une', 'aux', 'sur', 'pour', 'dans', 'que', 'qui', 'est', 'sont',
         'doit', 'application', 'veux', 'lorsque', 'avec', 'par', 'plus', 'tout', 'toutes'}


def norm(s: str) -> str:
    s = unicodedata.normalize('NFKC', s)
    s = (s.replace('’', "'").replace('«', '"').replace('»', '"')
           .replace('—', '-').replace('–', '-'))
    return re.sub(r'\s+', ' ', s).strip().lower()


def collecte(obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in CLES_TEXTE and isinstance(v, str) and len(v) > 25:
                out.append((k, v))
            elif k in CLES_LISTE and isinstance(v, list):
                for x in v:
                    if isinstance(x, str) and len(x) > 25:
                        out.append((k, x))
            elif k != 'reason':
                collecte(v, out)
    elif isinstance(obj, list):
        for v in obj:
            collecte(v, out)


def libelles(texte):
    """Libellés d'interface : entre guillemets français ou droits."""
    out = re.findall(r'«\s*([^»]{3,60})\s*»', texte) + re.findall(r'"([^"]{3,60})"', texte)
    return [re.sub(r'\s+', ' ', x).strip() for x in out]


def mots(s):
    return {w for w in re.findall(r"[a-zà-ÿ]{3,}", norm(s)) if w not in VIDES}


def cibles_du_lot(data):
    """{cible: [textes]} — cible = issueKey ou titre de page."""
    res = {}
    for cle in ('operations', 'modifications'):
        for item in data.get(cle, []):
            nom = item.get('issueKey') or item.get('title') or '?'
            textes, retraits = [], []
            for e in item.get('edits', []) + item.get('operations', []):
                t = e.get('with', '') or e.get('description', '')
                if t:
                    textes.append(t)
                if e.get('op') in OPS_RETRAIT:
                    retraits.append(e.get('find', '') or e.get('uniqueId', '') or e.get('with', ''))
            res.setdefault(nom, {'textes': [], 'retraits': []})
            res[nom]['textes'] += textes
            res[nom]['retraits'] += retraits
    return res


def main():
    args = [a for a in sys.argv[1:]]
    hist_dir = None
    if '--historique' in args:
        i = args.index('--historique')
        hist_dir = args[i + 1] if i + 1 < len(args) else None
        del args[i:i + 2]
    if len(args) < 2:
        print(__doc__)
        return 2
    js, mds = args[0], args[1:]
    data = json.load(open(js, encoding='utf-8'))
    md_brut = "\n".join(open(m, encoding='utf-8').read() for m in mds if os.path.exists(m))
    if not md_brut:
        print("ERREUR : aucun .md lisible."); return 2
    txt = norm(md_brut)
    pb = 0

    # ---- 1. cohérence json -> md
    frags = []
    for cle in ('globalOperations', 'operations', 'modifications', 'creations'):
        if cle in data:
            collecte(data[cle], frags)
    manquants = [(k, v) for k, v in frags if norm(v)[:55] and norm(v)[:55] not in txt]
    print(f"[1] Cohérence .json -> .md : {len(frags)} fragments, {len(manquants)} absent(s)")
    for k, v in manquants[:10]:
        print(f"      - ({k}) {v[:100]}...")
    pb += len(manquants)

    # ---- 2. piège des valeurs citées
    anciens = [g.get('find', '') for g in data.get('globalOperations', []) if g.get('find')]
    pieges = []
    for cle in ('operations', 'modifications'):
        for item in data.get(cle, []):
            for e in item.get('edits', []) + item.get('operations', []):
                t = e.get('with', '') or e.get('description', '')
                if not t or e.get('excludeFromGlobalOperations'):
                    continue
                for a in anciens:
                    if a and a in t:
                        pieges.append((item.get('issueKey') or item.get('title'), a, e.get('reason', '')[:40]))
    print(f"[2] Valeurs remplacées citées dans un texte ajouté : {len(pieges)}")
    for cible, val, r in pieges[:10]:
        print(f"      ! {cible} cite « {val} »  ({r})")
        print(f"        -> ajouter \"excludeFromGlobalOperations\": true sur cet edit")
    pb += len(pieges)

    # ---- 3. numérotation
    print("[3] Numérotation des identifiants ajoutés :")
    trouve = False
    for item in data.get('modifications', []):
        nums = [int(m.group(1)) for o in item.get('operations', [])
                if o.get('op') == 'addRule'
                for m in [re.search(r'#\w*?(\d+)\s*$', o.get('uniqueId', '') or '')] if m]
        if nums:
            trouve = True
            trous = [n for n in range(min(nums), max(nums) + 1) if n not in nums]
            if trous:
                pb += 1
            print(f"      {item.get('title', '?'):34} {sorted(nums)}  {'TROU ' + str(trous) if trous else 'contigus'}")
    if not trouve:
        print("      (aucune règle numérotée)")

    # ---- 4. précautions / dry-run
    a_prec = 'précaution' in txt or 'precaution' in txt
    a_dry = 'dry-run' in txt or 'dry run' in txt
    print(f"[4] Bloc « Précautions » : {'oui' if a_prec else 'NON'}   |   dry-run : {'oui' if a_dry else 'NON'}")
    pb += (0 if a_prec else 1) + (0 if a_dry else 1)

    # ---- 5. sections rédactionnelles périmées
    # une puce listée sous un titre « en attente / à valider » ne doit pas être traitée par le lot
    corpus_ops = norm(" ".join(t for c in cibles_du_lot(data).values() for t in c['textes']))
    en_attente, section = [], False
    for ligne in md_brut.split('\n'):
        l = ligne.strip()
        if l.startswith('#'):
            section = bool(re.search(r'(en attente|à valider|a valider|restant|non trait)', l, re.I))
            continue
        if section and l.startswith(('-', '*')) and len(l) > 12:
            en_attente.append(l.lstrip('-* ').strip())
    perimes = []
    for item in en_attente:
        anc = libelles(item)
        cles = mots(item)
        # traité si un libellé cité est repris par une opération, ou fort recouvrement de mots
        if any(norm(a) in corpus_ops for a in anc if len(a) > 8):
            perimes.append((item, "libellé repris par une opération du lot"))
        elif len(cles) >= 4 and len(cles & mots(corpus_ops)) / len(cles) > 0.85:
            perimes.append((item, "sujet largement couvert par le lot"))
    print(f"[5] Sections « en attente » : {len(en_attente)} point(s), {len(perimes)} suspect(s) d'être périmé(s)")
    for it, why in perimes[:8]:
        print(f"      ! « {it[:88]} »")
        print(f"        -> {why} : ce point semble tranché, à retirer de la section")
    pb += len(perimes)

    # ---- 6. cohérence inter-lots
    print("[6] Cohérence avec les lots antérieurs :", end=" ")
    if not hist_dir or not os.path.isdir(hist_dir):
        print("non contrôlée (passer --historique <dossier>)")
    else:
        courant = cibles_du_lot(data)
        # un remplacement global couvre aussi l'ancien texte, où qu'il se trouve
        couverture_globale = norm(" ".join(g.get('find', '') for g in data.get('globalOperations', [])))
        alertes = 0
        for autre in sorted(glob.glob(os.path.join(hist_dir, '*.json'))):
            if os.path.abspath(autre) == os.path.abspath(js):
                continue
            try:
                d2 = json.load(open(autre, encoding='utf-8'))
            except Exception:
                continue
            for cible, c2 in cibles_du_lot(d2).items():
                if cible not in courant:
                    continue
                anciens_lib = {l for t in c2['textes'] for l in libelles(t) if len(l) > 8}
                nouveaux_lib = {l for t in courant[cible]['textes'] for l in libelles(t) if len(l) > 8}
                retraits = norm(" ".join(courant[cible]['retraits']))
                for a in anciens_lib:
                    if a in nouveaux_lib:
                        continue
                    # libellé proche mais différent => contradiction potentielle
                    for n in nouveaux_lib:
                        communs = mots(a) & mots(n)
                        if len(communs) >= 2 and norm(a) != norm(n):
                            couvert = (norm(a) in retraits) or (norm(a) in couverture_globale)
                            if not couvert:
                                alertes += 1
                                print()
                                print(f"      ! {cible} : « {a} » (lot {os.path.basename(autre)[:38]}…)")
                                print(f"        remplacé de fait par « {n} » — aucune opération de retrait détectée")
                                print(f"        -> prévoir un deleteLine / removeRule / replaceText sur l'ancien texte")
                            break
        if alertes == 0:
            print("aucune contradiction non traitée détectée")
        pb += alertes

    print("\n" + "=" * 64)
    print("RÉSULTAT : lot conforme, prêt à être livré." if pb == 0
          else f"RÉSULTAT : {pb} point(s) à corriger avant livraison.")
    if not hist_dir:
        print("Astuce : ajouter --historique <dossier des lots> pour contrôler aussi")
        print("les contradictions avec les décisions déjà appliquées.")
    return 1 if pb else 0


if __name__ == '__main__':
    sys.exit(main())
