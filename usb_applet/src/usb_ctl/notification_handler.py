# Copyright 2022-2025 TII (SSRC) and the Ghaf contributors
# SPDX-License-Identifier: Apache-2.0

import threading
from usb_ctl.api_client import APIClient
from usb_ctl.vm_selection import show_device_setting

import json 
from usb_ctl.logger import logger

def format_product_name(dev):
    product_name = dev.get('product_name', None)
    if product_name is None:
        dev['product_name'] = "<unknown device>"
    else:
        product_name = product_name.replace('_', ' ')
        dev['product_name'] = product_name[:20]

class USBDeviceNotification:
    def __init__(self, server_port=2000):
        th, apiclient = APIClient.recv_notifications(
            callback=self.notify_user, port=server_port, cid=2, reconnect_delay=3
        )
        self.apiclient = apiclient
        th.join()

    def notify_user(self, msg):
        logger.debug(f"Device notification: {json.dumps(msg, indent=4)}")
        event = msg.get('event', '')
        if event != 'usb_select_vm':
            logger.info(f"Device notification <{event}> ignored!")
            return
        dev = msg.get("usb_device", {})
        allowed = msg.get("allowed_vms", [])
        if len(allowed) < 2:
            logger.error(f"VMs not available to make choice")
            return
        dev["allowed_vms"] = allowed
        format_product_name(dev)
        th = threading.Thread(target=self.show_notif_window, args=(dev, self.apiclient), daemon = True)
        th.start()
        #th.join()

    def show_notif_window(self, device, apiclient):
        show_device_setting(device, title = "Device Notification", apiclient = apiclient)
