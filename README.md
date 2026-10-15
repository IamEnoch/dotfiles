# Dotfiles

Configuration files for a Pop!_OS / Ubuntu development environment.

## Contents

This repository contains configuration files for:

- **Zsh** – Shell config: aliases, PATH, history, completion, fzf, zoxide, oh-my-posh
- **Neovim** – NvChad-derived editor config
- **WezTerm** – Terminal emulator
- **oh-my-posh** – Prompt theme (Jan De Dobbeleer)
- **CopyQ** – Clipboard history manager, autostarted for desktop sessions
- **Dotfiles CLI** – Setup, health checks, status, updates, and cleanup through `dotfiles`
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
├── copyq/
│   └── .config/autostart/
│       └── com.github.hluk.copyq.desktop            # Start clipboard history on login
├── nvim/
│   └── .config/nvim/                                # Neovim (NvChad) config tree
├── omp/
│   └── .config/oh-my-posh/jandedobbeleer.omp.json   # Prompt theme
├── system/
│   └── .local/bin/                                 # CLI and maintenance scripts
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

- Install system packages via apt: `stow`, `git`, `curl`, `build-essential`, `zsh`, `zsh-autosuggestions`, `zsh-syntax-highlighting`, `fzf`, `zoxide`, `eza`, `bat`, `ripgrep`, `fd-find`, `neovim`, `gh`, `copyq`, `wl-clipboard`, `fontconfig`, `unzip`
- Install WezTerm if its apt repository is already configured; otherwise print its installation link
- Install oh-my-posh and the MesloLGS Nerd Font
- Install Node.js + npm (if missing)
- Install the Codex CLI into `~/.local` via npm without sudo (if missing)
- Install Claude Code via the upstream installer
- Install the `dotnet-ef` global tool (only if `dotnet` is already on the box)
- Set zsh as the default login shell
- Check for Stow conflicts before creating symlinks under `$HOME`

Run the installer as your normal user. It requests sudo for system package installs. If dependencies are already installed, use `./install.sh --stow-only`.

The NvChad configuration uses `vim.lsp.enable`, which requires Neovim 0.11 or newer. Ubuntu 24.04 ships an older version; configure an appropriate Neovim package source or install a current release before using this editor configuration. The installer does not add third-party apt sources automatically.

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
   stow -vt ~ agents claude copyq nvim omp wezterm zsh system
   ```

   ```bash
   # Or install specific configurations
   stow -vt ~ agents
   stow -vt ~ claude
   stow -vt ~ copyq
   stow -vt ~ nvim
   stow -vt ~ omp
   stow -vt ~ wezterm
   stow -vt ~ zsh
   stow -vt ~ system
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

Skills are installed via [`npx skills`](https://github.com/vercel-labs/skills) and land in `~/.agents/skills/` (which stow points back into this repo). The `~/.claude/skills` symlink exposes the same store to Claude Code globally, and Codex also reads the shared store from this checkout.

Currently tracked skills include:

- `aspire` from `github/awesome-copilot` for .NET Aspire CLI, AppHost orchestration, dashboard, MCP, integrations, and deployment work.
- `find-docs` from `upstash/context7` for documentation lookup.
- `docx`, `frontend-design`, `next-best-practices`, `dotnet-backend-patterns`, `nuget-manager`, `excalidraw-diagram`, `supabase-postgres-best-practices`, `svg-logo-designer`, and `to-prd`.

### Update workflow

For routine updates, use the short path:

```bash
cd ~/dotfiles
npx skills update -g -y
npx skills list -g --json
git diff -- agents/.agents
```

If the updater says a skill was deleted upstream, it skips deletion in non-interactive mode. Review those skills manually before removing anything, because some local skills may still be useful even if the source repo moved or changed layout.

Validate skill metadata before committing:

```bash
tmpdir=$(mktemp -d /tmp/skill-validate.XXXXXX)
python3 -m venv "$tmpdir/venv"
"$tmpdir/venv/bin/python" -m pip install --quiet PyYAML

for d in agents/.agents/skills/*; do
  [ -f "$d/SKILL.md" ] || continue
  "$tmpdir/venv/bin/python" "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" "$d"
done

rm -rf "$tmpdir"
```

Keep only files that are part of the skill itself: `SKILL.md`, `references/`, `scripts/`, `assets/`, licenses, and lockfile data. Do not commit generated caches, virtualenvs, or upstream changelogs unless they are required by the skill at runtime.

Other useful commands:

```bash
# Add a skill
npx skills add <org/repo> -g -s <skill-name> -a claude-code -a codex -y

# Restore tracked skills from the lockfile on a new machine
npx skills experimental_install

# Verify installed global skills
npx skills list -g
```

After adding/updating, commit the changes in `agents/.agents/`.

## Private machine configuration

Git configuration, identities, signing keys, credentials, and trust settings are
outside this public repository. The installer does not create or change them.
`git/`, `.gitconfig`, and `.config/git/` are ignored. Keep your local Git setup
in regular files under your home directory; do not point it at a missing package
in this checkout.

## Dotfiles CLI

The `system` package installs the `dotfiles` command into `~/.local/bin`. The CLI
uses this checkout directly, including when invoked through a Stow symlink.

```bash
dotfiles doctor                   # Check tools and optional integrations; no changes
dotfiles status                   # Show checkout state and configuration links
dotfiles link --dry-run           # Preview links and report conflicts
dotfiles link                     # Link configs without installing dependencies
dotfiles install                  # Install dependencies and link configs
dotfiles update --dry-run         # Preview package updates and cleanup
dotfiles clean --dry-run          # Preview cleanup
dotfiles help update              # Show update options
dotfiles help clean               # Show cleanup options
```

`doctor` returns a nonzero exit code when required tools are missing. Optional
tools are reported separately. `status` reports existing files and links without
replacing them. `link` checks for conflicts before creating links; it never adopts
or overwrites existing regular files. Dependency installation has no dry run;
use `link --dry-run` to preview configuration linking only.

The original `update_system.sh` and `clean_system.sh` entry points remain
available. New shells also provide `update` and `clean` aliases through the CLI.

### System maintenance

Run the CLI and maintenance scripts as your normal user, without
prefixing the scripts with sudo; privileged commands request sudo internally.

```bash
update --dry-run                 # Preview updates and cleanup
update                           # apt upgrade, Snap, Flatpak, Homebrew, then cleanup
update --no-clean                # Update without cleanup/autoremove
update --skip-brew               # Skip Homebrew updates and cleanup
update --full-upgrade            # Explicitly allow apt package removals
update --include-npm             # Also update global npm packages
update --include-pip             # Also update user pip packages, if Python permits it
clean --dry-run                  # Preview cleanup
clean --empty-trash              # Explicitly and permanently empty Trash too
clean --journal-age 14d          # Keep two weeks of archived journal logs
clean --skip-journal             # Preserve journal logs
```

Cleanup removes unused apt packages, apt download caches, thumbnails, archived
journal logs older than seven days, unused Flatpak runtimes, Snap download cache,
and old Homebrew downloads/versions. Trash is preserved by default. Individual
cleanup stages have skip flags; use `clean --help` for the complete list.

Dry runs print the commands without performing updates, querying package indexes,
or deleting files. They are previews, not dependency-resolution simulations.
Pip, global npm, and Pop!_OS release upgrades remain opt-in. Externally managed
Python installations may reject user pip upgrades; the script reports the failure
and does not bypass Python's package protections. A failed stage stops the run.
Native Claude Code, .NET tools, editor plugins, and shared agent skills have their
own update workflows; they are not upgraded by this script.

The scripts resolve sibling files through symlinks, so an existing
`~/update_system.sh` or `~/clean_system.sh` can link to its counterpart in
`~/.local/bin` rather than keeping a separate copy.

Run the isolated checks with:

```bash
python3 -m unittest discover -s tests -v
```

The checks use temporary home directories and mocked package managers. They do
not perform actual system maintenance or validate a fresh-machine installation.

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
stow -Dvt ~ copyq
stow -Dvt ~ system

# Or uninstall all packages at once
stow -Dvt ~ agents claude copyq nvim omp wezterm zsh system
```
