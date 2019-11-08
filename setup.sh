#!/bin/bash

set -eu

__dir__=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")

data_home="${XDG_DATA_HOME:-${HOME}/.local/share}"
config_home="${XDG_CONFIG_HOME:-${HOME}/.config}"


function do_install() {
  mkdir -p "${config_home}/clisnips" "${data_home}/clisnips"

  pushd "${HOME}"

  if [[ -f "$HOME/.bashrc" ]]; then
    ln -s "${__dir__}/shell/key-bindings.bash" '.clisnips.bash'
    echo "PATH=\"${__dir__}:\$PATH\"" >> .bashrc
    echo 'source "$HOME/.clisnips.bash"' >> .bashrc
  fi
  if [[ -f "$HOME/.zshrc" ]]; then
    ln -s "${__dir__}/shell/key-bindings.zsh" '.clisnips.zsh'
    echo "PATH=\"${__dir__}:\$PATH\"" >> .zshrc
    echo 'source "$HOME/.clisnips.zsh"' >> .zshrc
  fi

  popd

}

function do_uninstall() {
  rm -rf "${config_home}/clisnips" "${data_home}/clisnips"
  rm -f "$HOME/.clisnips.bash" "$HOME/.clisnips.zsh"
  if [[ -f "$HOME/.bashrc" ]]; then
    sed -i '/clisnips/d' "$HOME/.bashrc"
  fi
  if [[ -f "$HOME/.zshrc" ]]; then
    sed -i '/clisnips/d' "$HOME/.zshrc"
  fi
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
