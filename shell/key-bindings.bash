
function __clisnips__() {
  local snip
  snip="$(clisnips.py 2> "$(tty)")"
  READLINE_LINE="${READLINE_LINE:0:$READLINE_POINT}${snip}${READLINE_LINE:$READLINE_POINT}"
  READLINE_POINT=$(( READLINE_POINT + ${#snip} ))
}
bind -x '"\es": "__clisnips__"'
