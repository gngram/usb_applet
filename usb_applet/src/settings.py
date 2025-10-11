#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, Pango

# ---------------- backend hooks ----------------
def get_options():
    # Level1 -> submenu options + current selection
    return {
        "USB Camera":  {"level2_options": ["hello", "world"], "selected": "hello"},
        "Readonly VM": {"level2_options": ["off", "ro", "rw"], "selected": "ro"},
        "Target VM":   {"level2_options": ["off", "ro", "ganga", "ram"], "selected": "ram"},
    }

def set_target(level1_option, selected_option):
    print(f"[set_target] {level1_option} -> {selected_option}", flush=True)

# ---------------- popover with radio options ----------------
class OptionsPopover(Gtk.Popover):
    def __init__(self, parent_widget, title, options, selected, on_chosen):
        super().__init__(has_arrow=True)
        self.set_parent(parent_widget)  # anchor popover to the clicked row
        self._selected = selected
        self._on_chosen = on_chosen

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(10); box.set_margin_bottom(10)
        box.set_margin_start(12); box.set_margin_end(12)
        self.set_child(box)

        head = Gtk.Label()
        # Gtk.utils.escape_markup exists in GTK4; if not, a simple replace works
        safe = (title
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))
        head.set_markup(f"<b>{safe}</b>")
        head.set_xalign(0.0)
        box.append(head)

        # Radio group using CheckButtons (GTK4-friendly)
        group_head = None
        for opt in options:
            btn = Gtk.CheckButton.new_with_label(str(opt))
            if group_head is None:
                group_head = btn
            else:
                btn.set_group(group_head)
            btn.set_active(opt == selected)
            btn.connect("toggled", self._on_toggled, opt)
            box.append(btn)

        # ESC to close
        kc = Gtk.EventControllerKey()
        kc.connect("key-pressed", self._on_key)
        self.add_controller(kc)

    def _on_key(self, _ctl, keyval, *_):
        if keyval == Gdk.KEY_Escape:
            self.popdown()
            return True
        return False

    def _on_toggled(self, btn, opt):
        if not btn.get_active():
            return
        if opt != self._selected:
            self._selected = opt
            self._on_chosen(opt)
        self.popdown()

# ---------------- main window ----------------
class DisplayOptionsWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Displays")
        self.set_default_size(700, 520)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        root.set_margin_top(20); root.set_margin_bottom(20)
        root.set_margin_start(22); root.set_margin_end(22)
        self.set_child(root)

        title = Gtk.Label(label="Displays")
        title.add_css_class("title-1")
        title.set_xalign(0.0)
        root.append(title)

        section_lbl = Gtk.Label(label="Display Options")
        section_lbl.add_css_class("title-3")
        section_lbl.set_xalign(0.0)
        root.append(section_lbl)

        self.list = Gtk.ListBox()
        self.list.add_css_class("boxed-list")
        # Important: make rows activatable
        self.list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list.set_activate_on_single_click(True)
        self.list.connect("row-activated", self._on_row_activated)

        root.append(self.list)

        self.status = Gtk.Label()
        self.status.set_xalign(0.0)
        self.status.add_css_class("dim-label")
        root.append(self.status)

        self._model = {}
        self.refresh()

        # ESC closes window
        kc = Gtk.EventControllerKey()
        kc.connect("key-pressed", self._on_key)
        self.add_controller(kc)

    # ----- data/UI -----
    def refresh(self):
        self._model = get_options() or {}
        self._rebuild_rows()
        self._update_status()

    def _rebuild_rows(self):
        for ch in list(self.list):
            self.list.remove(ch)

        for key, data in self._model.items():
            self.list.append(self._build_row(key, data))

        self.list.show()

    def _build_row(self, l1_key, data):
        row = Gtk.ListBoxRow()
        row._l1_key = l1_key
        row.set_activatable(True)

        h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        h.set_margin_top(14); h.set_margin_bottom(14)
        h.set_margin_start(16); h.set_margin_end(16)

        # Left title like Settings
        title = Gtk.Label(label=l1_key)
        title.set_xalign(0.0)
        title.set_hexpand(True)
        title.set_ellipsize(Pango.EllipsizeMode.END)
        title.set_max_width_chars(40)
        h.append(title)

        # Right: current value + chevron
        right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        right.set_halign(Gtk.Align.END)
        value = Gtk.Label(label=str(data.get("selected")))
        value.add_css_class("dim-label")
        right.append(value)
        chevron = Gtk.Image.new_from_icon_name("pan-down-symbolic")
        right.append(chevron)
        row._value_label = value

        h.append(right)
        row.set_child(h)

        # Extra: direct click handler (in case row-activated doesn't fire)
        click = Gtk.GestureClick()
        click.connect("released", lambda *_: self._open_popover_for_row(row))
        row.add_controller(click)

        return row

    def _open_popover_for_row(self, row):
        key = getattr(row, "_l1_key", None)
        if not key:
            return
        entry = self._model.get(key, {})
        options = entry.get("level2_options", [])
        selected = entry.get("selected")

        pop = OptionsPopover(
            parent_widget=row,
            title=key,
            options=options,
            selected=selected,
            on_chosen=lambda opt, k=key, r=row: self._apply_choice(k, opt, r),
        )
        pop.popup()

    # listbox activation path
    def _on_row_activated(self, _lb, row):
        if row:
            self._open_popover_for_row(row)

    def _apply_choice(self, l1_key, opt, row):
        cur = self._model.get(l1_key, {}).get("selected")
        if opt == cur:
            return
        set_target(l1_key, opt)
        self._model[l1_key]["selected"] = opt
        if hasattr(row, "_value_label"):
            row._value_label.set_text(str(opt))
        self._update_status()

    def _update_status(self):
        self.status.set_text(" | ".join(f"{k}: {v.get('selected')}" for k, v in self._model.items()))

    def _on_key(self, _ctl, keyval, *_):
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False

# ---- application ----
class Demo(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="dev.example.cosmic-display-options")

    def do_activate(self, *_):
        win = DisplayOptionsWindow(application=self)
        win.present()

if __name__ == "__main__":
    app = Demo()
    raise SystemExit(app.run())

