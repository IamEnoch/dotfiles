# Dotfiles

Configuration files for a Pop!_OS / Ubuntu development environment.

## Contents

This repository contains configuration files for:

- **Zsh** – Shell config: aliases, PATH, history, completion, fzf, zoxide, oh-my-posh
- **Neovim** – NvChad-derived editor config
- **WezTerm** – Terminal emulator
- **oh-my-posh** – Prompt theme (Jan De Dobbeleer)
- **Agent skills** – Shared skill store under `~/.agents/skills/`, surfaced to Claude Code via `~/.claude/skills`. Managed with [`npx skills`](https://github.com/vercel-labs/skills); lockfile committed for reproducible installs.

VS Code is intentionally not tracked here — its built-in Settings Sync handles that in the cloud.

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

Replace `YOUR_GITHUB_USERNAME` with the repository owner, then clone and run the installation script:

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/dotfiles.git ~/dotfiles
cd ~/dotfiles
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
   git clone https://github.com/YOUR_GITHUB_USERNAME/dotfiles.git ~/dotfiles
   cd ~/dotfiles
   ```

2. Install whatever packages you actually use (see `install.sh` for the full list).

3. Use stow to symlink configs into your home directory:

   ```bash
   # Install all configurations
   stow -vt ~ agents claude nvim omp wezterm zsh
   ```

   ```bash
   # Or install specific configurations
   stow -vt ~ agents
   stow -vt ~ claude
   stow -vt ~ nvim
   stow -vt ~ omp
   stow -vt ~ wezterm
   stow -vt ~ zsh
   ```

   - `-t ~` = target is your home folder (where symlinks will be created)
   - `-v` = verbose output so you can see what's happening

   If any of the destination paths already exist as regular files (e.g.
   `~/.zshrc`), move or remove them before running `stow`
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

## Uninstallation

To remove symlinks created by stow:

```bash
cd ~/dotfiles
stow -Dvt ~ agents
stow -Dvt ~ claude
stow -Dvt ~ nvim
stow -Dvt ~ omp
stow -Dvt ~ wezterm
stow -Dvt ~ zsh

# Or uninstall all packages at once
stow -Dvt ~ agents claude nvim omp wezterm zsh
```
