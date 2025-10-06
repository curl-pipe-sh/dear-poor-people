#!/usr/bin/env sh
# Common utilities for poor-tools

# Check if a command exists
has_command() {
  command -v "$1" >/dev/null 2>&1
}

# Get script directory (works with symlinks)
get_script_dir() {
  # Use positional parameter: $1 = script_path
  script_path="$1"

  if [ "${script_path%/*}" = "$script_path" ]
  then
    script_path=$(command -v -- "$script_path" 2>/dev/null || echo "$script_path")
  fi

  while LINK_TARGET=$(readlink "$script_path" 2>/dev/null)
  do
    case "$LINK_TARGET" in
      /*)
        script_path=${LINK_TARGET}
        ;;
      *)
        script_dirname=$(dirname -- "$script_path")
        script_path=${script_dirname}/${LINK_TARGET}
        ;;
    esac
  done

  CDPATH='' cd -- "$(dirname -- "$script_path")" && pwd -P
}
