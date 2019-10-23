CliSnips
========

![xkcd/tar](http://imgs.xkcd.com/comics/tar.png)

Let this be no more!

CliSnips provides a snippet library (similar to clicompanion2) in which you can save/edit/search/recall
your commands (or any code snippet for use in i.e. ipython or irb).

This is a plugin for teh awesome [Terminator](http://gnometerminator.blogspot.fr/p/introduction.html) terminal emulator.


## Dependencies

 * Python >= 3.7
 * python-gobject with glib >= 2.0, gtk >= 3.20, gtk-sourceview >= 3.0
 * [Terminator](http://gnometerminator.blogspot.fr/p/introduction.html)

On Debian, Ubuntu, Mint, etc... 
```sh
sudo apt install terminator python-gi gir1.2-gtksource-3.0
```


## Installation

```sh
git clone https://github.com/ju1ius/clisnips.git clisnips
cd clisnips
./local-install.sh
```

Open Terminator, go to Preferences > Plugins and enable CliSnipsMenu.
