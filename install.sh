#!/bin/bash

__FILE__=$(readlink -f "$0")
__DIR__=$(dirname "$__FILE__")

plugins_dir="$HOME/.config/terminator/plugins"

mkdir -p "$plugins_dir"

cp -r "$__DIR__/clisnips" "$plugins_dir"
cp "$__DIR__/clisnips_plugin.py" "$plugins_dir"

exit 0
