# dotfiles-claude

Backup de ma configuration Claude Code (`~/.claude/`).

## Contenu

- **`skills/`** — Skills installés pour Claude Code
- **`settings.json`** — Permissions, modèle par défaut, niveau d'effort
- **`mcp-config.json`** — Configuration des serveurs MCP (GitHub, Figma, n8n)

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

### Restauration des MCP servers

Le fichier `mcp-config.json` contient le bloc `mcpServers` à intégrer dans `~/.claude.json` (fichier de config utilisateur Claude Code).

1. Ouvrir `~/.claude.json` (le créer s'il n'existe pas)
2. Copier-coller le contenu de `mcp-config.json` dans le fichier, au niveau racine
3. Configurer les variables d'environnement référencées :

**Windows (PowerShell) :**
```powershell
[System.Environment]::SetEnvironmentVariable('GITHUB_PERSONAL_ACCESS_TOKEN', '<ton_token>', 'User')
```

**Linux/macOS :**
```bash
echo 'export GITHUB_PERSONAL_ACCESS_TOKEN="<ton_token>"' >> ~/.bashrc
source ~/.bashrc
```

4. Pour n8n : remplacer `YOUR_N8N_MCP_URL` et `YOUR_N8N_BEARER_TOKEN` par les valeurs de ton instance n8n
5. Pour Figma : aucune variable à configurer, mais OAuth browser-based au premier usage
6. Relancer Claude Code pour charger les MCP

## Fichiers exclus (ne pas committer)

- `.credentials.json` — tokens d'authentification
- `sessions/` — historique de conversations
- `telemetry/` — données de télémétrie
- `plans/` — plans temporaires
- `shell-snapshots/` — snapshots shell
- `.claude.json` — config utilisateur (contient des données sensibles, utiliser `mcp-config.json` à la place)
