# Dotfiles

Personal configuration files for my Pop!_OS / Ubuntu development environment.

## Contents

This repository contains configuration files for:

- **Zsh** – Shell config: aliases, PATH, history, completion, fzf, zoxide, oh-my-posh
- **Git** – Identity, GPG/SSH commit signing, gh credential helper, LFS
- **Neovim** – NvChad-derived editor config
- **WezTerm** – Terminal emulator
- **oh-my-posh** – Prompt theme (Jan De Dobbeleer)
- **Agent skills** – Shared skill store under `~/.agents/skills/`, surfaced to Claude Code via `~/.claude/skills`. Managed with [`npx skills`](https://github.com/vercel-labs/skills); lockfile committed for reproducible installs.

## Structure

```text
dotfiles/
├── agents/
│   └── .agents/
│       ├── .skill-lock.json                         # npx skills lockfile
│       └── skills/                                  # Installed agent skills
├── claude/
│   └── .claude/
│       └── skills -> ../../agents/.agents/skills    # Symlink to shared store
├── git/
│   └── .gitconfig                                   # Git config (signing, LFS, identity)
├── nvim/
│   └── .config/nvim/                                # Neovim (NvChad) config tree
├── omp/
│   └── .config/oh-my-posh/jandedobbeleer.omp.json   # Prompt theme
├── wezterm/
│   └── .wezterm.lua                                 # WezTerm config
└── zsh/
    └── .zshrc                                       # Zsh shell config
```

## Installation

This repository uses [GNU Stow](https://www.gnu.org/software/stow/) for managing symlinks.

### Quick install (recommended)

Clone the repository and run the installation script:

```bash
git clone git@github.com:IamEnoch/dotfiles.git ~/garage/personal/personalprojects/dotfiles
cd ~/garage/personal/personalprojects/dotfiles
chmod +x install.sh
./install.sh
```

The installation script will:

- Install system packages via apt: `stow`, `git`, `curl`, `build-essential`, `zsh`, `zsh-autosuggestions`, `zsh-syntax-highlighting`, `fzf`, `zoxide`, `eza`, `bat`, `ripgrep`, `fd-find`, `neovim`, `wezterm`, `gh`
- Install oh-my-posh and the MesloLGS Nerd Font
- Install Node.js + npm (if missing)
- Install the Codex CLI globally via npm
- Install Claude Code via the upstream installer
- Install the `dotnet-ef` global tool (only if `dotnet` is already on the box)
- Set zsh as the default login shell
- Run `stow` to create all symlinks under `$HOME`

### Manual installation

If you prefer to install components manually:

#### Prerequisites

```bash
sudo apt install stow
```

#### Setup

1. Clone the repository (anywhere; the path doesn't matter to stow):

   ```bash
   git clone git@github.com:IamEnoch/dotfiles.git ~/garage/personal/personalprojects/dotfiles
   cd ~/garage/personal/personalprojects/dotfiles
   ```

2. Install whatever packages you actually use (see `install.sh` for the full list).

3. Use stow to symlink configs into your home directory:

   ```bash
   # Install all configurations
   stow -vt ~ agents claude git nvim omp wezterm zsh
   ```

   ```bash
   # Or install specific configurations
   stow -vt ~ agents
   stow -vt ~ claude
   stow -vt ~ git
   stow -vt ~ nvim
   stow -vt ~ omp
   stow -vt ~ wezterm
   stow -vt ~ zsh
   ```

   - `-t ~` = target is your home folder (where symlinks will be created)
   - `-v` = verbose output so you can see what's happening

   If any of the destination paths already exist as regular files (e.g.
   `~/.zshrc` or `~/.gitconfig`), move or remove them before running `stow`
   so it does not fail with conflicts.

4. Restart your terminal or source the configurations:

   ```bash
   exec zsh
   ```

## Managing agent skills

Skills are installed via [`npx skills`](https://github.com/vercel-labs/skills) and land in `~/.agents/skills/` (which stow points back into this repo). The `~/.claude/skills` symlink exposes the same store to Claude Code globally.

```bash
# Add a skill
npx skills add <org/repo> -g -s <skill-name> -a claude-code -a codex -y

# Update all installed skills
npx skills update -g -y

# List installed skills
npx skills list
```

After adding/updating, commit the changes in `agents/.agents/`.

## Per-machine state (not tracked)

Some files belong on the machine but not in version control:

- `~/.config/git/config` – holds `safe.directory = *` for repos on root-owned mounts
- `~/.config/git/allowed_signers` – maps email → SSH pubkey for local signature verification
- `~/.ssh/git_signing_ed25519{,.pub}` – generated fresh per machine

Generate a fresh signing key on a new machine:

```bash
ssh-keygen -t ed25519 -C "your.email@example.com" -f ~/.ssh/git_signing_ed25519 -N ""
gh ssh-key add ~/.ssh/git_signing_ed25519.pub --type signing --title "$(hostname) - git signing"
echo "your.email@example.com $(awk '{print $1, $2}' ~/.ssh/git_signing_ed25519.pub)" \
  >> ~/.config/git/allowed_signers
```

## Uninstallation

To remove symlinks created by stow:

```bash
cd ~/garage/personal/personalprojects/dotfiles
stow -Dvt ~ agents
stow -Dvt ~ claude
stow -Dvt ~ git
stow -Dvt ~ nvim
stow -Dvt ~ omp
stow -Dvt ~ wezterm
stow -Dvt ~ zsh

# Or uninstall all packages at once
stow -Dvt ~ agents claude git nvim omp wezterm zsh
```
