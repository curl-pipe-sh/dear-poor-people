#!/usr/bin/env sh
# Common echo utilities for poor-tools

echo_success() {
  echo -e "🟢 \e[32m${*}\e[0m"
}

echo_error() {
  echo -e "🔴 \e[31m${*}\e[0m"
}

echo_warning() {
  echo -e "⚠️  \e[33m${*}\e[0m"
}

echo_info() {
  echo -e "ℹ️  \e[34m${*}\e[0m"
}
