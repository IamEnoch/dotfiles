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
alias update='sudo apt update && sudo apt upgrade -y'

# PATH (ported from .bashrc / .profile)
export PATH="$HOME/.local/bin:$PATH"
export PATH="$PATH:/opt/flutter/bin"
export PATH="/snap/bin:$PATH"
export DOTNET_ROOT="$HOME/.dotnet"
export PATH="$DOTNET_ROOT:$PATH"
export PATH="$PATH:$HOME/.dotnet/tools"
export PATH="/opt/android-studio/bin:$PATH"
export PATH="$HOME/.aspire/bin:$PATH"

# Homebrew
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"

# ASP.NET dev certs
export SSL_CERT_DIR="$HOME/.aspnet/dev-certs/trust:${SSL_CERT_DIR:-/etc/ssl/certs}"

# oh-my-posh prompt
eval "$(oh-my-posh init zsh --config ~/.config/oh-my-posh/jandedobbeleer.omp.json)"

# fzf - Ctrl+R (history), Ctrl+T (files), Alt+C (cd) + completion
source /usr/share/doc/fzf/examples/key-bindings.zsh
source /usr/share/doc/fzf/examples/completion.zsh

# zoxide - `z <partial>` to jump, `zi` for interactive picker
eval "$(zoxide init zsh)"

# Plugins - keep these LAST (syntax-highlighting must be last of the two)
source /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh
source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
