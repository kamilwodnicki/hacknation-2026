"""Checksums of Polish identifiers. Each function takes a digits-only string."""

from collections.abc import Callable


def _weighted(digits: str, weights: list[int]) -> int:
    return sum(int(d) * w for d, w in zip(digits, weights))


def nip_valid(value: str) -> bool:
    if len(value) != 10 or not value.isdigit():
        return False
    return _weighted(value, [6, 5, 7, 2, 3, 4, 5, 6, 7]) % 11 == int(value[9])


def regon_valid(value: str) -> bool:
    if not value.isdigit():
        return False
    if len(value) == 9:
        weights = [8, 9, 2, 3, 4, 5, 6, 7]
    elif len(value) == 14:
        weights = [2, 4, 8, 5, 0, 9, 7, 3, 6, 1, 2, 4, 8]
    else:
        return False
    return _weighted(value, weights) % 11 % 10 == int(value[-1])


def pesel_valid(value: str) -> bool:
    if len(value) != 11 or not value.isdigit():
        return False
    control = (10 - _weighted(value, [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]) % 10) % 10
    return control == int(value[10])


def iban_pl_valid(value: str) -> bool:
    """26-digit Polish account number (NRB) without the PL prefix."""
    if len(value) != 26 or not value.isdigit():
        return False
    # Move "PL" + check digits to the end; P=25, L=21
    return int(value[2:] + "2521" + value[:2]) % 97 == 1


def krs_valid(value: str) -> bool:
    """KRS has no checksum; only the format can be checked."""
    return len(value) == 10 and value.isdigit()


CHECKSUMS: dict[str, Callable[[str], bool]] = {
    "nip": nip_valid,
    "regon": regon_valid,
    "pesel": pesel_valid,
    "iban_pl": iban_pl_valid,
    "krs": krs_valid,
}
