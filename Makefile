
user_home := $(shell echo ~$(SUDO_USER))
ifeq ($(strip $(user_home)),)
user_home := $(HOME)
endif

xdg_config_home := $(XDG_CONFIG_HOME)
ifeq ($(strip $(xdg_config_home)),)
xdg_config_home := $(user_home)/.config
endif

plugins_dir := $(xdg_config_home)/terminator/plugins
dest_dir := $(plugins_dir)/clisnips

install:
	echo $(user_home)
	install -d $(dest_dir)
	install -m 0755 clisnips.py $(plugins_dir)/clisnips.py
	install -m 0755 clisnips_plugin.py $(plugins_dir)/clisnips_plugin.py
	find clisnips -type f -name "*.py" -or -name "*.ui" -or -name "*.xml" -or -name "*.lang" \
		| while read src; do \
		dest=`echo "$$src" | sed "s@.*@$(plugins_dir)/\0@"`; \
		install -Dm 0755 "$$src" "$$dest"; \
	done
	sed "s@__EXECPATH__@$(plugins_dir)/clisnips.py@" "org.ju1ius.CliSnips.service" \
		| sudo tee /usr/share/dbus-1/services/org.ju1ius.CliSnips.service

uninstall:
	rm -rf $(dest_dir)
	rm -f $(plugins_dir)/clisnips_plugin.py
	rm -f $(plugins_dir)/clisnips.py
	sudo rm -f /usr/share/dbus-1/services/org.ju1ius.CliSnips.service
