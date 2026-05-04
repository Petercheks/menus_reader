from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Currency(StrEnum):
    USD = "USD"
    EUR = "EUR"
    ARS = "ARS"
    BOB = "BOB"
    BRL = "BRL"
    CLP = "CLP"
    COP = "COP"
    CRC = "CRC"
    CUP = "CUP"
    DOP = "DOP"
    GTQ = "GTQ"
    HNL = "HNL"
    HTG = "HTG"
    MXN = "MXN"
    NIO = "NIO"
    PAB = "PAB"
    PEN = "PEN"
    PYG = "PYG"
    UYU = "UYU"
    VES = "VES"
    UNKNOWN = "UNKNOWN"


class MenuItemVariant(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Name of the size or variant (e.g. 'Small', 'Large')")
    price: float = Field(description="Numeric price of the variant")
    currency: Currency = Field(description="Detected currency")


class MenuItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Product name as it appears in the menu")
    description: str | None = Field(
        default=None,
        description="Description or ingredients if present, null if not shown",
    )
    price: float | None = Field(
        default=None,
        description="Numeric price. Null if it has multiple variants or is not legible",
    )
    currency: Currency = Field(
        default=Currency.UNKNOWN,
        description="Detected currency for the main price",
    )
    variants: list[MenuItemVariant] = Field(
        default_factory=list,
        description="Variants with their own price (e.g. sizes), empty if not applicable",
    )


class Category(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Category name (e.g. 'Grills', 'Burgers')")
    items: list[MenuItem] = Field(description="Items belonging to the category")


class Promotion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Promotion or combo title")
    description: str | None = Field(
        default=None,
        description="Additional description if present, null otherwise",
    )
    includes: list[str] = Field(
        description="Components included in the promotion (e.g. '2 Jumbos', '1 Liter Soda')"
    )
    price: float = Field(description="Total price of the promotion")
    currency: Currency = Field(description="Detected currency")


class MenuMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    restaurant_name: str | None = Field(
        default=None,
        description="Restaurant name if visible, null otherwise",
    )
    phone: str | None = Field(
        default=None,
        description="Phone or visible contact channel, null otherwise",
    )
    payment_methods: list[str] = Field(
        default_factory=list,
        description="Listed payment methods (e.g. 'Pago Movil', 'Bancamiga')",
    )


class ExtractedMenu(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metadata: MenuMetadata = Field(description="Establishment data extracted from the menu")
    categories: list[Category] = Field(
        default_factory=list,
        description="Menu categories with their individual items",
    )
    promotions: list[Promotion] = Field(
        default_factory=list,
        description="Promotions, combos or special bundles",
    )
    notes: str | None = Field(
        default=None,
        description="Extractor remarks about legibility or other details, null otherwise",
    )
