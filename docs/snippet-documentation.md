# Writing snippet documentation

A snippet documentation consists of three optional sections, in the following order:

  1. The header section
  2. The fields documentation section
  3. The code blocks section
  

## The header section

The header section is basically just free-form text.
It is not used internally by clisnips and is just here for you to read.
It can be anything as long as it doesn't match the syntax for a field documentation or a code block.


## The fields documentation section

The fields documentation section is a list of zero or more field documentation.

A field documentation must start on a line of his own, optionally indented.
Then must come the name of a template field parameter between curly brackets.

The template field name can then be followed by an optional `type-hint`, an optional `value-hint`,
and an optional free-form `text`.

Type hints and value hints give clisnips information about what input field to use for the template field.

### Field names

Template field names must match the names provided in the snippet's command, but can appear in any order.


### Type hints

A type hint is a keyword in-between parentheses, like `(somehint)`. No whitespace is allowed inside.

Currently only the following type hints are supported:
  * `string`: A string value. It can be omitted since it is the default.
  * `flag`: A boolean value. Can be omitted if the field name is a cli flag (starts with a `-`)
  * `path`: a filesystem path
  * `file`: an existing file on the filesystem
  * `dir`: a existing directory on the filesystem

The `flag` type will be rendered as a checkbox.
If the checkbox is not checked, nothing will be displayed in the output command.
If it is checked, the template field name will be displayed.

The `path`, `file` and `dir` type hints will be rendered as an input field with path auto-completion enabled.

### Value hints

Value hints can be either a value list or a value range.

#### Value lists

Value lists are rendered by clisnips as a select box.

A value list is a comma-separated list of values in between square brackets.
Values can be either integers, floats, single or double quoted strings.
For example `["foo", 'bar', "baz"]`, `[1,2,3]` or `[3.3, 6.66, 9.999]`

You can provide a default value by including the special marker `=>` before a value like so:
`["foo", =>"bar", "baz"]`. The string `bar` will be used as default in this case.

#### Value ranges

Value ranges have a start value, an end value, an optional step, and an optional default value,
all of which must be numbers.
The start, end and step value are separated by two a colon (`:`).
Like in value lists, the default value is preceded by the default marker `=>`.
Like a value list, a value range is enclosed in square brackets.

The following `[0:10:2=>6]` is a range starting at 0 (inclusive), ending at 10 (inclusive),
with a step of 2 and a default value of 6.
As you might have guessed, it represents the range of even numbers between 0 and 10.

You can also mix integers and floats, i.e. `[1:5:0.5]`, `[0:0.9:0.1]`


## The code blocks section

**CAUTION: code blocks can execute arbitrary python code
and have complete access to your environment and filesystem.**
If you use third-party snippets, it is **your** responsibility to check that they don't contain malicious code.
You've been warned !

A code blocks section a list of zero or more code blocks.
A code block is python code in-between triple-backticks (` ``` `) code fences.

~~~
```
# Write some python code in here
```
~~~

Code blocks are executed before inserting a snippet into a terminal,
in the order in which they appear in the documentation.

Each code block is passed a global `fields` dictionary,
containing the provided values of the template fields,
which can then be modified in order to customize the output.

Note that numbered fields must be accessed using their string representation like so:
```py
fields['0'] = fields['0'].upper()
```

Importing python modules works as you'd expect, including modules in the current working directory.
```py
import os
fields['filename'] = os.path.join(os.getcwd(), fields['filename'])
```


## For the grammar geeks

Here's the documentation grammar in [PEG](https://en.wikipedia.org/wiki/Parsing_expression_grammar) syntax:

```
Documentation   <- Header? FieldDoc* CodeBlock*
Header          <- Text+
FieldDoc        <- NEWLINE WS* Param WS* TypeHint? WS* ValueHint? WS* Text?
Param           <- "{" ParamName "}"
ParamName       <- Integer | Flag | Identifier
TypeHint        <- "(" Identifier ")"
ValueHint       <- "[" (!"]")+ "]"
Text            <- ( !(FieldDoc | CodeBlock) )+
CodeBlock       <- CodeFence (!CodeFence)* CodeFence
CodeFence       <- NEWLINE "```"
Flag            <- "-" "-"? [0-9A-Za-z]+
Identifier      <- [A-Za-z_] [0-9A-Za-z_]*
Integer         <- "0" | ( [1-9] [0-9]* )
NEWLINE         <- "\n"
WS              <- " " | "\t" | "\f"
```
