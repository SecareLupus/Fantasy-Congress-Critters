import pytest

from pipeline import auth
from pipeline.play import Problem


def test_passwords_hash_with_a_salt_and_check():
    a, b = auth.hash_password("correct horse"), auth.hash_password("correct horse")
    assert a != b and a.startswith("scrypt$")
    assert auth.check_password("correct horse", a)
    assert not auth.check_password("correct horsE", a)
    assert not auth.check_password("correct horse", "not a hash")


def test_invite_codes_read_the_same_however_they_are_typed():
    code = auth.new_invite_code()
    assert len(code) == 14 and not set(code.replace("-", "")) - set(auth.CODE_ALPHABET)
    assert auth.normalize_code("k7qm 3xpa hw2n") == auth.normalize_code(" K7QM3XPAHW2N") == "K7QM-3XPA-HW2N"


def test_new_accounts_need_a_plain_username_and_a_long_password():
    auth.check_new_account("Ann_B-2", "ten chars!")
    for username, password in (("ab", "long enough pw"), ("has space", "long enough pw"),
                               ("ann", "too short"), ("annabelle12", "ANNABELLE12")):
        with pytest.raises(Problem):
            auth.check_new_account(username, password)


def test_the_throttle_refuses_after_repeated_failures_until_the_window_passes():
    now = [0.0]
    t = auth.Throttle(limit=3, window=60, clock=lambda: now[0])
    for _ in range(3):
        t.check("user:ann", "ip:1")
        t.fail("user:ann", "ip:1")
    with pytest.raises(Problem):
        t.check("user:bob", "ip:1")  # the address is refused, whoever it tries
    t.check("user:bob", "ip:2")
    now[0] = 61
    t.check("user:ann", "ip:1")
