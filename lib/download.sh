# Download utilities for poor-tools
# shellcheck shell=sh

# Select the best available downloader
select_downloader_impl() {
  if [ -n "${POOR_DOWNLOADER_SELECTED:-}" ]
  then
    printf '%s' "$POOR_DOWNLOADER_SELECTED"
    return 0
  fi

  if [ -n "${POOR_DOWNLOADER:-}" ]
  then
    case "$POOR_DOWNLOADER" in
      curl|wget)
        if has_command "$POOR_DOWNLOADER"
        then
          POOR_DOWNLOADER_SELECTED=$POOR_DOWNLOADER
          printf '%s' "$POOR_DOWNLOADER_SELECTED"
          return 0
        fi
        ;;
    esac
  fi

  if has_command curl
  then
    POOR_DOWNLOADER_SELECTED=curl
    printf '%s' "$POOR_DOWNLOADER_SELECTED"
    return 0
  fi

  if has_command wget
  then
    POOR_DOWNLOADER_SELECTED=wget
    printf '%s' "$POOR_DOWNLOADER_SELECTED"
    return 0
  fi

  echo_error "no downloader (curl or wget) available"
  return 1
}

# Download file using curl or wget
download_file_impl() {
  # Use positional parameters: $1=url, $2=target, $3=downloader (optional)
  url="$1"
  target="$2"
  downloader="${3:-}"

  if [ -z "$downloader" ]
  then
    downloader=$(select_downloader_impl) || return 1
  fi

  case "$downloader" in
    curl)
      if curl -fsSL "$url" -o "$target"
      then
        chmod +x "$target" 2>/dev/null || true
        return 0
      else
        return 1
      fi
      ;;
    wget)
      if wget -q "$url" -O "$target"
      then
        chmod +x "$target" 2>/dev/null || true
        return 0
      else
        return 1
      fi
      ;;
    *)
      echo_error "Unknown downloader: $downloader"
      return 1
      ;;
  esac
}

