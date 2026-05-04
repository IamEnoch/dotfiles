#!/usr/bin/env bash
# Bootstrap a fresh Pop!_OS / Ubuntu box with my dev environment.
# Idempotent: safe to re-run, skips anything already installed.

set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGES=(zsh git nvim wezterm omp agents claude)

echo "Starting dotfiles installation from $DOTFILES_DIR"

# 1. apt packages
echo "Installing system packages..."
sudo apt update
sudo apt install -y \
  stow git curl ca-certificates build-essential \
  zsh zsh-autosuggestions zsh-syntax-highlighting \
  fzf zoxide eza bat ripgrep fd-find \
  neovim wezterm gh

# 2. oh-my-posh
if ! command -v oh-my-posh &>/dev/null; then
  echo "Installing oh-my-posh..."
  curl -s https://ohmyposh.dev/install.sh | sudo bash -s
fi

# 3. nerd font
if ! fc-list | grep -qi "MesloLGS"; then
  echo "Installing MesloLGS Nerd Font..."
  oh-my-posh font install meslo
fi

# 4. node + npm
if ! command -v npm &>/dev/null; then
  echo "Installing Node.js + npm..."
  sudo apt install -y nodejs npm
fi

# 5. codex cli
if ! command -v codex &>/dev/null; then
  echo "Installing Codex CLI..."
  sudo npm install -g @openai/codex
fi

# 6. claude code
if ! command -v claude &>/dev/null; then
  echo "Installing Claude Code..."
  curl -fsSL https://claude.ai/install.sh | bash
fi

# 7. dotnet-ef (skipped if dotnet missing)
if command -v dotnet &>/dev/null; then
  if ! dotnet tool list --global 2>/dev/null | grep -q '^dotnet-ef'; then
    echo "Installing dotnet-ef..."
    dotnet tool install --global dotnet-ef
  fi
else
  echo "dotnet not found, skipping dotnet-ef"
fi

# 8. default shell
if [ "$(getent passwd "$USER" | awk -F: '{print $NF}')" != "$(which zsh)" ]; then
  echo "Setting default shell to zsh..."
  chsh -s "$(which zsh)"
fi

# 9. stow
echo "Stowing packages: ${PACKAGES[*]}"
cd "$DOTFILES_DIR"
stow -vt "$HOME" "${PACKAGES[@]}"

echo "Done. Open a new terminal."
echo "Next: run 'codex' once to sign in (ChatGPT account or API key)."
