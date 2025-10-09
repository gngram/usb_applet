import gi
gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
from gi.repository import Gtk, AppIndicator3, GObject, GLib

from usb_panel.logger import logger
from usb_panel.api_client import APIClient



def set_target(level1_option, old_option, new_option):
    print(f"[set_target] {level1_option}: {old_option!r} → {new_option!r}", flush=True)

class VHotplugServer():
    def __init__(self, server_port=2000):
        self.server_port = server_port
        self.apiclient = APIClient(port=self.server_port)
        print("11111")
        self.apiclient.connect()
        print("222222222")
        self.device_map = {}
        self.refresh()


    def refresh(self):
        self.device_map.clear()
        devices = self.apiclient.usb_list()
        print(f"{devices}")
        unique_idx = 1
        if devices.get("result") == "ok":
            for dev in devices.get("usb_devices", []):
                if "device_node" in dev and "product_name" in dev:
                    product_name = dev.get("product_name")
                    if product_name is None:
                        continue

                    if product_name.isdigit():
                        product_name = "Unknown Device"
                    product_name = product_name.replace('_', " ")
                    if product_name not in self.device_map:
                        self.device_map[product_name] = dev
                    else:
                        product_name = product_name + "(" + str(unique_idx) + ")"
                        self.device_map[product_name] = dev
                        unique_idx += 1
        print(f"SSSSSSSSSSSSSS:{self.device_map}")
    def switch_vm(self, device, new_vm):
        self.apiclient.usb_detach(self.device_map[device]["device_node"])
        response = self.apiclient.usb_attach(self.device_map[device]["device_node"], new_vm)
        if (
            response.get("event", "") == "usb_attached"
            or response.get("result", "") == "ok"
        ):
            self.device_map[device]["vm"] = new_vm
            return True
        else:
            return False

    def eject_device(self, device):
        self.apiclient.usb_detach(self.device_map[device]["device_node"])
        self.device_map[device]["vm"] = None

class USBApplet:
    def __init__(self, port=2000):

        self.vhotplug = VHotplugServer(port)
        self.groups = {}

        self.indicator = AppIndicator3.Indicator.new(
            "usb-applet", "media-removable-symbolic",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        # Keep ONE menu instance alive; only rebuild its contents
        self.menu = Gtk.Menu()
        self.indicator.set_menu(self.menu)
        self._rebuild_menu_contents()

    def _clear_menu(self, menu: Gtk.Menu):
        # Remove all children safely
        for child in list(menu.get_children()):
            menu.remove(child)

    def _rebuild_menu_contents(self, *_):
        self._clear_menu(self.menu)
        self.groups.clear()

        for target, data in self.vhotplug.device_map.items():
            submenu = Gtk.Menu()
            selected = data.get("vm")
            self.groups[target] = []
            allowed_vms = data.get("allowed_vms",[])
            if len(allowed_vms) <= 1:
                continue
            if selected is None:
                selected = allowed_vms[0] 
            if allowed_vms[0] != "remove":
                allowed_vms.insert(0, "remove")
            print(f"AAAAAAAAAA{target} {allowed_vms}")
            for opt in allowed_vms:
                item = Gtk.CheckMenuItem.new_with_label(opt)
                item.set_draw_as_radio(True)
                item.set_active(opt == selected)
                hid = item.connect("toggled", self.on_option_toggled, target, opt)
                self.groups[target].append({"opt": opt, "item": item, "hid": hid})
                submenu.append(item)

            top_item = Gtk.MenuItem(label=target)
            top_item.set_submenu(submenu)
            self.menu.append(top_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        refresh_item = Gtk.MenuItem(label="Refresh")
        refresh_item.connect("activate", self.on_refresh)
        self.menu.append(refresh_item)

        self.menu.show_all()
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        return False

    def on_option_toggled(self, widget, target, option):
        if not widget.get_active():
            return
        old = self.vhotplug.device_map[target].get("vm")
        if old == option:
            return
        if option == "remove":
            self.vhotplug.eject_device(target)
            GLib.idle_add(self._rebuild_menu_contents)
        else:
            if self.vhotplug.switch_vm(target, option):
                GLib.idle_add(self._rebuild_menu_contents)

    def on_refresh(self, *_):
        self.vhotplug.refresh()
        GLib.idle_add(self._rebuild_menu_contents)

def start_usb_applet(port):
    GObject.threads_init()
    USBApplet(port)
    Gtk.main()
