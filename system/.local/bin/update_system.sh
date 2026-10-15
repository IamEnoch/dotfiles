#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

# Resolve the actual file so sibling cleanup works through Stow and legacy links.
SCRIPT_DIR="$(dirname -- "$(readlink -f -- "${BASH_SOURCE[0]}")")"

DRY_RUN=false
RUN_CLEAN=true
RUN_RELEASE_UPGRADE=false
RUN_PIP=false
RUN_NPM=false
RUN_BREW=true
FULL_UPGRADE=false

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
  warn "Update failed at line $line (exit $exit_code)."
  exit "$exit_code"
}

usage() {
  cat <<EOF
Usage: ${0##*/} [options]

Run routine updates for apt, Snap, Flatpak, and Homebrew. Cleanup runs at the end
when clean_system.sh is available, preserving Trash. Run as your normal user.

Options:
  -n, --dry-run          Show actions without changing anything.
      --no-clean         Do not run clean_system.sh after updates.
      --release-upgrade  Run Pop!_OS release upgrade if pop-upgrade exists.
      --include-pip      Upgrade outdated user pip packages.
      --include-npm      Upgrade global npm packages.
      --skip-brew        Skip Homebrew updates and cleanup.
      --full-upgrade     Allow apt to remove packages to resolve upgrades.
  -h, --help             Show this help message.
EOF
}

quote_cmd() {
  local quoted
  printf -v quoted '%q ' "$@"
  printf '%s' "${quoted% }"
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

have() {
  command -v "$1" >/dev/null 2>&1
}

update_apt() {
  if ! have apt-get; then
    warn "apt-get not found; skipping apt updates"
    return 0
  fi

  run_root apt-get update
  if "$FULL_UPGRADE"; then
    run_root apt-get full-upgrade -y
  else
    run_root apt-get upgrade -y
  fi
}

update_brew() {
  if ! have brew; then
    info "brew not found; skipping Homebrew updates"
    return 0
  fi
  run brew update
  run brew upgrade
}

update_snap() {
  if ! have snap; then
    info "snap not found; skipping Snap updates"
    return 0
  fi

  run_root snap refresh
}

update_flatpak() {
  if ! have flatpak; then
    info "flatpak not found; skipping Flatpak updates"
    return 0
  fi

  run flatpak update -y
}

update_pip_user_packages() {
  if ! have python3; then
    warn "python3 not found; skipping pip package updates"
    return 0
  fi

  if ! python3 -m pip --version >/dev/null 2>&1; then
    warn "python3 pip is not available; skipping pip package updates"
    return 0
  fi

  if "$DRY_RUN"; then
    info "[dry-run] Discover outdated user pip packages, then upgrade each with python3 -m pip install --user --upgrade"
    return 0
  fi

  local package_json package_names
  package_json="$(python3 -m pip list --user --outdated --format=json)" || die "Failed to list outdated pip packages."
  package_names="$(python3 -c 'import json,sys; print("\n".join(pkg["name"] for pkg in json.load(sys.stdin)))' <<< "$package_json")" || die "Failed to parse the pip package list."
  local packages=()
  if [[ -n "$package_names" ]]; then
    mapfile -t packages <<< "$package_names"
  fi

  if [[ ${#packages[@]} -eq 0 ]]; then
    success "User pip packages are up to date"
    return 0
  fi

  local package
  for package in "${packages[@]}"; do
    run python3 -m pip install --user --upgrade "$package"
  done
}

update_npm_global_packages() {
  if ! have npm; then
    info "npm not found; skipping npm global updates"
    return 0
  fi

  run npm update -g
}

run_cleanup() {
  local clean_script="${SCRIPT_DIR}/clean_system.sh"
  local clean_args=()
  if ! "$RUN_BREW"; then
    clean_args+=(--skip-brew)
  fi
  if [[ ! -x "$clean_script" ]]; then
    warn "clean_system.sh not found or not executable at $clean_script; skipping cleanup"
    return 0
  fi

  if "$DRY_RUN"; then
    info "$(quote_cmd "$clean_script" --dry-run "${clean_args[@]}")"
    "$clean_script" --dry-run "${clean_args[@]}"
  else
    run "$clean_script" "${clean_args[@]}"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--dry-run)
      DRY_RUN=true
      ;;
    --no-clean)
      RUN_CLEAN=false
      ;;
    --release-upgrade)
      RUN_RELEASE_UPGRADE=true
      ;;
    --include-pip)
      RUN_PIP=true
      ;;
    --include-npm)
      RUN_NPM=true
      ;;
    --skip-brew)
      RUN_BREW=false
      ;;
    --full-upgrade)
      FULL_UPGRADE=true
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
trap 'on_error "$?" "$LINENO"' ERR

info "Starting system update"

update_apt
update_snap
update_flatpak
if "$RUN_BREW"; then
  update_brew
fi

if "$RUN_RELEASE_UPGRADE"; then
  if have pop-upgrade; then
    run_root pop-upgrade release upgrade
  else
    warn "pop-upgrade not found; skipping Pop!_OS release upgrade"
  fi
fi

if "$RUN_PIP"; then
  update_pip_user_packages
else
  info "Skipping pip package updates; pass --include-pip to enable"
fi

if "$RUN_NPM"; then
  update_npm_global_packages
else
  info "Skipping npm global updates; pass --include-npm to enable"
fi

if "$RUN_CLEAN"; then
  run_cleanup
fi

if [[ -e /var/run/reboot-required ]]; then
  warn "A reboot is required to finish applying system updates."
fi

success "System update completed"
