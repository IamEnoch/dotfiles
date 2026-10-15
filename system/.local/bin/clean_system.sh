#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

DRY_RUN=false
JOURNAL_AGE="7d"
SKIP_APT=false
SKIP_JOURNAL=false
SKIP_FLATPAK=false
SKIP_SNAP=false
SKIP_BREW=false
SKIP_THUMBNAILS=false
EMPTY_TRASH=false

if [[ -t 1 ]] && command -v tput >/dev/null 2>&1; then
  RED="$(tput setaf 1 || true)"
  GREEN="$(tput setaf 2 || true)"
  YELLOW="$(tput setaf 3 || true)"
  BLUE="$(tput setaf 4 || true)"
  RESET="$(tput sgr0 || true)"
else
  RED=""
  GREEN=""
  YELLOW=""
  BLUE=""
  RESET=""
fi

log() { printf '%s %s\n' "$(date +'%Y-%m-%d %H:%M:%S')" "$*"; }
info() { log "${BLUE}->${RESET} $*"; }
success() { log "${GREEN}OK${RESET} $*"; }
warn() { log "${YELLOW}WARN${RESET} $*" >&2; }
die() { log "${RED}ERROR${RESET} $*" >&2; exit 1; }
on_error() {
  local exit_code="$1" line="$2"
  warn "Cleanup failed at line $line (exit $exit_code)."
  exit "$exit_code"
}

usage() {
  cat <<EOF
Usage: ${0##*/} [options]

Clean common local system caches and package leftovers. Trash is preserved
unless --empty-trash is passed. Run as your normal user; sudo is used as needed.

Options:
  -n, --dry-run          Show actions without changing anything.
      --journal-age AGE  Vacuum journal logs older than AGE (default: ${JOURNAL_AGE}).
      --skip-apt         Skip apt autoremove/autoclean/clean.
      --skip-journal     Skip systemd journal vacuuming.
      --skip-flatpak     Skip unused Flatpak runtime cleanup.
      --skip-snap        Skip Snap cache cleanup.
      --skip-brew        Skip Homebrew cleanup.
      --skip-thumbnails Skip thumbnail cache cleanup.
      --empty-trash     Permanently delete this user's Trash contents.
  -h, --help             Show this help message.
EOF
}

quote_cmd() {
  local quoted
  printf -v quoted '%q ' "$@"
  printf '%s' "${quoted% }"
}

as_root() {
  if [[ $EUID -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

run() {
  if "$DRY_RUN"; then
    info "[dry-run] $(quote_cmd "$@")"
    return 0
  fi

  info "$(quote_cmd "$@")"
  "$@"
}

run_root() {
  if "$DRY_RUN"; then
    if [[ $EUID -eq 0 ]]; then
      info "[dry-run] $(quote_cmd "$@")"
    else
      info "[dry-run] sudo $(quote_cmd "$@")"
    fi
    return 0
  fi

  if [[ $EUID -eq 0 ]]; then
    info "$(quote_cmd "$@")"
    "$@"
  else
    info "sudo $(quote_cmd "$@")"
    sudo "$@"
  fi
}

empty_dir_contents() {
  local dir="$1"
  local label="$2"

  if [[ ! -d "$dir" ]]; then
    warn "$label not found: $dir"
    return 0
  fi

  if "$DRY_RUN"; then
    local count="unknown"
    if count="$(find "$dir" -mindepth 1 -maxdepth 1 2>/dev/null | wc -l)"; then
      count="${count//[[:space:]]/}"
    else
      count="unknown"
    fi
    info "[dry-run] remove $count item(s) from $label: $dir"
    return 0
  fi

  info "Cleaning $label: $dir"
  find "$dir" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
}

empty_dir_contents_root() {
  local dir="$1"
  local label="$2"

  if [[ ! -d "$dir" ]]; then
    info "$label not found; skipping: $dir"
    return 0
  fi

  if "$DRY_RUN"; then
    local count="unknown"
    if count="$(find "$dir" -mindepth 1 -maxdepth 1 2>/dev/null | wc -l)"; then
      count="${count//[[:space:]]/}"
    else
      count="unknown"
    fi
    if [[ $EUID -eq 0 ]]; then
      info "[dry-run] remove $count item(s) from $label: $dir"
    else
      info "[dry-run] sudo remove $count item(s) from $label: $dir"
    fi
    return 0
  fi

  info "Cleaning $label: $dir"
  as_root find "$dir" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--dry-run)
      DRY_RUN=true
      ;;
    --journal-age)
      [[ $# -ge 2 ]] || die "--journal-age requires a value"
      JOURNAL_AGE="$2"
      shift
      ;;
    --skip-apt)
      SKIP_APT=true
      ;;
    --skip-journal)
      SKIP_JOURNAL=true
      ;;
    --skip-flatpak)
      SKIP_FLATPAK=true
      ;;
    --skip-snap)
      SKIP_SNAP=true
      ;;
    --skip-brew)
      SKIP_BREW=true
      ;;
    --skip-thumbnails)
      SKIP_THUMBNAILS=true
      ;;
    --empty-trash)
      EMPTY_TRASH=true
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown option: $1"
      ;;
  esac
  shift
done

[[ $EUID -ne 0 ]] || die "Run as your normal user, without sudo; privileged steps request sudo themselves."
[[ $JOURNAL_AGE =~ ^[1-9][0-9]*(s|min|h|d|w|month|y)$ ]] || die "Invalid journal age: use a positive duration such as 7d or 24h."
[[ ${XDG_DATA_HOME:-$HOME/.local/share} == /* && ${XDG_CACHE_HOME:-$HOME/.cache} == /* ]] || die "XDG data and cache directories must be absolute paths."
trap 'on_error "$?" "$LINENO"' ERR

info "Starting system cleanup"

if ! "$SKIP_APT"; then
  if command -v apt-get >/dev/null 2>&1; then
    run_root apt-get autoremove -y
    run_root apt-get autoclean -y
    run_root apt-get clean
  else
    info "apt-get not found; skipping apt cleanup"
  fi
fi

if "$EMPTY_TRASH"; then
  empty_dir_contents "${XDG_DATA_HOME:-$HOME/.local/share}/Trash/files" "trash files"
  empty_dir_contents "${XDG_DATA_HOME:-$HOME/.local/share}/Trash/info" "trash metadata"
else
  info "Preserving Trash; pass --empty-trash to permanently empty it"
fi
if ! "$SKIP_THUMBNAILS"; then
  empty_dir_contents "${XDG_CACHE_HOME:-$HOME/.cache}/thumbnails" "thumbnail cache"
fi

if ! "$SKIP_JOURNAL"; then
  if command -v journalctl >/dev/null 2>&1; then
    run_root journalctl "--vacuum-time=${JOURNAL_AGE}"
  else
    info "journalctl not found; skipping journal cleanup"
  fi
fi

if ! "$SKIP_FLATPAK"; then
  if command -v flatpak >/dev/null 2>&1; then
    run flatpak uninstall --unused -y
  else
    info "flatpak not found; skipping Flatpak cleanup"
  fi
fi

if ! "$SKIP_SNAP"; then
  empty_dir_contents_root "/var/lib/snapd/cache" "Snap cache"
fi

if ! "$SKIP_BREW" && command -v brew >/dev/null 2>&1; then
  run brew cleanup
fi

success "System cleanup completed"
