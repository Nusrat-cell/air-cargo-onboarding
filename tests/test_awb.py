from cargo import awb


def test_check_digit_is_serial_mod_7():
    assert awb.check_digit("1234567") == 1234567 % 7


def test_make_and_validate_roundtrip():
    number = awb.make("176", 1234567)
    assert awb.is_valid(number)
    assert awb.is_valid(number.replace("-", ""))


def test_wrong_check_digit_or_format_is_invalid():
    good = awb.make("176", 1234567)
    bad = good[:-1] + str((int(good[-1]) + 1) % 7)
    assert not awb.is_valid(bad)
    assert not awb.is_valid("17-1234567")
    assert not awb.is_valid("abc")
