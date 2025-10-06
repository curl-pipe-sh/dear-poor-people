# vim: set ft=sh:
# shellcheck shell=sh

CRON="${CRON:-}"
DEBUG="${DEBUG:-}"
NO_COLOR="${NO_COLOR:-}"
NO_WARNING="${NO_WARNING:-}"
VERBOSE="${VERBOSE:-}"
ECHO_SYSLOG="${ECHO_SYSLOG:-}"
QUIET="${QUIET:-}"

echo_fancy() {
  prefix="$1"
  color="$2"
  shift 2

  line="$prefix $*"
  line_fmt="$line"

  if [ -z "$NO_COLOR" ] && [ -z "$CRON" ]
  then
    line_fmt="${color}${prefix}\033[0m $*"
  fi

  printf '%b\n' "$line_fmt" >&2

  # Optionally log to syslog
  [ -z "$ECHO_SYSLOG" ] && return 0
  logger -t "$SCRIPT_NAME" "$(printf '%b\n' "$line_fmt")"
}

echo_info() {
  # Respect QUIET by suppressing info-level logs
  if [ -n "$QUIET" ]
  then
    return 0
  fi
  prefix="INF"
  color='\033[1m\033[34m'

  echo_fancy "$prefix" "$color" "$*"
}

echo_success() {
  prefix="OK"
  color='\033[1m\033[32m'

  echo_fancy "$prefix" "$color" "$*"
}

echo_warning() {
  [ -n "$NO_WARNING" ] && return 0
  prefix="WRN"
  color='\033[1m\033[33m'

  echo_fancy "$prefix" "$color" "$*"
}

echo_error() {
  prefix="ERR"
  color='\033[1m\033[31m'

  echo_fancy "$prefix" "$color" "$*"
}

echo_debug() {
  [ -z "${DEBUG}${VERBOSE}" ] && return 0
  prefix="DBG"
  color='\033[1m\033[35m'

  echo_fancy "$prefix" "$color" "$*"
}

echo_dryrun() {
  prefix="DRY"
  color='\033[1m\033[35m'

  echo_fancy "$prefix" "$color" "$*"
}

echo_confirm() {
  if [ -n "$NOCONFIRM" ]
  then
    return 0
  fi

  msg_pre='\033[31mASK\033[0m'
  msg="${1:-"Continue?"}"
  printf '%b %s [y/N] ' "$msg_pre" "$msg"
  read -r yn
  case "$yn" in
    [yY]*) return 0 ;;
    *) return 1 ;;
  esac
}
