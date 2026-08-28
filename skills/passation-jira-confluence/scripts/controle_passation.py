# -*- coding: utf-8 -*-
"""Contrôle d'un lot de passation avant livraison.

Usage :
    python controle_passation.py <operations.json> <delta.md> [autre.md ...]

Vérifie :
  1. cohérence .json -> .md (tout texte porteur de sens du JSON figure dans le MD)
  2. piège des valeurs citées (un texte ajouté cite une valeur remplacée globalement)
  3. numérotation des identifiants ajoutés (contiguïté)
  4. présence du bloc « Précautions » et de la consigne de dry-run

Sortie : rapport lisible + code retour 1 si au moins un problème bloquant.
"""
import sys, os, json, re, unicodedata

CLES_TEXTE = ('with', 'find', 'description', 'Description', 'Summary')
CLES_LISTE = ('notes', 'objectifs', 'elementsAction')


def norm(s: str) -> str:
    s = unicodedata.normalize('NFKC', s)
    s = (s.replace('’', "'").replace('«', '"').replace('»', '"')
           .replace('—', '-').replace('–', '-'))
    return re.sub(r'\s+', ' ', s).strip().lower()


def collecte(obj, out):
    """Récupère (clé, texte) pour tout fragment porteur de sens."""
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


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    js, mds = sys.argv[1], sys.argv[2:]
    data = json.load(open(js, encoding='utf-8'))
    md_txt = "\n".join(open(m, encoding='utf-8').read() for m in mds if os.path.exists(m))
    if not md_txt:
        print("ERREUR : aucun .md lisible."); return 2
    txt = norm(md_txt)
    pb = 0

    # ---- 1. cohérence json -> md
    frags = []
    for cle in ('globalOperations', 'operations', 'modifications', 'creations'):
        if cle in data:
            collecte(data[cle], frags)
    manquants = [(k, v) for k, v in frags if norm(v)[:55] and norm(v)[:55] not in txt]
    print(f"[1] Cohérence .json -> .md : {len(frags)} fragments contrôlés, {len(manquants)} absent(s)")
    for k, v in manquants[:10]:
        print(f"      - ({k}) {v[:100]}...")
    pb += len(manquants)

    # ---- 2. piège des valeurs citées
    anciens = [g.get('find', '') for g in data.get('globalOperations', []) if g.get('find')]
    pieges = []
    for cle in ('operations', 'modifications'):
        for item in data.get(cle, []):
            for e in item.get('edits', []) + item.get('operations', []):
                texte = e.get('with', '') or e.get('description', '')
                if not texte or e.get('excludeFromGlobalOperations'):
                    continue
                for a in anciens:
                    if a and a in texte:
                        pieges.append((item.get('issueKey') or item.get('title'), a, e.get('reason', '')[:40]))
    print(f"[2] Valeurs remplacées citées dans un texte ajouté : {len(pieges)}")
    for cible, val, r in pieges[:10]:
        print(f"      ! {cible} cite « {val} »  ({r})")
        print(f"        -> ajouter \"excludeFromGlobalOperations\": true sur cet edit")
    pb += len(pieges)

    # ---- 3. numérotation
    print("[3] Numérotation des identifiants ajoutés :")
    for item in data.get('modifications', []):
        nums = []
        for o in item.get('operations', []):
            m = re.search(r'#\w*?(\d+)\s*$', o.get('uniqueId', '') or '')
            if m and o.get('op') == 'addRule':
                nums.append(int(m.group(1)))
        if nums:
            trous = [n for n in range(min(nums), max(nums) + 1) if n not in nums]
            etat = f"TROU {trous}" if trous else "contigus"
            if trous:
                pb += 1
            print(f"      {item.get('title', '?'):34} {sorted(nums)}  {etat}")

    # ---- 4. précautions et dry-run
    a_prec = 'précaution' in txt or 'precaution' in txt
    a_dry = 'dry-run' in txt or 'dry run' in txt
    print(f"[4] Bloc « Précautions » présent : {'oui' if a_prec else 'NON'}"
          f"   |   consigne de dry-run : {'oui' if a_dry else 'NON'}")
    if not a_prec:
        pb += 1
    if not a_dry:
        pb += 1

    print("\n" + "=" * 62)
    if pb == 0:
        print("RÉSULTAT : lot conforme, prêt à être livré.")
    else:
        print(f"RÉSULTAT : {pb} point(s) à corriger avant livraison.")
    print("Rappel — à vérifier à la main : sections rédactionnelles (points validés /")
    print("en attente, contexte) et opérations de retrait si une décision antérieure")
    print("déjà appliquée est annulée.")
    return 1 if pb else 0


if __name__ == '__main__':
    sys.exit(main())
