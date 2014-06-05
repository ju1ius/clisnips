CliSnips
========

![xkcd/tar](http://imgs.xkcd.com/comics/tar.png)

Ever found yourself in this kind of embarrassing situation?
You use the great [Terminator](http://gnometerminator.blogspot.fr/p/introduction.html) terminal emulator ?

Then this Terminator plugin is for you!
It provides a snippet library (similar to clicompanion2) in which you can save/edit/search/recall
your commands (or any code snippet for use in i.e. ipython or irb).


## Install

```sh
# Clone the repo
git clone https://github.com/ju1ius/clisnips.git /path/to/clisnips
cd /path/to/clisnips
# Create your plugins directory if it does'nt exist
mkdir -p ~/.config/terminator/plugins
# copy clisnips_plugin.py and the clisnips directory to your plugin directory
cp -rt ~/.config/terminator/plugins clisnips_plugin.py clisnips
# symlinks work to!
```

Then in Terminator, go to Preferences > Plugins and enable CliSnipsMenu.
