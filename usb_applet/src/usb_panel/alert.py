#!/usr/bin/env python3
from gi import require_version
require_version("Gtk", "3.0")
require_version("Gdk", "3.0")

from gi.repository import Gtk, Gdk
from usb_panel.api_client import APIClient
from usb_panel.logger import logger
import threading

SELECT = "Select"
ALLOWED = "allowed_vms"
CURRENT = "vm"
NODE = "device_node"
PRODUCT = "product_name"

class AlertWindow(Gtk.Window):
    def __init__(self, device_info, apiclient):
        self.device_info = device_info
        Gtk.Window.__init__(self, title="USB Notification")
        self.set_default_size(360, 140)

        # ---- CSS ----
        self.apiclient = apiclient
        css = b"""
        label.alert {
            background-color: #fff3cd;
            color: #856404;
            padding: 6px 10px;
            border-radius: 8px;
            font-weight: bold;
        }
        """
        logger.info(f"Alert WIndo {device_info}")
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        screen = Gdk.Screen.get_default()
        if screen is not None:
            Gtk.StyleContext.add_provider_for_screen(
                screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)
        vbox.set_margin_start(12)
        vbox.set_margin_end(12)
        self.add(vbox)

        # ---- Header row: icon + label ----
        header_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        # Use a stock dialog-warning icon (yellow triangle)
        icon = Gtk.Image.new_from_icon_name("dialog-warning", Gtk.IconSize.BUTTON)
        header_row.pack_start(icon, False, False, 0)

        header = Gtk.Label(label="New device alert")
        header.get_style_context().add_class("alert")
        header.set_xalign(0.0)
        header_row.pack_start(header, False, False, 0)

        vbox.pack_start(header_row, False, False, 0)

        # ---- Device name row ----
        name_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        name_lbl = Gtk.Label(label="Device:")
        name_lbl.set_xalign(0.0)
        value_lbl = Gtk.Label(label=device_info.get(PRODUCT, "<unknown>"))
        value_lbl.set_xalign(0.0)
        name_row.pack_start(name_lbl, False, False, 0)
        name_row.pack_start(value_lbl, False, False, 0)
        vbox.pack_start(name_row, False, False, 0)

        # ---- Dropdown ----
        combo_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        combo_lbl = Gtk.Label(label="Allowed VM:")
        combo_lbl.set_xalign(0.0)
        self.combo = Gtk.ComboBoxText()

        options = device_info.get(ALLOWED, [])
        current = device_info.get(CURRENT, "")
        if current == "":
            options.append(SELECT)
            current = SELECT
        for i, opt in enumerate(options):
            self.combo.append_text(opt)
            if opt == current:
                active_index = i

        if options:
            self.combo.set_active(active_index)

        self.combo.connect("changed", self.on_changed)

        combo_row.pack_start(combo_lbl, False, False, 0)
        combo_row.pack_start(self.combo, False, False, 0)
        vbox.pack_start(combo_row, False, False, 0)

        btn = Gtk.Button(label="Close")
        btn.connect("clicked", lambda *_: self.close())
        vbox.pack_end(btn, False, False, 0)

        self.connect("destroy", Gtk.main_quit)
        self.show_all()

    def on_changed(self, combo):
        new = combo.get_active_text()
        new = "" if new == SELECT else new
        if new == self.device_info[CURRENT]:
            return
        if self.device_info[CURRENT] != "" or new == "":
            self.apiclient.usb_detach(self.device_info[NODE])
        if new != "":
            response = self.apiclient.usb_attach(self.device_info[NODE], new)
            if (
                response.get("event", "") != "usb_attached"
                and response.get("result", "") != "ok"
            ):
                return
        self.device_info[CURRENT] = new

class USBDeviceNotification:
    def __init__(self, server_port=2000):
        th, apiclient = APIClient.recv_notifications(
            callback=self.notify_user, port=server_port, cid=2, reconnect_delay=3
        )
        self.apiclient = apiclient
        self.thread = th
        logger.info("Thread created")

    def monitor(self):
        self.thread.join()

    def notify_user(self, msg):
        logger.info(f"New device notification: {msg}")
        dev = msg.get("usb_device", {})
        allowed = msg.get(ALLOWED, [])
        logger.info(f"New device notification: {dev} --- {allowed} -- {len(allowed)}")
        #if len(allowed) < 2:
        #    return
        dev[ALLOWED] = ["business-vm", "chrome-vm"]
        th = threading.Thread(target=self.show_notif_window, args=(dev, self.apiclient))
        th.start()
        #th.join()

    def show_notif_window(self, device, apiclient):
        win = AlertWindow(device, apiclient)
        Gtk.main()


