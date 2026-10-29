#!/usr/bin/env bash
# Bootstrap a fresh Pop!_OS / Ubuntu box with my dev environment.
# Idempotent: safe to re-run, skips anything already installed.

set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGES=(zsh nvim wezterm omp agents claude copyq hokum system)
STOW_ONLY=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
case "$1" in
  --stow-only) STOW_ONLY=true ;;
  -n|--dry-run) DRY_RUN=true ;;
  -h|--help)
    echo "Usage: ${0##*/} [--stow-only [--dry-run]]"
    echo "Install dependencies and symlink public configs, or only symlink existing configs."
    echo "--dry-run previews Stow links and requires --stow-only."
    exit 0
    ;;
  *) echo "Unknown argument: $1" >&2; exit 1 ;;
esac
shift
done
if "$DRY_RUN" && ! "$STOW_ONLY"; then
  echo "Use --stow-only with --dry-run; dependency installation has no dry-run." >&2
  exit 1
fi
[[ $EUID -ne 0 ]] || { echo "Run as your normal user, without sudo." >&2; exit 1; }
export PATH="$HOME/.local/bin:$PATH"

for package in "${PACKAGES[@]}"; do
  [[ -d "$DOTFILES_DIR/$package" ]] || { echo "Missing Stow package: $package" >&2; exit 1; }
done

stow_configs() {
  # Check all conflicts before creating any links; never adopt private files.
  stow --simulate --verbose --target="$HOME" --dir="$DOTFILES_DIR" "${PACKAGES[@]}"
  if ! "$DRY_RUN"; then
    stow --verbose --target="$HOME" --dir="$DOTFILES_DIR" "${PACKAGES[@]}"
  fi
}

if "$STOW_ONLY"; then
  stow_configs
  exit 0
fi

echo "Starting dotfiles installation from $DOTFILES_DIR"

# 1. apt packages
echo "Installing system packages..."
sudo apt update
sudo apt install -y \
  stow git curl ca-certificates build-essential fontconfig unzip \
  zsh zsh-autosuggestions zsh-syntax-highlighting \
  fzf zoxide eza bat ripgrep fd-find \
  neovim gh \
  copyq wl-clipboard

# WezTerm needs its upstream apt repository on a fresh Ubuntu installation.
if ! command -v wezterm &>/dev/null; then
  if apt-cache show wezterm >/dev/null 2>&1; then
    sudo apt install -y wezterm
  else
    echo "WezTerm unavailable in configured apt sources; install it from https://wezterm.org/install/linux.html"
  fi
fi

# 2. oh-my-posh
if ! command -v oh-my-posh &>/dev/null; then
  echo "Installing oh-my-posh..."
  mkdir -p "$HOME/.local/bin"
  curl -fsSL https://ohmyposh.dev/install.sh | bash -s -- -d "$HOME/.local/bin"
fi

# 3. nerd font
if ! fc-list | grep -qi "MesloLGS"; then
  echo "Installing MesloLGS Nerd Font..."
  oh-my-posh font install meslo
fi

# 4. node + npm
if ! command -v node &>/dev/null || ! command -v npm &>/dev/null; then
  echo "Installing Node.js + npm..."
  sudo apt install -y nodejs npm
fi

# 5. codex cli (standalone binary, so Node/OpenSSL upgrades cannot break it)
if ! command -v codex &>/dev/null; then
  echo "Installing Codex CLI..."
  if command -v brew &>/dev/null; then
    brew install --cask codex
  else
    case "$(uname -m)" in
      x86_64) codex_target=x86_64-unknown-linux-musl ;;
      aarch64|arm64) codex_target=aarch64-unknown-linux-musl ;;
      *) echo "Unsupported architecture for Codex CLI: $(uname -m)" >&2; exit 1 ;;
    esac
    mkdir -p "$HOME/.local/bin"
    curl -fsSL "https://github.com/openai/codex/releases/latest/download/codex-$codex_target.tar.gz" \
      | tar -xzO "codex-$codex_target" > "$HOME/.local/bin/codex"
    chmod +x "$HOME/.local/bin/codex"
  fi
fi

# 6. hokum notification daemon (COSMIC hands it the slot via hokum/.local/bin/cosmic-notifications)
HOKUM_VERSION=0.1.2
if ! command -v hokum &>/dev/null; then
  case "$(uname -m)" in
    x86_64) hokum_arch=x64 ;;
    aarch64|arm64) hokum_arch=arm64 ;;
    *) hokum_arch="" ;;
  esac
  if [[ -n "$hokum_arch" ]]; then
    echo "Installing Hokum $HOKUM_VERSION..."
    mkdir -p "$HOME/.local/bin"
    curl -fsSL -o "$HOME/.local/bin/hokum" \
      "https://github.com/anomalyco/hokum/releases/download/v$HOKUM_VERSION/hokum-$HOKUM_VERSION-linux-$hokum_arch"
    chmod +x "$HOME/.local/bin/hokum"
  else
    echo "Hokum has no build for $(uname -m), skipping"
  fi
fi

# 7. claude code
if ! command -v claude &>/dev/null; then
  echo "Installing Claude Code..."
  curl -fsSL https://claude.ai/install.sh | bash
fi

# 8. dotnet-ef (skipped if dotnet missing)
if command -v dotnet &>/dev/null; then
  if ! dotnet tool list --global 2>/dev/null | grep -q '^dotnet-ef'; then
    echo "Installing dotnet-ef..."
    dotnet tool install --global dotnet-ef
  fi
else
  echo "dotnet not found, skipping dotnet-ef"
fi

# 9. default shell
if [ "$(getent passwd "$(id -un)" | awk -F: '{print $NF}')" != "$(command -v zsh)" ]; then
  echo "Setting default shell to zsh..."
  chsh -s "$(command -v zsh)"
fi

# 10. stow
echo "Stowing packages: ${PACKAGES[*]}"
stow_configs

echo "Done. Open a new terminal."
echo "Next: run 'codex' once to sign in (ChatGPT account or API key)."
