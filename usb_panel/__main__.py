from usb_panel.applet import Demo  # or USBApplet directly
import sys

def main():
    app = Demo()
    sys.exit(app.run())

