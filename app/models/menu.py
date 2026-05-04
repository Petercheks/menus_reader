from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Currency(StrEnum):
    USD = "USD"
    VES = "VES"
    UNKNOWN = "UNKNOWN"


class MenuItemVariant(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Nombre del tamano o variante (ej: 'Pequena', 'Grande')")
    price: float = Field(description="Precio numerico de la variante")
    currency: Currency = Field(description="Moneda detectada")


class MenuItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Nombre del producto tal como aparece en el menu")
    description: str | None = Field(
        default=None,
        description="Descripcion o ingredientes si esta presente, null si no aparece",
    )
    price: float | None = Field(
        default=None,
        description="Precio numerico. Null si tiene varias variantes o no es legible",
    )
    currency: Currency = Field(
        default=Currency.UNKNOWN,
        description="Moneda detectada para el precio principal",
    )
    variants: list[MenuItemVariant] = Field(
        default_factory=list,
        description="Variantes con precio propio (ej: tamanos), vacio si no aplica",
    )


class Category(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Nombre de la categoria (ej: 'Parrillas', 'Hamburguesas')")
    items: list[MenuItem] = Field(description="Items pertenecientes a la categoria")


class Promotion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Titulo de la promocion o combo")
    description: str | None = Field(
        default=None,
        description="Descripcion adicional si existe, null si no",
    )
    includes: list[str] = Field(
        description="Componentes que incluye la promocion (ej: '2 Jumbos', '1 Refresco de Litro')"
    )
    price: float = Field(description="Precio total de la promocion")
    currency: Currency = Field(description="Moneda detectada")


class MenuMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    restaurant_name: str | None = Field(
        default=None,
        description="Nombre del restaurante si es visible, null si no",
    )
    phone: str | None = Field(
        default=None,
        description="Telefono o canal de contacto visible, null si no",
    )
    payment_methods: list[str] = Field(
        default_factory=list,
        description="Metodos de pago listados (ej: 'Pago Movil', 'Bancamiga')",
    )


class ExtractedMenu(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metadata: MenuMetadata = Field(description="Datos del establecimiento extraidos del menu")
    categories: list[Category] = Field(
        default_factory=list,
        description="Categorias del menu con sus items individuales",
    )
    promotions: list[Promotion] = Field(
        default_factory=list,
        description="Promociones, combos o paquetes especiales",
    )
    notes: str | None = Field(
        default=None,
        description="Observaciones del extractor sobre legibilidad u otros detalles, null si no",
    )
