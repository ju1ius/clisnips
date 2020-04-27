# Creating snippets

## I. Simple snippets

First open clisnips by invoking the keyboard shortcut (`alt+s` by default).

Then follow these steps:
  1. put the focus on the snippets list by pressing your `tab` key
  2. invoke the snippet creation dialog by pressing `+`.
  3. fill the snippets properties, using your `up` or `down` arrow keys to move focus between the input fields.
  4. When finished, focus the `< Apply >` button and press `enter`.

## II. Parametrized snippets

Creating parametrized snippets is what clisnips is really about,
allowing the creation of truly reusable command templates.

### A simple example

Let's start with a simple example.

Follow the steps 1 to 4 from section I. above, using the following values for step 3:

| Field         | Value              |
|---------------|--------------------|
| Title         | Example n°1        |
| Tags          | tutorial           |
| Command       | mv {} {}           |
| Documentation | Moves stuff around |

Notice that the value for our `command` field contains to template fields.

Back to the snippet list, find your new snippet by searching for `example` or `tutorial`,
focus it and press `enter`.

Clisnips now recognizes that the snippet is parametrized and opens a dialog
to prompt you for the two values corresponding to the template fields we provided for the command.

Since we did not provide a name for the fields they are implicitly numbered 0 and 1.

If you fill-in the input fields with the values `foo` and `bar` and press the `< Apply >` button,
clisnips should now have inserted the command `mv foo bar` in your terminal.

Congratulations, you just created your first parametrized snippet ! 

### Going further

There is more you can do with parametrized snippets.

#### Field naming

Instead of relying on the implicit field numbering as in the above example,
you can (and probably should) give a descriptive name to your template fields,
for example `mv {source} {destination}`.

#### Field syntax

The template fields in commands follow the [Python format string syntax](https://docs.python.org/3.8/library/string.html#format-string-syntax).

Since clisnips is written in python, this means you can use all the formatting options of the aforementioned syntax
(i.e. using `{: >4}` to pad a string with up-to 4 space characters).

This also means that to include a literal curly-brace character (`{` or `}`) in your command,
you have to escape it by doubling it using `{{` or `}}`.

#### Flag fields

Since clisnips was made to deal mostly with CLI snippets, it extends the python format string syntax
to allow for one or two leading `-` characters in template field names.

When provided with such a field name, clisnips will treat it as a boolean CLI flag.

For example given the command `ls {-l}`, clisnips will prompt you with a checkbox,
and output either `ls -l` if you check it, or just `ls` if it don't.


#### Field types

By default, template fields are treated as simple strings (or boolean flags as we've just seen).

There are other special field types you can use like numbers, filesystem paths, ranges, choice lists...
To use these special types, you'll have to write proper documentation for your snippet.

These are documented in the following section: [Snippet documentation](./snippet-documentation.md)
