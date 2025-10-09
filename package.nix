# Copyright 2022-2025 TII (SSRC) and the Ghaf contributors
# SPDX-License-Identifier: Apache-2.0

{
  buildPythonApplication,
  setuptools,
  wheel,
  gtk3,
  wrapGAppsHook,
  pygobject3,
}:

buildPythonApplication {
  pname = "ghaf_usb_applet";
  version = "0.1.0";
  src = ./ghaf_usb_applet;
  pyproject = true;

  nativeBuildInputs = [
    setuptools
    wheel
    gobject-introspection
    wrapGAppsHook
  ];

  propagatedBuildInputs = [
    pygobject3
  ];

  buildInputs = [
    gtk3
    gsettings-desktop-schemas
  ];
}
