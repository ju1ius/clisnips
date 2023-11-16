# clisnips


clisnips is a command-line snippets manager.

![xkcd/tar](http://imgs.xkcd.com/comics/tar.png)

It provides a graphical command-line user interface in which you can save, search and recall your commands.


## Installation

clisnips requires python 3.11 or higher.

### 1. Install clisnips

The recommended way is to use [pipx](https://pypa.github.io/pipx/):
```sh
pipx install git+https://github.com/ju1ius/clisnips.git
```

### 2. Install shell key-bindings

```sh
# For bash
clisnips key-bindings bash
# For zsh
clisnips key-bindings zsh
```

Open a *new* shell and type the `Alt+s` keyboard shortcut to open the snippets library.

## Usage

Clisnips stores snippets in a local SQLite database,
using an FTS5 table to enable full-text search.
The search input accepts the whole [FTS5 full-text query syntax](https://www.sqlite.org/fts5.html#full_text_query_syntax).

Please have a look at the docs for getting started on
[writing your own snippets](./docs/creating-snippets.md).

In addition to its TUI, clisnips comes with a bunch of other subcommands
to help you manage your snippets. Please run `clisnips --help` to read the CLI documentation.
