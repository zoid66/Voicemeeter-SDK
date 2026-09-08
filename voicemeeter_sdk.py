import ctypes
import os
import sys
import winreg


class VoicemeeterError(RuntimeError):
    """Raised when a Voicemeeter API call returns an error code."""


class VoicemeeterClient:
    """A small ctypes wrapper around the native VoicemeeterRemote DLL."""

    INSTALLER_UNINST_KEY = "VB:Voicemeeter {17359A74-1236-5467}"
    UNINSTALL_REGISTRY_PATH = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"

    def __init__(self, dll_path=None, arch_bits=None):
        self.dll_path = dll_path or self._resolve_dll_path(arch_bits or (ctypes.sizeof(ctypes.c_void_p) * 8))
        self._lib = ctypes.WinDLL(self.dll_path)
        self._bind_functions()

    def _bind_functions(self):
        self.login = self._lib.VBVMR_Login
        self.login.restype = ctypes.c_long
        self.login.argtypes = []

        self.logout = self._lib.VBVMR_Logout
        self.logout.restype = ctypes.c_long
        self.logout.argtypes = []

        self.run_voicemeeter = self._lib.VBVMR_RunVoicemeeter
        self.run_voicemeeter.restype = ctypes.c_long
        self.run_voicemeeter.argtypes = [ctypes.c_long]

        self.get_voicemeeter_type = self._lib.VBVMR_GetVoicemeeterType
        self.get_voicemeeter_type.restype = ctypes.c_long
        self.get_voicemeeter_type.argtypes = [ctypes.POINTER(ctypes.c_long)]

        self.get_voicemeeter_version = self._lib.VBVMR_GetVoicemeeterVersion
        self.get_voicemeeter_version.restype = ctypes.c_long
        self.get_voicemeeter_version.argtypes = [ctypes.POINTER(ctypes.c_long)]

        self.is_parameters_dirty = self._lib.VBVMR_IsParametersDirty
        self.is_parameters_dirty.restype = ctypes.c_long
        self.is_parameters_dirty.argtypes = []

        self.get_parameter_float = self._lib.VBVMR_GetParameterFloat
        self.get_parameter_float.restype = ctypes.c_long
        self.get_parameter_float.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_float)]

        self.set_parameter_float = self._lib.VBVMR_SetParameterFloat
        self.set_parameter_float.restype = ctypes.c_long
        self.set_parameter_float.argtypes = [ctypes.c_char_p, ctypes.c_float]

        self.set_parameters = self._lib.VBVMR_SetParameters
        self.set_parameters.restype = ctypes.c_long
        self.set_parameters.argtypes = [ctypes.c_char_p]

        self.get_parameter_string_a = self._lib.VBVMR_GetParameterStringA
        self.get_parameter_string_a.restype = ctypes.c_long
        self.get_parameter_string_a.argtypes = [ctypes.c_char_p, ctypes.c_char_p]

        self.logout = self._lib.VBVMR_Logout
        self.logout.restype = ctypes.c_long
        self.logout.argtypes = []

    @staticmethod
    def _decode_version(raw_version):
        return (
            (raw_version >> 24) & 0xFF,
            (raw_version >> 16) & 0xFF,
            (raw_version >> 8) & 0xFF,
            raw_version & 0xFF,
        )

    @staticmethod
    def _raise_for_result(result):
        if result == 0:
            return
        raise VoicemeeterError(f"Voicemeeter API returned error code {result}")

    @staticmethod
    def _resolve_dll_path(arch_bits=64):
        install_dir = VoicemeeterClient._find_install_dir()
        dll_name = "VoicemeeterRemote64.dll" if int(arch_bits) == 64 else "VoicemeeterRemote.dll"
        return os.path.join(install_dir, dll_name)

    @staticmethod
    def _find_install_dir():
        registry_path = f"{VoicemeeterClient.UNINSTALL_REGISTRY_PATH}\\{VoicemeeterClient.INSTALLER_UNINST_KEY}"
        for access_flags in (0, winreg.KEY_WOW64_32KEY):
            key = None
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path, 0, winreg.KEY_READ | access_flags)
                value, _ = winreg.QueryValueEx(key, "UninstallString")
                if value:
                    value = str(value).strip().strip('"')
                    return os.path.dirname(value)
            except FileNotFoundError:
                continue
            finally:
                if key is not None:
                    winreg.CloseKey(key)
        raise VoicemeeterError("Voicemeeter is not installed or the registry key could not be read.")

    def login(self):
        raise AttributeError("The native function bindings are not initialized.")

    def logout(self):
        raise AttributeError("The native function bindings are not initialized.")

    def run_voicemeeter(self, v_type):
        result = self._lib.VBVMR_RunVoicemeeter(v_type)
        self._raise_for_result(result)
        return result

    def get_voicemeeter_type(self):
        value = ctypes.c_long()
        result = self._lib.VBVMR_GetVoicemeeterType(ctypes.byref(value))
        self._raise_for_result(result)
        return int(value.value)

    def get_voicemeeter_version(self):
        value = ctypes.c_long()
        result = self._lib.VBVMR_GetVoicemeeterVersion(ctypes.byref(value))
        self._raise_for_result(result)
        return self._decode_version(int(value.value))

    def is_parameters_dirty(self):
        result = self._lib.VBVMR_IsParametersDirty()
        self._raise_for_result(result)
        return result

    def get_parameter_float(self, parameter_name):
        value = ctypes.c_float()
        result = self._lib.VBVMR_GetParameterFloat(parameter_name.encode("ascii"), ctypes.byref(value))
        self._raise_for_result(result)
        return float(value.value)

    def set_parameter_float(self, parameter_name, value):
        result = self._lib.VBVMR_SetParameterFloat(parameter_name.encode("ascii"), ctypes.c_float(value))
        self._raise_for_result(result)
        return result

    def set_parameters(self, script):
        result = self._lib.VBVMR_SetParameters(script.encode("ascii"))
        self._raise_for_result(result)
        return result

    def get_parameter_string(self, parameter_name):
        buffer = ctypes.create_string_buffer(512)
        result = self._lib.VBVMR_GetParameterStringA(parameter_name.encode("ascii"), buffer)
        self._raise_for_result(result)
        return buffer.value.decode("ascii", errors="replace")


if __name__ == "__main__":
    client = VoicemeeterClient()
    try:
        client.login()
        print("Voicemeeter type:", client.get_voicemeeter_type())
        print("Voicemeeter version:", client.get_voicemeeter_version())
        client.logout()
    except VoicemeeterError as exc:
        print(exc)
        sys.exit(1)
