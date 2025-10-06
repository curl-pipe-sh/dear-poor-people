#!/usr/bin/env sh
# TOOL_NAME installer — install TOOL_NAME from poor-tools web installer
# Generated from: SERVER_URL

set -eu

# INCLUDE_FILE: lib/utils.sh
# INCLUDE_FILE: lib/echo.sh

TOOL_NAME="TOOL_NAME"
SCRIPT_URL="SERVER_URL/TOOL_NAME"
DEST=""
EMULATE=0
CLEAR=0
UNINSTALL=0

usage() {
  cat <<'USAGE' >&2
Usage: install-TOOL_NAME [OPTIONS]

Options:
  --dest DIR       Install into DIR (or set DEST environment variable)
  --emulate        Strip leading "poor" when naming installed binary
  --clear          Remove DEST before install. With --uninstall try removing DEST after
  --uninstall      Remove matching files instead of installing
  -h, --help       Show this help

Installs TOOL_NAME from SERVER_URL
USAGE
}

error_missing_arg() {
  echo "option '$1' requires an argument" >&2
  usage
  exit 2
}

# Parse arguments
while [ $# -gt 0 ]; do
  case "$1" in
    --dest)
      [ $# -gt 1 ] || error_missing_arg "$1"
      DEST="$2"
      shift 2
      ;;
    --dest=*)
      DEST="${1#*=}"
      shift
      ;;
    --emulate)
      EMULATE=1
      shift
      ;;
    --clear)
      CLEAR=1
      shift
      ;;
    --uninstall)
      UNINSTALL=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "unknown option: $1" >&2
      usage
      exit 2
      ;;
    *)
      echo "unexpected argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

# Set default destination
if [ -z "$DEST" ]; then
  if [ -n "${DEST:-}" ]; then
    DEST="$DEST"
  else
    DEST="$HOME/.local/bin"
  fi
fi

# Ensure destination exists
if [ "$UNINSTALL" = 0 ]; then
  mkdir -p "$DEST"
fi

# Clear destination if requested
if [ "$CLEAR" = 1 ] && [ "$UNINSTALL" = 0 ]; then
  echo_info "Clearing destination directory: $DEST"
  rm -rf "$DEST"
  mkdir -p "$DEST"
fi

# Determine binary name
if [ "$EMULATE" = 1 ]; then
  if [ "$TOOL_NAME" = "curl-openssl" ]; then
    BIN_NAME="curl-openssl"
  else
    # Remove "poor" prefix if it exists
    BIN_NAME=$(echo "$TOOL_NAME" | sed 's/^poor//')
  fi
else
  # Use full poor-tool name
  if [ "$TOOL_NAME" = "curl-openssl" ]; then
    BIN_NAME="poorcurl-openssl"
  else
    BIN_NAME="poor$TOOL_NAME"
  fi
fi

TARGET_FILE="$DEST/$BIN_NAME"

# Check for available downloader
DOWNLOADER=""
if has_command curl; then
  DOWNLOADER="curl"
elif has_command wget; then
  DOWNLOADER="wget"
else
  echo_error "Neither curl nor wget found. Cannot download $TOOL_NAME."
  exit 1
fi

if [ "$UNINSTALL" = 1 ]; then
  echo_info "Uninstalling $TOOL_NAME from $TARGET_FILE"
  if [ -f "$TARGET_FILE" ]; then
    rm -f "$TARGET_FILE"
    echo_success "Removed $TARGET_FILE"
  else
    echo_warning "$TARGET_FILE not found"
  fi

  # Try to remove destination if --clear was specified and it's empty
  if [ "$CLEAR" = 1 ] && [ -d "$DEST" ]; then
    if rmdir "$DEST" 2>/dev/null; then
      echo_info "Removed empty directory: $DEST"
    fi
  fi
else
  echo_info "Installing $TOOL_NAME to $TARGET_FILE"
  echo_info "Downloading from: $SCRIPT_URL"

  # Download the script
  case "$DOWNLOADER" in
    curl)
      if curl -fsSL "$SCRIPT_URL" -o "$TARGET_FILE"; then
        chmod +x "$TARGET_FILE"
        echo_success "Successfully installed $BIN_NAME to $TARGET_FILE"
      else
        echo_error "Failed to download $TOOL_NAME"
        exit 1
      fi
      ;;
    wget)
      if wget -q "$SCRIPT_URL" -O "$TARGET_FILE"; then
        chmod +x "$TARGET_FILE"
        echo_success "Successfully installed $BIN_NAME to $TARGET_FILE"
      else
        echo_error "Failed to download $TOOL_NAME"
        exit 1
      fi
      ;;
  esac
fi
