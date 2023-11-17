# Anatomy of a snippet

A clisnips snippet has the following properties:

 * `title`: a title
 * `tag`: some tags
 * `cmd`: a command
 * `doc`: a documentation

The `title` and `tag` properties are what affect search results.
The `cmd` and `doc` properties affect what will end up being inserted in your terminal.
We will describe these properties in the following sections.

## The `title` property

The title property is, as the name suggests, a descriptive title for the snippet.
The content of this property will be indexed in the snippets database and will influence the snippets search result.
It should be kept short and descriptive.

## The `tag` property

The tag property is a list of keywords that allows you to logically group your snippets.
The content of this property will be indexed in the snippets database and will influence the snippets search result.

A tag is any keyword that:
 * consists only of unicode alphabetical characters plus the "_" and "-" characters.
   Diacritics like "é" will be internally converted to their ASCII equivalent during a search.
 * is at least two characters long

This means that tags can be separated by commas, spaces, colons, etc...
For example the string `this,is a list;of|tags` is a list of tags containing the tags `this`, `is`, `list` and `tags`.

## The `cmd` property

This is the actual meat of the snippet. The thing you want to insert in your terminal.

The content of this property will NOT influence the snippets search result.

A command can be a simple string, like `cat /etc/passwd`,
but it can also contain template fields like `zip -r -9 {archive_name}.zip {input_directory}`.

Template fields MUST conform to the [Python format string syntax](https://docs.python.org/3.8/library/string.html#format-string-syntax).

If a snippet's `cmd` property contains template fields,
clisnips will prompt you for a value before inserting a snippet into the terminal.

## The `doc` property

The role of this property is two-fold:
  1. it can be used to provide more extensive documentation on your snippet.
  2. it can be used to provide contextual information about the command's template fields.

The content of this property will NOT influence the snippets search result.

For example, given a snippet with the following `cmd` property:
```sh
zip -r -9 {archive_name}.zip {input_directory}
```
The corresponding documentation could look like this:
```
Creates a ZIP archive of a directory with maximum compression level.

  {archive_name} (string) The file name of the output archive
  {input_directory} (directory) The directory to compress
```

When requested to insert this snippet into your terminal, clisnips will parse this documentation.
The first paragraph will just be treated as informative free-form text.
The following lines however will be parsed as your template fields documentation.
Clisnips will then use this information to provide you with a more sensible user-interface.
For example, clisnips will acknowledge that the `input_directory` field should be an actual directory
on your filesystem, and present you an input field with path completion enabled.
