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
        self._VBVMR_Login = self._lib.VBVMR_Login
        self._VBVMR_Login.restype = ctypes.c_long
        self._VBVMR_Login.argtypes = []

        self._VBVMR_Logout = self._lib.VBVMR_Logout
        self._VBVMR_Logout.restype = ctypes.c_long
        self._VBVMR_Logout.argtypes = []

        self._VBVMR_RunVoicemeeter = self._lib.VBVMR_RunVoicemeeter
        self._VBVMR_RunVoicemeeter.restype = ctypes.c_long
        self._VBVMR_RunVoicemeeter.argtypes = [ctypes.c_long]

        self._VBVMR_GetVoicemeeterType = self._lib.VBVMR_GetVoicemeeterType
        self._VBVMR_GetVoicemeeterType.restype = ctypes.c_long
        self._VBVMR_GetVoicemeeterType.argtypes = [ctypes.POINTER(ctypes.c_long)]

        self._VBVMR_GetVoicemeeterVersion = self._lib.VBVMR_GetVoicemeeterVersion
        self._VBVMR_GetVoicemeeterVersion.restype = ctypes.c_long
        self._VBVMR_GetVoicemeeterVersion.argtypes = [ctypes.POINTER(ctypes.c_long)]

        self._VBVMR_IsParametersDirty = self._lib.VBVMR_IsParametersDirty
        self._VBVMR_IsParametersDirty.restype = ctypes.c_long
        self._VBVMR_IsParametersDirty.argtypes = []

        self._VBVMR_GetParameterFloat = self._lib.VBVMR_GetParameterFloat
        self._VBVMR_GetParameterFloat.restype = ctypes.c_long
        self._VBVMR_GetParameterFloat.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_float)]

        self._VBVMR_SetParameterFloat = self._lib.VBVMR_SetParameterFloat
        self._VBVMR_SetParameterFloat.restype = ctypes.c_long
        self._VBVMR_SetParameterFloat.argtypes = [ctypes.c_char_p, ctypes.c_float]

        self._VBVMR_SetParameters = self._lib.VBVMR_SetParameters
        self._VBVMR_SetParameters.restype = ctypes.c_long
        self._VBVMR_SetParameters.argtypes = [ctypes.c_char_p]

        self._VBVMR_GetParameterStringA = self._lib.VBVMR_GetParameterStringA
        self._VBVMR_GetParameterStringA.restype = ctypes.c_long
        self._VBVMR_GetParameterStringA.argtypes = [ctypes.c_char_p, ctypes.c_char_p]

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
        result = self._VBVMR_Login()
        if result < 0:
            self._raise_for_result(result)
        return result

    def logout(self):
        result = self._VBVMR_Logout()
        self._raise_for_result(result)
        return result

    def run_voicemeeter(self, v_type):
        result = self._VBVMR_RunVoicemeeter(v_type)
        self._raise_for_result(result)
        return result

    def get_voicemeeter_type(self):
        value = ctypes.c_long()
        result = self._VBVMR_GetVoicemeeterType(ctypes.byref(value))
        self._raise_for_result(result)
        return int(value.value)

    def get_voicemeeter_version(self):
        value = ctypes.c_long()
        result = self._VBVMR_GetVoicemeeterVersion(ctypes.byref(value))
        self._raise_for_result(result)
        return self._decode_version(int(value.value))

    def is_parameters_dirty(self):
        result = self._VBVMR_IsParametersDirty()
        self._raise_for_result(result)
        return result

    def get_parameter_float(self, parameter_name):
        value = ctypes.c_float()
        result = self._VBVMR_GetParameterFloat(parameter_name.encode("ascii"), ctypes.byref(value))
        self._raise_for_result(result)
        return float(value.value)

    def set_parameter_float(self, parameter_name, value):
        result = self._VBVMR_SetParameterFloat(parameter_name.encode("ascii"), ctypes.c_float(value))
        self._raise_for_result(result)
        return result

    def set_parameters(self, script):
        result = self._VBVMR_SetParameters(script.encode("ascii"))
        self._raise_for_result(result)
        return result

    def get_parameter_string(self, parameter_name):
        buffer = ctypes.create_string_buffer(512)
        result = self._VBVMR_GetParameterStringA(parameter_name.encode("ascii"), buffer)
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
