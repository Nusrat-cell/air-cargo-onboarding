"""Air waybill (AWB) numbers: 3 digit airline prefix, 7 digit serial, 1 check digit (serial modulo 7)."""
import re

_AWB = re.compile(r"^(\d{3})-?(\d{7})(\d)$")


def parse(awb: str):
    """Return (prefix, serial, check) or None when the format is wrong."""
    m = _AWB.match(str(awb).strip())
    if not m:
        return None
    return m.group(1), m.group(2), int(m.group(3))


def check_digit(serial: str) -> int:
    return int(serial) % 7


def is_valid(awb: str) -> bool:
    parts = parse(awb)
    if parts is None:
        return False
    _, serial, check = parts
    return check_digit(serial) == check


def make(prefix: str, serial: int) -> str:
    s = f"{serial:07d}"
    return f"{prefix}-{s}{check_digit(s)}"
