#!/usr/bin/env sh
# Download utilities for poor-tools

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

# Detect wget feature support
wget_has() {
  # Detect support by looking at help text (works on GNU and BusyBox).
  wget --help 2>&1 | grep -Eq -- "[[:space:]]$1([=[:space:]]|$)"
}

# Get wget flags with fallbacks for different implementations
get_wget_flags() {
  WGET_SRVR="$([ "$(wget_has --server-response && echo y || echo n)" = y ] && echo '--server-response' || echo '-S')"
  WGET_REDIRECT="$([ "$(wget_has --max-redirect && echo y || echo n)" = y ] && echo '--max-redirect=20' || echo '')"
  WGET_NOCHK="$([ "$(wget_has --no-check-certificate && echo y || echo n)" = y ] && echo '--no-check-certificate' || echo '')"
  WGET_CONNTO="$([ "$(wget_has --connect-timeout && echo y || echo n)" = y ] && echo '--connect-timeout' || echo '')"
  WGET_TIMEOUT="$([ "$(wget_has --timeout && echo y || echo n)" = y ] && echo '--timeout' || echo '-T')" # BusyBox uses -T
  WGET_RETRY="$([ "$(wget_has --tries && echo y || echo n)" = y ] && echo '--tries' || echo '')"
  WGET_UA="$([ "$(wget_has --user-agent && echo y || echo n)" = y ] && echo '--user-agent' || echo '')"
  WGET_HEADER="$([ "$(wget_has --header && echo y || echo n)" = y ] && echo '--header' || echo '')"
  WGET_POSTDATA="$([ "$(wget_has --post-data && echo y || echo n)" = y ] && echo '--post-data' || echo '')"
  
  # Auth flags: GNU has --http-user/--http-password; BusyBox has --user=USER:PASSWORD
  if wget_has --http-user && wget_has --http-password
  then
    WGET_AUTH_USER='--http-user'
    WGET_AUTH_PASS='--http-password'
  else
    WGET_AUTH_USER='--user'  # expects USER:PASSWORD together if BusyBox
    WGET_AUTH_PASS=''        # leave empty
  fi
}