import unittest
from unittest.mock import patch

from voicemeeter_sdk import VoicemeeterClient, VoicemeeterError


class VoicemeeterClientTests(unittest.TestCase):
    def test_parse_version_from_int(self):
        self.assertEqual(VoicemeeterClient._decode_version(0x01020304), (1, 2, 3, 4))

    def test_should_raise_on_negative_result(self):
        client = VoicemeeterClient.__new__(VoicemeeterClient)
        with self.assertRaises(VoicemeeterError):
            client._raise_for_result(-1)

    def test_resolve_dll_path_uses_64bit_name_for_x64(self):
        with patch("voicemeeter_sdk.winreg.OpenKey") as open_key, patch(
            "voicemeeter_sdk.winreg.QueryValueEx"
        ) as query_value_ex, patch("voicemeeter_sdk.winreg.CloseKey"):
            open_key.return_value = object()
            query_value_ex.return_value = ("C:\\Program Files\\VB\\Voicemeeter\\Voicemeeter.exe", 0)
            self.assertTrue(VoicemeeterClient._resolve_dll_path(64).endswith("VoicemeeterRemote64.dll"))

    def test_resolve_dll_path_uses_32bit_name_for_x86(self):
        with patch("voicemeeter_sdk.winreg.OpenKey") as open_key, patch(
            "voicemeeter_sdk.winreg.QueryValueEx"
        ) as query_value_ex, patch("voicemeeter_sdk.winreg.CloseKey"):
            open_key.return_value = object()
            query_value_ex.return_value = ("C:\\Program Files (x86)\\VB\\Voicemeeter\\Voicemeeter.exe", 0)
            self.assertTrue(VoicemeeterClient._resolve_dll_path(32).endswith("VoicemeeterRemote.dll"))


if __name__ == "__main__":
    unittest.main()
