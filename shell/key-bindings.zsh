
function __clisnips__() {
  local snip
  local ret
  snip="$(/usr/bin/env python3 clisnips-tui.py 2> "$(tty)")"
  ret=$?
  LBUFFER="${LBUFFER}${snip}"
  zle reset-prompt
  return $ret
}
zle     -N   __clisnips__
bindkey '\es' __clisnips__
