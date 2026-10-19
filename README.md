# Voicemeeter Control Panel

A Python desktop control panel for Voicemeeter Remote API, built with PyWebView.

# Python desktop control panel

The control panel provides:

- connection and engine information;
- eight strip and eight bus faders;
- mute and mono controls;
- live connection status;
- a command script box for `VBVMR_SetParameters`.

The native Voicemeeter application must be installed on Windows. From a Python 3.11+ environment, install the project and launch the app:

```powershell
python -m pip install -e .
python voicemeeter_app.py
```

The Python UI is an additional application; it does not replace the Voicemeeter mixer. The HTML/CSS frontend communicates with the native DLL only through `voicemeeter_app.py`, which keeps the Windows API calls in Python and the presentation in the browser view.

# Licensing

All source code is free to use in any kind of project interacting with Voicemeeter through the voicemeeterremote DLL or VBAN protocol.

Copyright (c) 2021 Vincent Burel

# Links

- Download Voicemeeter: www.voicemeeter.com
- VBAN Protocol: https://vb-audio.com/Voicemeeter/vban.htm
- VB-Audio Support page: https://vb-audio.com/Services/support.htm
