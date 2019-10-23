#!/usr/bin/env bash

__DIR__=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")

set -eu

PLUGINS_DIR=/usr/share/terminator/terminatorlib/plugins
APP_DIR=/opt/clisnips
SERVICE_FILE='me.ju1ius.clisnips.service'

function do_install() {

  install -d "${PLUGINS_DIR}"
  install -m 0755 "${__DIR__}/terminator_plugin.py" "${PLUGINS_DIR}/clisnips.py"

  install -d "${APP_DIR}"
  cd "${__DIR__}"
  git ls-files | while read -r path; do
    install -D -m 0755 "${path}" "${APP_DIR}/${path}"
  done
  python3 -m compileall -fqq "${APP_DIR}"

  sed "s#__EXEC_PATH__#${APP_DIR}/clisnips.py#" \
    "${__DIR__}/${SERVICE_FILE}" \
    > "/usr/share/dbus-1/services/${SERVICE_FILE}"
}

function do_uninstall() {
  rm -f "${PLUGINS_DIR}/clisnips.py"
  rm -f "/usr/share/dbus-1/services/${SERVICE_FILE}"
  rm -rf "${APP_DIR}"
}


case "$1" in
  -u|--uninstall)
    do_uninstall
  ;;
  *)
    do_install
  ;;
esac

exit 0
