# dotfiles-claude

Backup de ma configuration Claude Code (`~/.claude/`).

## Contenu

- **`skills/`** — Skills installés pour Claude Code
- **`settings.json`** — Permissions, modèle par défaut, niveau d'effort

## Sources des skills

| Dossier | Source |
|---------|--------|
| `bmad-*` (43 skills) | [BMad Method](https://github.com/bmadcode/BMAD-METHOD) — framework agents/workflows produit |
| `ui-ux-pro-max` | [ui-ux-pro-max](https://github.com/saliftankoano/ui-ux-pro-max) — design intelligence pour UI/UX |

## Restauration

```bash
# Cloner le repo
git clone https://github.com/paulmayer1905/dotfiles-claude.git

# Copier les skills
cp -r dotfiles-claude/skills/ ~/.claude/skills/

# Copier les settings (attention : écraser les settings existants)
cp dotfiles-claude/settings.json ~/.claude/settings.json
```

## Fichiers exclus (ne pas committer)

- `.credentials.json` — tokens d'authentification
- `sessions/` — historique de conversations
- `telemetry/` — données de télémétrie
- `plans/` — plans temporaires
- `shell-snapshots/` — snapshots shell
