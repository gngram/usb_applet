# Copyright 2022-2025 TII (SSRC) and the Ghaf contributors
# SPDX-License-Identifier: Apache-2.0

from usb_ctl import applet 
from usb_ctl.logger import setup_logger
import argparse

def main():
    parser = argparse.ArgumentParser(description="USB Device Applet")
    parser.add_argument("--loglevel", type=str, default="info", help="Log level")
    parser.add_argument("--port", type=int, default=2000, help="vHotplg server port")
    args = parser.parse_args()
    setup_logger(args.loglevel)
    applet.start_usb_applet(args.port)
    alert.main()
    
