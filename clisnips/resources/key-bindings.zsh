
function __clisnips__() {
  local snip
  local ret
  snip="$(clisnips 2> "$(tty)")"
  ret=$?
  LBUFFER="${LBUFFER}${snip}"
  zle reset-prompt
  return $ret
}
zle     -N   __clisnips__
bindkey '\es' __clisnips__
