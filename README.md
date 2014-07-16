CliSnips
========

![xkcd/tar](http://imgs.xkcd.com/comics/tar.png)

Let this be no more!

CliSnips provides a snippet library (similar to clicompanion2) in which you can save/edit/search/recall
your commands (or any code snippet for use in i.e. ipython or irb).

This is a plugin for teh awesome [Terminator](http://gnometerminator.blogspot.fr/p/introduction.html) terminal emulator.


## Dependencies

 * Python >= 2.7
 * PyGtk
 * PyGtkSourceView (optional)
 * [Terminator](http://gnometerminator.blogspot.fr/p/introduction.html)

On Debian, Ubuntu, Mint, etc... 
```sh
sudo apt-get install terminator python-gtksourceview2
```


## Installation

```sh
git clone https://github.com/ju1ius/clisnips.git clisnips
cd clisnips
./install.sh
```

Open Terminator, go to Preferences > Plugins and enable CliSnipsMenu.
