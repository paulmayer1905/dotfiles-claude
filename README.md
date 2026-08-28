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

## Remote Control — piloter Claude Code depuis le téléphone ou le navigateur

Remote Control connecte [claude.ai/code](https://claude.ai/code) ou l'app mobile Claude à une session Claude Code **qui tourne sur ta machine**. Le code, les fichiers et les MCP restent en local : le web et le mobile ne sont qu'une fenêtre sur la session locale.

À ne pas confondre avec Claude Code on the web (`claude --cloud`), où tout s'exécute dans une VM Anthropic à partir d'un clone GitHub.

### Prérequis

- Plan Pro, Max, Team ou Enterprise — une clé API ne suffit pas (se connecter via `/login`)
- Pas de `ANTHROPIC_BASE_URL` personnalisé, ni Bedrock / Vertex / Foundry
- Les variables `DISABLE_TELEMETRY`, `DO_NOT_TRACK`, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` et `DISABLE_GROWTHBOOK` doivent être absentes
- Le dossier du projet doit avoir été ouvert au moins une fois (dialogue de confiance accepté)

### Depuis l'extension VS Code

1. Ouvrir le dossier du projet dans VS Code (`Fichier > Ouvrir le dossier`)
2. Ouvrir le panneau Claude Code et taper `/remote-control` (ou `/rc`) dans la zone de saisie
3. Une bannière apparaît au-dessus de la zone de saisie avec l'état de la connexion, et l'URL de session est postée dans la conversation
4. Cliquer sur **claude.ai/code** dans la bannière, ou retrouver la session dans la liste sur claude.ai/code ou l'app mobile (icône ordinateur + pastille verte)

Pour déconnecter : cliquer sur la croix de la bannière, ou retaper `/remote-control`.

La commande VS Code n'accepte pas de nom en argument et n'affiche pas de QR code (contrairement au CLI) ; le titre de la session vient de l'historique ou du premier prompt.

Pour activer automatiquement sur toutes les sessions : **Enable Remote Control for all sessions** dans la section Settings du menu `/` (Claude Code v2.1.203+).

### Depuis le terminal

| Commande | Usage |
|---|---|
| `claude --remote-control "Nom"` | session interactive au terminal, également pilotable à distance |
| `claude remote-control` | mode serveur : pas de saisie locale, plusieurs sessions, `espace` affiche un QR code |
| `/remote-control` (ou `/rc`) | active Remote Control sur une session déjà en cours, historique conservé |

Créer un nouveau projet et le rendre pilotable à distance :

```bash
mkdir C:/travail/mon-projet && cd C:/travail/mon-projet
git init
claude                       # 1er lancement : accepter le dialogue de confiance, puis /exit
claude --remote-control "Mon projet"
```

Quelques options utiles du mode serveur :

- `--spawn worktree` — chaque session distante obtient son propre git worktree (pas de conflit entre sessions parallèles)
- `--name "Mon projet"` — titre visible dans la liste des sessions
- `--continue` / `--session-id <id>` — récupérer les sessions d'un serveur arrêté (fenêtre d'environ 4 h)

### Activer par défaut sur toutes les sessions

Dans `~/.claude/settings.json` (donc dans ce repo, pour le garder sauvegardé) :

```json
"remoteControlAtStartup": true
```

Équivalent via l'interface : `/config` dans le CLI, **Settings > Claude Code > Enable remote control by default** dans l'app Desktop, ou la section Settings du menu `/` dans VS Code.

### Sécurité

La session locale n'ouvre aucun port entrant : elle fait uniquement des requêtes HTTPS sortantes vers l'API Anthropic. Tant que Remote Control est connecté, la transcription (messages, réponses, activité des outils) est stockée sur les serveurs Anthropic pour synchroniser les appareils ; l'exécution et l'accès aux fichiers restent sur la machine.

Documentation : <https://code.claude.com/docs/en/remote-control>
