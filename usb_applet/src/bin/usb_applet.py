from usb_panel import applet, alert 
from usb_panel.logger import setup_logger
import logging 

logger = logging.getLogger("vhotplug_client")
import sys

def main():
    #applet.start_usb_applet(2000)
    setup_logger("info")
    notifications = alert.USBDeviceNotification(server_port = 2000)
    notifications.monitor()

