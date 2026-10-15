# History
HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000
setopt HIST_IGNORE_DUPS HIST_IGNORE_SPACE SHARE_HISTORY APPEND_HISTORY

# Completion
autoload -Uz compinit && compinit
zstyle ':completion:*' menu select
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'

# Aliases (ported from .bashrc)
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias grep='grep --color=auto'
alias garage='cd ~/garage'
alias update='zotu update'
alias clean='zotu clean'

# Keep PATH entries unique when reloading this file.
typeset -U path PATH
path=("$HOME/.local/bin" $path /opt/flutter/bin /snap/bin)
export DOTNET_ROOT="$HOME/.dotnet"
path=("$DOTNET_ROOT" "$HOME/.aspire/bin" /opt/android-studio/bin $path "$HOME/.dotnet/tools")

# Homebrew
if [[ -x /home/linuxbrew/.linuxbrew/bin/brew ]]; then
  eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
fi

# ASP.NET dev certs
if [[ ":${SSL_CERT_DIR:-}:" != *":$HOME/.aspnet/dev-certs/trust:"* ]]; then
  export SSL_CERT_DIR="$HOME/.aspnet/dev-certs/trust:${SSL_CERT_DIR:-/etc/ssl/certs}"
fi

# oh-my-posh prompt
if (( $+commands[oh-my-posh] )); then
  eval "$(oh-my-posh init zsh --config ~/.config/oh-my-posh/jandedobbeleer.omp.json)"
fi

# fzf - Ctrl+R (history), Ctrl+T (files), Alt+C (cd) + completion
if [[ -r /usr/share/doc/fzf/examples/key-bindings.zsh ]]; then
  source /usr/share/doc/fzf/examples/key-bindings.zsh
fi
if [[ -r /usr/share/doc/fzf/examples/completion.zsh ]]; then
  source /usr/share/doc/fzf/examples/completion.zsh
fi

# zoxide - `z <partial>` to jump, `zi` for interactive picker
if (( $+commands[zoxide] )); then
  eval "$(zoxide init zsh)"
fi

# Plugins - keep these LAST (syntax-highlighting must be last of the two)
if [[ -r /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh ]]; then
  source /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh
fi
if [[ -r /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]]; then
  source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
fi
