#!/usr/bin/env bash
# Install Security Research Lab Cursor rules into another project.
#
# Standalone (download this script only — auto-clones the lab):
#   curl -fsSL https://raw.githubusercontent.com/purwowd/security-research-lab/main/scripts/install_lab_rules.sh \
#     | bash -s -- /path/to/new-project
#
# Or from a local lab checkout:
#   ./scripts/install_lab_rules.sh /path/to/new-project
#   ./scripts/install_lab_rules.sh /path/to/new-project --mode symlink --with-scripts --force
#
# What gets installed (by default):
#   .cursorrules
#   ai_agent_instructions/   (docs 00–20 + templates + INDEX.md)
#
# Optional:
#   scripts/new_poc.py       (--with-scripts)
#   FIRST_PROMPT.txt         (always written unless --no-prompt-file)

set -euo pipefail

MODE="copy"          # copy | symlink
WITH_SCRIPTS=0
FORCE=0
DRY_RUN=0
WRITE_PROMPT=1
TARGET=""
REPO_URL="${LAB_REPO_URL:-https://github.com/purwowd/security-research-lab.git}"
CACHE_DIR="${LAB_CACHE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/security-research-lab}"
BRANCH="${LAB_BRANCH:-main}"
NO_CLONE=0

SCRIPT_DIR=""
if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

usage() {
  cat <<'EOF'
Install Security Research Lab Cursor rules into a target project.

If this script is not running from a full lab checkout, it clones the lab
repo into a local cache, then copies/symlinks the rules into your project.

Usage:
  install_lab_rules.sh <target-project-dir> [options]

Options:
  --mode copy|symlink   Install method (default: copy)
  --with-scripts        Also install scripts/new_poc.py (+ scripts/ dir)
  --force               Replace existing .cursorrules / ai_agent_instructions
  --dry-run             Print actions without writing
  --no-prompt-file      Do not write FIRST_PROMPT.txt
  --repo-url URL        Lab git URL (default: github.com/purwowd/security-research-lab)
  --cache-dir DIR       Where to clone when not inside the lab (default: ~/.cache/...)
  --branch NAME         Git branch to clone/pull (default: main)
  --no-clone            Fail instead of auto-cloning when lab source is missing
  -h, --help            Show this help

Env overrides:
  LAB_REPO_URL, LAB_CACHE_DIR, LAB_BRANCH

Examples:
  # Standalone one-liner (no prior clone needed)
  curl -fsSL https://raw.githubusercontent.com/purwowd/security-research-lab/main/scripts/install_lab_rules.sh \
    | bash -s -- ~/Developments/my-new-lab

  # From this repo
  ./scripts/install_lab_rules.sh ~/Developments/my-new-lab
  ./scripts/install_lab_rules.sh ../other-app --mode symlink --with-scripts
EOF
}

log() { printf '[*] %s\n' "$*"; }
warn() { printf '[!] %s\n' "$*" >&2; }
die() { printf '[-] %s\n' "$*" >&2; exit 1; }

run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] %s\n' "$*"
  else
    eval "$@"
  fi
}

is_lab_root() {
  local root="$1"
  [[ -n "$root" && -f "$root/.cursorrules" && -d "$root/ai_agent_instructions" ]]
}

ensure_lab_source() {
  # Prefer local checkout when the script lives inside the lab.
  if [[ -n "$SCRIPT_DIR" ]] && is_lab_root "$(cd "$SCRIPT_DIR/.." && pwd)"; then
    LAB_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
    log "Using local lab checkout: $LAB_ROOT"
    return 0
  fi

  if [[ "$NO_CLONE" -eq 1 ]]; then
    die "Lab source not found next to this script (use a full checkout, or omit --no-clone)"
  fi

  command -v git >/dev/null 2>&1 || die "git is required to auto-clone the lab repo"

  LAB_ROOT="$CACHE_DIR"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "[dry-run] would ensure lab clone at $LAB_ROOT (branch=$BRANCH url=$REPO_URL)"
    return 0
  fi

  if is_lab_root "$LAB_ROOT"; then
    log "Updating cached lab: $LAB_ROOT"
    git -C "$LAB_ROOT" fetch --quiet origin "$BRANCH" || warn "git fetch failed — using existing cache"
    git -C "$LAB_ROOT" checkout --quiet "$BRANCH" 2>/dev/null || true
    git -C "$LAB_ROOT" pull --ff-only --quiet origin "$BRANCH" 2>/dev/null \
      || warn "git pull failed — using existing cache"
  else
    log "Cloning lab repo into cache: $LAB_ROOT"
    mkdir -p "$(dirname "$LAB_ROOT")"
    rm -rf "$LAB_ROOT"
    git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$LAB_ROOT"
  fi

  is_lab_root "$LAB_ROOT" || die "Clone succeeded but lab files missing under $LAB_ROOT"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="${2:-}"
      shift 2
      ;;
    --with-scripts)
      WITH_SCRIPTS=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --no-prompt-file)
      WRITE_PROMPT=0
      shift
      ;;
    --repo-url)
      REPO_URL="${2:-}"
      shift 2
      ;;
    --cache-dir)
      CACHE_DIR="${2:-}"
      shift 2
      ;;
    --branch)
      BRANCH="${2:-}"
      shift 2
      ;;
    --no-clone)
      NO_CLONE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      die "Unknown option: $1"
      ;;
    *)
      if [[ -n "$TARGET" ]]; then
        die "Unexpected argument: $1"
      fi
      TARGET="$1"
      shift
      ;;
  esac
done

[[ -n "$TARGET" ]] || { usage; die "target project directory required"; }
[[ "$MODE" == "copy" || "$MODE" == "symlink" ]] || die "--mode must be copy or symlink"
[[ -n "$REPO_URL" ]] || die "--repo-url must not be empty"
[[ -n "$CACHE_DIR" ]] || die "--cache-dir must not be empty"
[[ -n "$BRANCH" ]] || die "--branch must not be empty"

# Resolve target to absolute path (create if missing)
if [[ ! -d "$TARGET" ]]; then
  log "Creating target directory: $TARGET"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "[dry-run] mkdir -p $TARGET"
    PARENT="$(cd "$(dirname "$TARGET")" 2>/dev/null && pwd || true)"
    BASE="$(basename "$TARGET")"
    if [[ -n "$PARENT" ]]; then
      TARGET="$PARENT/$BASE"
    fi
  else
    mkdir -p "$TARGET"
    TARGET="$(cd "$TARGET" && pwd)"
  fi
else
  TARGET="$(cd "$TARGET" && pwd)"
fi

ensure_lab_source

if [[ "$DRY_RUN" -ne 1 ]]; then
  [[ -f "$LAB_ROOT/.cursorrules" ]] || die "Missing $LAB_ROOT/.cursorrules"
  [[ -d "$LAB_ROOT/ai_agent_instructions" ]] || die "Missing $LAB_ROOT/ai_agent_instructions"
fi

install_path() {
  # install_path <src> <dest>
  local src="$1"
  local dest="$2"
  if [[ -e "$dest" || -L "$dest" ]]; then
    if [[ "$FORCE" -eq 1 ]]; then
      warn "Replacing existing: $dest"
      run "rm -rf $(printf '%q' "$dest")"
    else
      die "Already exists (use --force): $dest"
    fi
  fi
  case "$MODE" in
    copy)
      if [[ -d "$src" ]]; then
        run "cp -R $(printf '%q' "$src") $(printf '%q' "$dest")"
      else
        run "cp $(printf '%q' "$src") $(printf '%q' "$dest")"
      fi
      ;;
    symlink)
      run "ln -s $(printf '%q' "$src") $(printf '%q' "$dest")"
      ;;
  esac
  log "Installed ($MODE): $dest"
}

log "Lab root:    $LAB_ROOT"
log "Target:      $TARGET"
log "Mode:        $MODE"

install_path "$LAB_ROOT/.cursorrules" "$TARGET/.cursorrules"
install_path "$LAB_ROOT/ai_agent_instructions" "$TARGET/ai_agent_instructions"

if [[ "$WITH_SCRIPTS" -eq 1 ]]; then
  if [[ ! -f "$LAB_ROOT/scripts/new_poc.py" ]]; then
    warn "scripts/new_poc.py not found — skipping"
  else
    if [[ "$MODE" == "symlink" ]]; then
      install_path "$LAB_ROOT/scripts" "$TARGET/scripts"
    else
      run "mkdir -p $(printf '%q' "$TARGET/scripts")"
      if [[ -e "$TARGET/scripts/new_poc.py" || -L "$TARGET/scripts/new_poc.py" ]]; then
        if [[ "$FORCE" -eq 1 ]]; then
          run "rm -f $(printf '%q' "$TARGET/scripts/new_poc.py")"
        else
          die "Already exists (use --force): $TARGET/scripts/new_poc.py"
        fi
      fi
      run "cp $(printf '%q' "$LAB_ROOT/scripts/new_poc.py") $(printf '%q' "$TARGET/scripts/new_poc.py")"
      run "chmod +x $(printf '%q' "$TARGET/scripts/new_poc.py")"
      log "Installed (copy): $TARGET/scripts/new_poc.py"
    fi
  fi
fi

PROMPT_BODY='Read ai_agent_instructions/00–20 (see INDEX.md). Prioritize 13 (PoC), 14 (red team),
and 20 (horizon 2026–2031). Confirm: full-attack packages; --mode full as primary
reproduce command; framework is 5-year-tuned (not timeless).'

if [[ "$WRITE_PROMPT" -eq 1 ]]; then
  PROMPT_FILE="$TARGET/FIRST_PROMPT.txt"
  if [[ -e "$PROMPT_FILE" && "$FORCE" -ne 1 ]]; then
    warn "Leaving existing FIRST_PROMPT.txt (use --force to overwrite)"
  else
    if [[ "$DRY_RUN" -eq 1 ]]; then
      log "[dry-run] write $PROMPT_FILE"
    else
      printf '%s\n' "$PROMPT_BODY" >"$PROMPT_FILE"
      log "Wrote: $PROMPT_FILE"
    fi
  fi
fi

cat <<EOF

[+] Done.

Next steps:
  1. Open the project in Cursor:  cursor $(printf '%q' "$TARGET")
  2. Start Agent chat and paste contents of FIRST_PROMPT.txt
     (or run:  cat $(printf '%q' "$TARGET/FIRST_PROMPT.txt"))

Installed:
  - .cursorrules
  - ai_agent_instructions/
EOF

if [[ "$WITH_SCRIPTS" -eq 1 ]]; then
  echo "  - scripts/ (new_poc.py)"
fi
echo
