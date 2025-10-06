#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio

# ---------------- backend hooks ----------------
def get_options():
    return {
        "usb_vamera": {"level2_options": ["hello", "world"], "selected": "off"},
        "ajhsasa asasasas": {"level2_options": ["off", "ro", "rw"], "selected": "ro"},
        "VM-Cssssssssssssssssss": {"level2_options": ["off", "ro", "ganga", "ram"], "selected": "rw"},
    }

def set_target(level1_option, selected_option):
    print(f"[set_target] {level1_option} -> {selected_option}", flush=True)

# ---------------- applet ----------------
class USBApplet(Gtk.MenuButton):
    def __init__(self):
        super().__init__()
        self._model = {}
        self._current_l1 = None

        # Build a robust icon (fallbacks) and *set as child* to avoid theme issues.
        icon = Gio.ThemedIcon.new_from_names([
            "drive-removable-media-usb-symbolic",   # primary
            "media-removable-symbolic",             # fallback
            "drive-removable-media-symbolic"        # fallback
        ])
        img = Gtk.Image.new_from_gicon(icon)
        img.set_pixel_size(18)  # small panel-like size; tweak to your panel’s scale
        self.set_has_frame(False)
        self.set_tooltip_text("USB Options")
        self.set_child(img)

        # Popover content
        pop = Gtk.Popover()
        self.set_popover(pop)

        outer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        outer.set_margin_start(10)
        outer.set_margin_end(10)
        outer.set_margin_top(10)
        outer.set_margin_bottom(10)
        pop.set_child(outer)

        # Left: Level-1
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left_label = Gtk.Label(label="Targets"); left_label.set_xalign(0.0); left_label.add_css_class("heading")
        self._l1 = Gtk.ListBox()
        self._l1.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._l1.connect("row-selected", self._on_l1_selected)
        left_box.append(left_label); left_box.append(self._l1)

        # Right: Level-2
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        right_label = Gtk.Label(label="Options"); right_label.set_xalign(0.0); right_label.add_css_class("heading")
        self._l2 = Gtk.ListBox()
        self._l2.set_selection_mode(Gtk.SelectionMode.SINGLE)
        # IMPORTANT: in GTK4, activation is on the list, not the row
        self._l2.connect("row-activated", self._on_l2_activated)
        right_box.append(right_label); right_box.append(self._l2)

        outer.append(left_box)
        outer.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        outer.append(right_box)

        pop.connect("show", lambda *_: self.refresh())

    # ------- model / UI -------
    def refresh(self):
        self._model = get_options() or {}
        if self._current_l1 not in self._model:
            self._current_l1 = next(iter(self._model), None)
        self._rebuild_l1()
        self._rebuild_l2()

    def _rebuild_l1(self):
        for ch in list(self._l1): self._l1.remove(ch)
        for key in self._model.keys():
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            lbl = Gtk.Label(label=key); lbl.set_xalign(0.0)
            if key == self._current_l1: lbl.add_css_class("title-3")
            box.append(lbl)
            row.set_child(box)
            row._l1_key = key  # attach data
            row.set_activatable(True)
            self._l1.append(row)
        # select current
        for row in self._l1:
            if getattr(row, "_l1_key", None) == self._current_l1:
                self._l1.select_row(row); break

    def _rebuild_l2(self):
        for ch in list(self._l2): self._l2.remove(ch)
        if not self._current_l1 or self._current_l1 not in self._model:
            return
        entry = self._model[self._current_l1]
        opts = entry.get("level2_options", [])
        sel = entry.get("selected")

        for opt in opts:
            row = Gtk.ListBoxRow()
            h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

            # Reliable tick: disabled CheckButton to show state consistently across themes
            tick = Gtk.CheckButton()
            tick.set_active(opt == sel)
            tick.set_sensitive(False)   # not interactive, just an indicator
            tick.set_can_focus(False)
            h.append(tick)

            lbl = Gtk.Label(label=str(opt)); lbl.set_xalign(0.0); lbl.set_hexpand(True)
            h.append(lbl)

            row.set_child(h)
            row._l2_value = opt
            row.set_selectable(True)   # so row-activated can trigger
            self._l2.append(row)

        # keep selection off by default (visual clarity)
        self._l2.unselect_all()

    # ------- signals -------
    def _on_l1_selected(self, _listbox, row):
        if not row: return
        key = getattr(row, "_l1_key", None)
        if key and key != self._current_l1:
            self._current_l1 = key
            self._rebuild_l1()
            self._rebuild_l2()

    def _on_l2_activated(self, listbox, row):
        if not row or not self._current_l1: return
        opt = getattr(row, "_l2_value", None)
        current = self._model.get(self._current_l1, {}).get("selected")
        if not opt or opt == current: return
        set_target(self._current_l1, opt)
        # update indicator immediately
        self._model[self._current_l1]["selected"] = opt
        self._rebuild_l2()

# ---- quick tester (optional) ----
class Demo(Gtk.Application):
    def __init__(self): super().__init__(application_id="dev.example.usb-applet-fixed")
    def do_activate(self):
        win = Gtk.ApplicationWindow(application=self); win.set_default_size(260, 60)
        hb = Gtk.HeaderBar(); win.set_titlebar(hb)
        hb.pack_end(USBApplet()); win.present()

if __name__ == "__main__":
    app = Demo(); raise SystemExit(app.run())

