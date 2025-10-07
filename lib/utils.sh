#!/usr/bin/env sh
# Common utilities for poor-tools

# Check if a command exists
has_command() {
  command -v "$1" >/dev/null 2>&1
}

# Get script directory (works with symlinks) - improved to avoid infinite loops
get_script_dir() {
  # Use positional parameter: $1 = script_path
  script_path="$1"
  visited_paths=""

  if [ "${script_path%/*}" = "$script_path" ]
  then
    script_path=$(command -v -- "$script_path" 2>/dev/null || echo "$script_path")
  fi

  while LINK_TARGET=$(readlink "$script_path" 2>/dev/null)
  do
    # Check for circular symlinks to prevent infinite loops
    case " $visited_paths " in
      *" $script_path "*)
        echo_error "circular symlink detected for $script_path"
        return 1
        ;;
    esac
    visited_paths="$visited_paths $script_path"

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
