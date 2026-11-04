"""Website accounts: invite codes, passwords and sessions.

The beta is invite-only. A GameMaker makes invite codes with `critters invite create`;
each code makes up to max_uses accounts, with the invite's role, until it expires.
Passwords are hashed with scrypt. Signing in sets a cookie holding a random token, and
only the token's SHA-256 is stored, so a leaked sessions table can't be replayed.
"""

import hashlib
import hmac
import re
import secrets
import time
from collections import defaultdict, deque

from .play import Problem

ROLES = ("player", "commissioner", "gamemaker")
USERNAME = re.compile(r"^[A-Za-z0-9_-]{3,24}$")
MIN_PASSWORD = 10
SESSION_DAYS = 30
SCRYPT = {"n": 2 ** 14, "r": 8, "p": 1}
# Invite codes avoid letters and digits that read alike (0/O, 1/I/L).
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


class NotSignedIn(Problem):
    pass


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, **SCRYPT, dklen=32)
    return f"scrypt${SCRYPT['n']}${SCRYPT['r']}${SCRYPT['p']}${salt.hex()}${digest.hex()}"


def check_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt, digest = stored.split("$")
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    found = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r), p=int(p),
                           dklen=len(digest) // 2)
    return hmac.compare_digest(found.hex(), digest)


# Checked against when a username doesn't exist, so a wrong name takes as long as a wrong password.
DUMMY_HASH = hash_password(secrets.token_hex(16))


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_invite_code() -> str:
    """Three groups of four, e.g. K7QM-3XPA-HW2N."""
    return "-".join("".join(secrets.choice(CODE_ALPHABET) for _ in range(4)) for _ in range(3))


def normalize_code(code: str) -> str:
    """As typed (k7qm 3xpa hw2n, K7QM3XPAHW2N) to K7QM-3XPA-HW2N."""
    letters = re.sub(r"[^A-Z0-9]", "", code.upper())
    return "-".join(letters[i:i + 4] for i in range(0, len(letters), 4))


def check_new_account(username: str, password: str) -> None:
    if not USERNAME.match(username):
        raise Problem("a username is 3 to 24 letters, digits, hyphens or underscores")
    check_new_password(username, password)


def check_new_password(username: str, password: str) -> None:
    if len(password) < MIN_PASSWORD:
        raise Problem(f"a password needs at least {MIN_PASSWORD} characters")
    if password.lower() == username.lower():
        raise Problem("the password can't be the username")


class Throttle:
    """Refuse a key (a username, an address) after `limit` failures within `window` seconds.
    Kept in memory: it resets when the server restarts, which is fine for one process."""

    def __init__(self, limit: int = 10, window: float = 15 * 60, clock=time.monotonic):
        self.limit, self.window, self.clock = limit, window, clock
        self.failures: dict[str, deque] = defaultdict(deque)

    def _recent(self, key: str) -> deque:
        times = self.failures[key]
        while times and times[0] <= self.clock() - self.window:
            times.popleft()
        return times

    def check(self, *keys: str) -> None:
        if any(len(self._recent(k)) >= self.limit for k in keys):
            raise Problem("too many failed sign-ins; try again in 15 minutes")

    def fail(self, *keys: str) -> None:
        for k in keys:
            self._recent(k).append(self.clock())

    def clear(self, key: str) -> None:
        self.failures.pop(key, None)
