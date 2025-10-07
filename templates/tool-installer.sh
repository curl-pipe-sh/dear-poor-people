#!/usr/bin/env sh
# <TOOL_NAME> installer — install <TOOL_NAME> from poor-tools web installer
# Generated from: <SERVER_URL>

set -eu

# Source utility libraries - these lines get replaced during templating
. lib/utils.sh # <TEMPLATE>
. lib/echo.sh # <TEMPLATE>
. lib/download.sh # <TEMPLATE>

TOOL_NAME="<TOOL_NAME>"
SCRIPT_URL="<SERVER_URL>/<TOOL_NAME>"
DEST=""
EMULATE=0
CLEAR=0
UNINSTALL=0

usage() {
  cat <<'USAGE' >&2
Usage: install-<TOOL_NAME> [OPTIONS]

Options:
  --dest DIR       Install into DIR (or set DEST environment variable)
  --emulate        Strip leading "poor" when naming installed binary
  --clear          Remove DEST before install. With --uninstall try removing DEST after
  --uninstall      Remove matching files instead of installing
  --debug          Enable debug output
  --trace          Enable shell tracing (set -x)
  -h, --help       Show this help

Installs <TOOL_NAME> from <SERVER_URL>
USAGE
}

error_missing_arg() {
  echo_error "option '$1' requires an argument"
  usage
  return 2
}

# Download file using available downloader
download_file() {
  # Use positional parameters directly to avoid 'local' in POSIX sh
  # $1 = url, $2 = target, $3 = downloader

  # Use the common download_file function from lib/download.sh
  download_file_impl "$1" "$2" "$3"
}

# Parse arguments
while [ $# -gt 0 ]
do
  case "$1" in
    --dest)
      [ $# -gt 1 ] || { error_missing_arg "$1"; exit 2; }
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
    --debug)
      DEBUG=1
      shift
      ;;
    --trace)
      set -x
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo_error "unknown option: $1"
      usage
      exit 2
      ;;
    *)
      echo_error "unexpected argument: $1"
      usage
      exit 2
      ;;
  esac
done

# Set default destination
if [ -z "$DEST" ]
then
  if [ -n "${DEST_ENV:-}" ]
  then
    DEST="$DEST_ENV"
  else
    DEST="$HOME/.local/bin"
  fi
fi

# Ensure destination exists
if [ "$UNINSTALL" = 0 ]
then
  mkdir -p "$DEST"
fi

# Clear destination if requested
if [ "$CLEAR" = 1 ] && [ "$UNINSTALL" = 0 ]
then
  echo_info "Clearing destination directory: ${DEST}"
  rm -rf "$DEST"
  mkdir -p "$DEST"
fi

# Determine binary name
if [ "$EMULATE" = 1 ]
then
  # Remove "poor" prefix if it exists for emulation mode
  BIN_NAME=$(echo "$TOOL_NAME" | sed 's/^poor//')
else
  # Use full poor-tool name, add "poor" prefix if not already present
  case "$TOOL_NAME" in
    poor*)
      BIN_NAME="$TOOL_NAME"
      ;;
    *)
      BIN_NAME="poor$TOOL_NAME"
      ;;
  esac
fi

TARGET_FILE="$DEST/$BIN_NAME"

# Check for available downloader
DOWNLOADER=""
if has_command curl
then
  DOWNLOADER="curl"
elif has_command wget
then
  DOWNLOADER="wget"
else
  echo_error "Neither curl nor wget found. Cannot download ${TOOL_NAME}."
  exit 1
fi

# Handle special case for "all tools" installation
if [ "$TOOL_NAME" = "all" ]
then
  echo_info "Installing all poor-tools"
  echo_info "This will download and install all available tools from the server"

  # Use the tools list that gets replaced by the server
  TOOLS="nmap curl curl-openssl column socat"
  BASE_URL="${SCRIPT_URL%/all}"

  for tool in $TOOLS
  do
    echo_info "Installing ${tool}..."
    tool_url="${BASE_URL}/${tool}"

    # Determine tool filename
    if [ "$EMULATE" = 1 ]
    then
      tool_bin=$(echo "$tool" | sed 's/^poor//')
    else
      case "$tool" in
        poor*) tool_bin="$tool" ;;
        *) tool_bin="poor${tool}" ;;
      esac
    fi

    tool_target="${DEST}/${tool_bin}"

    if download_file "$tool_url" "$tool_target" "$DOWNLOADER"
    then
      echo_success "✅ Installed ${tool_bin}"
    else
      echo_error "❌ Failed to download ${tool}"
    fi
  done

  echo_success "All tools installation complete!"
  exit 0
fi

if [ "$UNINSTALL" = 1 ]
then
  echo_info "Uninstalling ${TOOL_NAME} from ${TARGET_FILE}"
  if [ -f "$TARGET_FILE" ]
  then
    rm -f "$TARGET_FILE"
    echo_success "Removed ${TARGET_FILE}"
  else
    echo_warning "${TARGET_FILE} not found"
  fi

  # Try to remove destination if --clear was specified and it's empty
  if [ "$CLEAR" = 1 ] && [ -d "$DEST" ]
  then
    if rmdir "$DEST" 2>/dev/null
    then
      echo_info "Removed empty directory: ${DEST}"
    fi
  fi
else
  echo_info "Installing ${TOOL_NAME} to ${TARGET_FILE}"
  echo_info "Downloading from: ${SCRIPT_URL}"

  # Download the script
  if download_file "$SCRIPT_URL" "$TARGET_FILE" "$DOWNLOADER"
  then
    echo_success "Successfully installed ${BIN_NAME} to ${TARGET_FILE}"
  else
    echo_error "Failed to download ${TOOL_NAME}"
    exit 1
  fi
fi
