# -*- coding: utf-8 -*-
"""Contrôle d'un lot de passation avant livraison.

Usage :
    python controle_passation.py <operations.json> <delta.md> [autre.md ...]
                                 [--historique <dossier_des_lots_anterieurs>]
                                 [--backlog <backlog_consolide.md>]
                                 [--cr <fichier_ou_dossier_de_CR>]
                                 [--lisezmoi <LISEZMOI - Index des passations.md>]

Contrôles :
  1. cohérence .json -> .md (tout texte porteur de sens du JSON figure dans le MD)
  2. piège des valeurs citées (un texte ajouté cite une valeur remplacée globalement)
  3. numérotation des identifiants ajoutés (contiguïté)
  4. présence du bloc « Précautions », de la consigne de dry-run,
     et — si le lot modifie des tickets — de la règle du ticket gelé
  5. sections rédactionnelles périmées (un point listé « en attente » est tranché par le lot ;
     les textes marqués [À VALIDER] ne comptent pas comme tranchés)
  6. cohérence inter-lots (une décision antérieure appliquée est-elle contredite sans retrait ?)
  7. couverture : un objet d'interface nommé dans une décision est-il sujet d'une US ?
     (--backlog) Détecte l'objet cité de partout mais spécifié nulle part.
  8. points « à valider » des CR non suivis (--cr + --lisezmoi)

Sortie : rapport lisible + code retour 1 si au moins un point est à corriger.
"""
import sys, os, json, re, glob, unicodedata

CLES_TEXTE = ('with', 'find', 'description', 'Description', 'Summary')
CLES_LISTE = ('notes', 'objectifs', 'elementsAction')
OPS_RETRAIT = ('deleteLine', 'removeRule', 'removeSection', 'replaceText', 'setRuleDescription')
VIDES = {'les', 'des', 'une', 'aux', 'sur', 'pour', 'dans', 'que', 'qui', 'est', 'sont',
         'doit', 'application', 'veux', 'lorsque', 'avec', 'par', 'plus', 'tout', 'toutes'}

# Objets d'interface : un lot qui les nomme doit pouvoir les rattacher a une US.
OBJETS = ('panneau', 'encart', 'ecran', 'bouton', 'onglet', 'page', 'tableau de bord',
          'rubrique', 'sous-rubrique', 'champ', 'colonne', 'popin', 'pop-up',
          'boite de dialogue', 'bandeau', 'menu', 'formulaire', 'notification')
RE_OBJET = re.compile(
    r'\b(' + '|'.join(o.replace(' ', r'\s+').replace('-', r'[- ]') for o in OBJETS) +
    r')\b[^«"\n]{0,30}(?:«\s*([^»\n]{3,60}?)\s*»|"([^"\n]{3,60}?)")', re.I)

# Un objet que le lot RETIRE n'a pas besoin d'une US : on ne le signale pas.
RE_NEGATION = re.compile(
    r"(ne doit pas|ne doivent pas|ne soit pas|ne sont pas|n'affiche pas|sans |pas de |"
    r"retrait|retir[ée]|supprim[ée]|abandonn[ée]|ne propose pas|n'en comporte)", re.I)

# Marqueurs d'un point laisse en suspens dans un compte-rendu.
RE_SUSPENS = re.compile(
    r"([^.;|\n]{10,220}?(?:[àa]\s+valider|[àa]\s+confirmer|[àa]\s+trancher|"
    r"[àa]\s+arbitrer|[àa]\s+pr[ée]ciser|[àa]\s+d[ée]finir|"
    r"en\s+attente\s+de\s+r[ée]ponse|reste\s+[àa]\s+d[ée]finir|"
    r"question\s+ouverte)[^.;|\n]{0,140})", re.I)


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


def objets_nommes(textes):
    """[(type, nom)] — objets d'interface nommes dans les textes du lot."""
    vus, out = set(), []
    for t in textes:
        for m in RE_OBJET.finditer(unicodedata.normalize('NFKC', t)):
            typ = re.sub(r'\s+', ' ', m.group(1)).lower()
            nom = (m.group(2) or m.group(3) or '').strip()
            if len(nom) < 4 or norm(nom) in vus:
                continue
            # contexte immediat : un objet que le lot retire ne demande pas d'US.
            # La negation peut preceder l'objet (« ne doit pas proposer de bouton X »)
            # comme le suivre (« le bouton X soit supprime »).
            contexte = t[max(0, m.start() - 90):m.end() + 70]
            if RE_NEGATION.search(norm(contexte)):
                vus.add(norm(nom))
                continue
            vus.add(norm(nom))
            out.append((typ, nom))
    return out


def titres_backlog(chemin):
    """[(cle, titre)] — les US du backlog, reperees par leur ligne de titre."""
    if not chemin or not os.path.exists(chemin):
        return None
    brut = open(chemin, encoding='utf-8').read()
    res = []
    for l in brut.split('\n'):
        m = re.match(r'^#{2,4}\s+((?:TE_OPUR-)?\d*)\s*[—-]?\s*(.+?)\s*$', l)
        if m and m.group(2) and not l.startswith('#####'):
            res.append((m.group(1) or '?', m.group(2)))
    return res, brut


def main():
    args = [a for a in sys.argv[1:]]
    hist_dir = None
    backlog = cr_path = lisezmoi = None
    for drapeau in ('--historique', '--backlog', '--cr', '--lisezmoi'):
        if drapeau in args:
            i = args.index(drapeau)
            val = args[i + 1] if i + 1 < len(args) else None
            del args[i:i + 2]
            if drapeau == '--historique':
                hist_dir = val
            elif drapeau == '--backlog':
                backlog = val
            elif drapeau == '--cr':
                cr_path = val
            else:
                lisezmoi = val
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
    # un lot qui modifie des tickets doit prevoir le cas du ticket gele
    modifie = bool(data.get('operations'))
    a_gel = bool(re.search(
        r"(ticket gel[ée]|tickets gel[ée]s|en cours de d[ée]veloppement|\bin dev\b"
        r"|US de compl[ée]ment|story de compl[ée]ment|relever le statut|statut du ticket"
        r"|statut de chaque ticket)", txt, re.I))
    mention_gel = "sans objet (aucune modification de ticket)" if not modifie else ("oui" if a_gel else "NON")
    print(f"[4] Bloc « Précautions » : {'oui' if a_prec else 'NON'}   |   dry-run : {'oui' if a_dry else 'NON'}"
          f"   |   ticket gelé : {mention_gel}")
    pb += (0 if a_prec else 1) + (0 if a_dry else 1)
    if modifie and not a_gel:
        print("      ! le lot modifie des tickets sans prévoir le cas du ticket en cours de développement")
        print("        -> ajouter la consigne : relever le statut, et créer une US de complément si le ticket est gelé")
        pb += 1

    # ---- 5. sections rédactionnelles périmées
    # une puce listée sous un titre « en attente / à valider » ne doit pas être traitée par le lot
    # Un point que le lot laisse explicitement ouvert ([À VALIDER]) n'est PAS tranché :
    # on retire ces lignes du corpus, sinon le lot se signale lui-même comme périmé.
    _textes = [t for c in cibles_du_lot(data).values() for t in c['textes']]
    _tranche = []
    for _t in _textes:
        for _l in _t.split('\n'):
            if not re.search(r"\[\s*(À|A)\s*VALIDER", _l, re.I):
                _tranche.append(_l)
    corpus_ops = norm(" ".join(_tranche))
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


    # ---- 7. couverture : objet nomme partout, specifie nulle part
    print("\n[7] Couverture des objets d'interface nommés :", end=" ")
    if not backlog:
        print("non contrôlée (passer --backlog <backlog consolidé.md>)")
    else:
        bl = titres_backlog(backlog)
        if bl is None:
            print(f"backlog introuvable ({backlog})")
        else:
            titres, brut_bl = bl
            # les US creees par le lot lui-meme comptent comme couverture
            for c in data.get('creations', []):
                s = c.get('fields', {}).get('Summary') or c.get('summary') or ''
                if s:
                    titres.append(('(ce lot)', s))
            corpus = norm(brut_bl)
            textes_lot = [v for _, v in frags_src] if 'frags_src' in dir() else []
            if not textes_lot:
                tmp = []
                collecte(data, tmp)
                textes_lot = [v for _, v in tmp]
            alertes7 = 0
            for typ, nom in objets_nommes(textes_lot):
                mn = mots(nom)
                if len(mn) < 1:
                    continue
                sujet = any(len(mn & mots(t)) >= min(2, len(mn)) for _, t in titres)
                if sujet:
                    continue
                cites = corpus.count(norm(nom))
                if cites > 0:
                    alertes7 += 1
                    print()
                    print(f"      ! {typ} « {nom} »")
                    print(f"        cité {cites} fois dans le backlog, sujet d'aucune US")
                    print(f"        -> soit créer l'US qui le spécifie, soit rattacher explicitement")
                    print(f"           la décision à une US existante")
            if alertes7 == 0:
                print("tout objet nommé est rattaché à une US")
            pb += alertes7

    # ---- 8. points « à valider » des CR non suivis
    print("[8] Points « à valider » des comptes-rendus :", end=" ")
    if not (cr_path and lisezmoi):
        print("non contrôlés (passer --cr <CR> et --lisezmoi <index>)")
    elif not os.path.exists(cr_path) or not os.path.exists(lisezmoi):
        print("chemin introuvable")
    else:
        fichiers = ([cr_path] if os.path.isfile(cr_path)
                    else glob.glob(os.path.join(cr_path, '**', '*.md'), recursive=True))
        suivi = norm(open(lisezmoi, encoding='utf-8').read())
        points, vus8 = [], set()
        for f in fichiers:
            try:
                brut8 = open(f, encoding='utf-8').read()
                contenu = norm(brut8.replace('<br>', '\n').replace('<BR>', '\n'))
            except Exception:
                continue
            for ligne in contenu.split('\n'):
              for m in RE_SUSPENS.finditer(ligne):
                p = re.sub(r'\s+', ' ', m.group(1)).strip(' -|*')
                if len(p) > 12 and p not in vus8:
                    vus8.add(p)
                    points.append((os.path.basename(f), p))
        non_suivis = []
        for f, p in points:
            mp = mots(p)
            if len(mp) < 3:
                continue
            # le point est-il repris dans l'index (points ouverts / etat) ?
            couvert = False
            for phrase in suivi.split('\n'):
                if len(mots(phrase) & mp) >= max(3, len(mp) // 3):
                    couvert = True
                    break
            if not couvert:
                non_suivis.append((f, p))
        if not points:
            print("aucun point en suspens détecté dans les CR")
        elif not non_suivis:
            print(f"{len(points)} point(s) détecté(s), tous repris dans l'index")
        else:
            print(f"{len(points)} détecté(s), {len(non_suivis)} NON repris dans l'index")
            for f, p in non_suivis[:12]:
                print(f"      ! {p[:150]}")
                print(f"        ({f})")
            if len(non_suivis) > 12:
                print(f"      … et {len(non_suivis) - 12} autre(s)")
            print("      -> ajouter ces points aux « Points ouverts » du LISEZMOI,")
            print("         ou les clore explicitement.")
            pb += len(non_suivis)

    print("\n" + "=" * 64)
    print("RÉSULTAT : lot conforme, prêt à être livré." if pb == 0
          else f"RÉSULTAT : {pb} point(s) à corriger avant livraison.")
    manquants = [d for d, v in (('--historique', hist_dir), ('--backlog', backlog),
                                ('--cr', cr_path), ('--lisezmoi', lisezmoi)) if not v]
    if manquants:
        print("Astuce : contrôles non exécutés faute d'argument -> " + ", ".join(manquants))
    return 1 if pb else 0


if __name__ == '__main__':
    sys.exit(main())
