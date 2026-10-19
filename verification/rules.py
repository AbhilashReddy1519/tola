from decimal import Decimal

# The table is a simplified OIML R 76-1 class III initial-verification set to be confirmed.
# Specified in units of verification scale interval e: (upper_load_in_e, mpe_factor_in_e)
CLASS_III_MPE_TABLE = [
    (Decimal("500"), Decimal("0.5")),
    (Decimal("2000"), Decimal("1.0")),
    (Decimal("10000"), Decimal("1.5")),
]


def mpe_for(load, e, accuracy_class="III"):
    """
    Compute the Maximum Permissible Error (MPE) for a given test load and scale interval e.
    The table is a simplified OIML R 76-1 class III initial-verification set to be confirmed.
    Boundaries:
      0 <= m <= 500 e:       MPE = 0.5 e
      500 < m <= 2000 e:     MPE = 1.0 e
      2000 < m <= 10000 e:   MPE = 1.5 e
    """
    load = Decimal(str(load))
    e = Decimal(str(e))

    if e <= Decimal("0"):
        raise ValueError("Scale interval 'e' must be strictly positive.")

    m = abs(load) / e

    for upper_bound, factor in CLASS_III_MPE_TABLE:
        if m <= upper_bound:
            return factor * e

    # Fallback for loads above 10,000 e
    return Decimal("1.5") * e


def evaluate_reading(load, indication, e, accuracy_class="III"):
    """
    Evaluate a test reading:
      Error = indication - test_load
      Reading passes when abs(error) <= MPE
    """
    load = Decimal(str(load))
    indication = Decimal(str(indication))
    e = Decimal(str(e))

    error = indication - load
    mpe = mpe_for(load, e, accuracy_class)
    within_limit = abs(error) <= mpe

    return {
        "load": load,
        "indication": indication,
        "error": error,
        "mpe": mpe,
        "within_limit": within_limit,
    }


def is_inspection_passing(zero_ok, readings):
    """
    An inspection passes only if zero_ok is True and every test reading is within limit.
    If zero_ok is False, the inspection fails regardless of readings.
    """
    if not zero_ok:
        return False
    if not readings:
        return False

    for r in readings:
        within = r.get("within_limit") if isinstance(r, dict) else getattr(r, "within_limit", False)
        if not within:
            return False

    return True
