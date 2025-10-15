# Copyright 2022-2025 TII (SSRC) and the Ghaf contributors
# SPDX-License-Identifier: Apache-2.0

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
from gi.repository import Gtk, AppIndicator3, GLib

from usb_ctl.logger import logger
from usb_ctl.api_client import APIClient

import threading
import subprocess


class USBApplet:
    def __init__(self, port=2000):
        self.device_map = {}
        self.radio_groups = {}
        self.apiclient = APIClient(port=port)
        self.apiclient.connect()

        self.indicator = AppIndicator3.Indicator.new(
            "usb-applet",
            "drive-removable-media-usb", 
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        self.menu = Gtk.Menu()
        self.indicator.set_menu(self.menu)
        self.devices_item = Gtk.MenuItem(label="Devices")
        self.menu.append(self.devices_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        self.settings_item = Gtk.MenuItem(label="Settings")
        self.settings_item.connect("activate", self.open_settings)
        self.menu.append(self.settings_item)

        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self.quit)
        self.menu.append(quit_item)

        self.menu.show_all()
        self.refresh_device_list(async_=True)
        self.devices_item.connect("activate", lambda *_: self.refresh_device_list(async_=True))

    def _build_devices_submenu(self):
        submenu = Gtk.Menu()
        self.radio_groups.clear()
        for dev_name, dev in self.device_map.items():
            label = f"{dev_name:<25}\n▶ {dev["vm"]}"
            dev_top = Gtk.MenuItem(label=label)
            self.radio_groups[dev_name] = dev_top
            dev_top.connect("activate",  self.refresh_device)
            submenu.append(dev_top)

        submenu.show_all()
        self.devices_item.set_submenu(submenu)
            
    def open_settings(self, *_):
        result = subprocess.run(["usb_settings"], capture_output=True, text=True, check=True)
        #self.devices_item.get_submenu().cancel()
        #self.menu.popdown()
        Gtk.MenuShell.deactivate(self.menu)

        
        print("PPPPPPPPPPPPPP")
        logger.info("Command output:")
        logger.info(result.stdout)
        logger.info(f"Command exited with code: {result.returncode}")

    def quit(self, *_):
        Gtk.main_quit()

    def refresh_device_list(self, async_=True):
        def _fetch_and_update():
            try:
                devs = self.apiclient.get_devices_pretty()
            except Exception as e:
                logger.exception("Failed fetching devices")
                self._error("Server Error", f"Device fetch failed: {e}")
                return

            def _apply():
                self.device_map = devs or {}
                self.radio_groups.clear()
                self._build_devices_submenu()
                return False
            GLib.idle_add(_apply)

        if async_:
            threading.Thread(target=_fetch_and_update, daemon=True).start()
        else:
            _fetch_and_update()

    def _notify_error(self, title: str, msg: str) -> None:
        dialog = Gtk.MessageDialog(
            parent=None,
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            message_format=title,
        )
        dialog.format_secondary_text(msg)
        dialog.run()
        dialog.destroy()

    def refresh_device(self, widget):
        l = widget.get_label()
        self.devices_item.get_submenu().popdown()
        self.menu.popdown()
        name, _ = l.split('\n')
        name = name.strip()
        dev = self.device_map.get(name, None)
        if dev is None:
            GLib.idle_add(self._notify_error, "Device Error", "Not able to access device")
            return
        if len(dev.get('allowed_vms',[])) < 2:
            self._notify_error("Device Error", "Operation not permitted")
            return
        
        cmd = [
            "usb_device",
            "--title", "Device Setting",
            "--device_node", dev.get('device_node', ''),
            "--product_name", name,
            "--allowed_vms", *dev.get('allowed_vms', ''),
        ]

        selected = dev.get('vm', None)
        if selected:
            cmd = cmd + ["--vm", selected]

        logger.debug(cmd)
        result = subprocess.run(cmd,  capture_output=True, text=True, check=True)
        logger.debug(f"usb_device::STDOUT:\n{result.stdout}")
        logger.debug(f"usb_device::STDERR:\n{result.stderr}")

        

_app_instance = None

def start_usb_applet(port=2000):
    global _app_instance
    _app_instance = USBApplet(port=port)
    Gtk.main()
