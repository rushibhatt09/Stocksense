"""String constants used by the model layer.

Plain strings rather than database enums: the same code then runs on SQLite and
Postgres, and adding a status never needs a migration on the enum type.
"""


class Role:
    MANAGER = "manager"
    STAFF = "staff"

    ALL = (MANAGER, STAFF)


class LocationType:
    INTERNAL = "internal"
    VENDOR = "vendor"
    CUSTOMER = "customer"
    ADJUSTMENT = "adjustment"
    SCRAP = "scrap"

    ALL = (INTERNAL, VENDOR, CUSTOMER, ADJUSTMENT, SCRAP)
    # Locations that hold real stock. Everything else is a counterpart that
    # explains where stock came from or went.
    PHYSICAL = (INTERNAL,)


class DocType:
    RECEIPT = "receipt"
    DELIVERY = "delivery"
    INTERNAL = "internal"
    ADJUSTMENT = "adjustment"

    ALL = (RECEIPT, DELIVERY, INTERNAL, ADJUSTMENT)
    # Prefix used when numbering a document, e.g. WH1/IN/0001.
    PREFIX = {RECEIPT: "IN", DELIVERY: "OUT", INTERNAL: "INT", ADJUSTMENT: "ADJ"}


class DocStatus:
    DRAFT = "draft"
    WAITING = "waiting"
    READY = "ready"
    DONE = "done"
    CANCELED = "canceled"

    ALL = (DRAFT, WAITING, READY, DONE, CANCELED)
    # A document in one of these still counts as pending on the dashboard.
    OPEN = (DRAFT, WAITING, READY)


class OtpPurpose:
    PASSWORD_RESET = "password_reset"
