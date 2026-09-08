import sys

from voicemeeter_sdk import VoicemeeterClient, VoicemeeterError


def main():
    client = VoicemeeterClient()
    try:
        status = client.login()
        print(f"Login returned {status}")
        print("Type:", client.get_voicemeeter_type())
        print("Version:", client.get_voicemeeter_version())
        print("Dirty:", client.is_parameters_dirty())
    except VoicemeeterError as exc:
        print(f"Voicemeeter error: {exc}")
        return 1
    finally:
        try:
            client.logout()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
