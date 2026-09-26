"""Shared field types."""

from decimal import Decimal
from typing import Annotated

from pydantic import PlainSerializer

# Quantities are Decimal everywhere inside the application, so arithmetic on
# kilogrammes and litres stays exact. On the wire they go out as plain JSON
# numbers, which is what the UI and the dashboard read.
Qty = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]
