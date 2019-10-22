#!/bin/bash

set -eu

__DIR__=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")

DATA_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}"
CONFIG_HOME="${XDG_CONFIG_HOME:-${HOME}/.config}"
PLUGINS_HOME="${CONFIG_HOME}/terminator/plugins"

SERVICE_FILE="me.ju1ius.clisnips.service"


function do_install() {
  mkdir -p "${PLUGINS_HOME}" "${DATA_HOME}/dbus-1/services"

  pushd "${PLUGINS_HOME}"
  ln -sf "${__DIR__}/terminator_plugin.py" clisnips.py
  popd

  sed "s#__EXEC_PATH__#${__DIR__}/clisnips.py#" \
    "${__DIR__}/${SERVICE_FILE}" \
    > "${DATA_HOME}/dbus-1/services/${SERVICE_FILE}"
}

function do_uninstall() {
  rm -f "${PLUGINS_HOME}/clisnips.py"
  rm -f "${DATA_HOME}/dbus-1/services/${SERVICE_FILE}"
}

if [[ -z "${1:-}" ]]; then
    do_install
    exit $?
fi

case "$1" in
  -u|--uninstall)
    do_uninstall
  ;;
  *)
    echo "Unknown option or argument: $1"
  ;;
esac

exit 0
