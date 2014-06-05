Command Prompt:
    * display free form documentation !
    * a checkbox to view original template ?
    * a checkbox to toggle output editing
      + a button to revert changes in output field

Argument types:
  * string
  * path: a (possibly non existing) file-system path
  * file: path to an existing file
  * dir: path to an existing directory
  * file? | dir?: opens a file browser dialog
  * choice: list of choices (strings or integers)
        example: ["low", *"medium", "high"] (* is the default selected item)
                 [1, 2, 3, 4, 5] no default so the first item is used
  * range [1:5]

