import pytest
from pydantic import ValidationError

from app.models.menu import (
    Category,
    Currency,
    ExtractedMenu,
    MenuItem,
    MenuItemVariant,
    MenuMetadata,
    Promotion,
)


def test_currency_values() -> None:
    assert Currency.USD == "USD"
    assert Currency.VES == "VES"
    assert Currency.UNKNOWN == "UNKNOWN"


def test_currency_supports_latam_and_euro() -> None:
    expected = {
        "USD",
        "EUR",
        "ARS",
        "BOB",
        "BRL",
        "CLP",
        "COP",
        "CRC",
        "CUP",
        "DOP",
        "GTQ",
        "HNL",
        "HTG",
        "MXN",
        "NIO",
        "PAB",
        "PEN",
        "PYG",
        "UYU",
        "VES",
        "UNKNOWN",
    }
    assert {c.value for c in Currency} == expected


def test_menu_item_minimal() -> None:
    item = MenuItem(name="Choripan")
    assert item.name == "Choripan"
    assert item.description is None
    assert item.price is None
    assert item.currency is Currency.UNKNOWN
    assert item.variants == []


def test_menu_item_full() -> None:
    item = MenuItem(
        name="Pizza",
        description="Tomate y queso",
        price=12.5,
        currency=Currency.USD,
        variants=[
            MenuItemVariant(name="Pequena", price=1890, currency=Currency.VES),
            MenuItemVariant(name="Grande", price=4050, currency=Currency.VES),
        ],
    )
    assert item.price == 12.5
    assert len(item.variants) == 2


def test_promotion_requires_includes_and_price() -> None:
    promo = Promotion(
        name="2 Jumbos + 1 Refresco",
        includes=["2 Jumbos", "1 Refresco de Litro"],
        price=2700,
        currency=Currency.VES,
    )
    assert promo.price == 2700
    assert promo.description is None


def test_extracted_menu_defaults() -> None:
    menu = ExtractedMenu(metadata=MenuMetadata())
    assert menu.categories == []
    assert menu.promotions == []
    assert menu.notes is None
    assert menu.metadata.payment_methods == []


def test_extracted_menu_full() -> None:
    menu = ExtractedMenu(
        metadata=MenuMetadata(
            restaurant_name="All Grill",
            phone="0424.209.87.56",
            payment_methods=["Pago Movil"],
        ),
        categories=[
            Category(
                name="Parrillas",
                items=[
                    MenuItem(name="Mix", price=4320, currency=Currency.VES),
                ],
            )
        ],
        promotions=[
            Promotion(
                name="2 Empanadas + 1 Malta/Ref de botella",
                includes=["2 Empanadas", "1 Malta/Ref de botella"],
                price=1890,
                currency=Currency.VES,
            )
        ],
    )
    assert menu.metadata.restaurant_name == "All Grill"
    assert menu.categories[0].items[0].name == "Mix"
    assert menu.promotions[0].price == 1890


def test_extracted_menu_extra_field_forbidden() -> None:
    with pytest.raises(ValidationError):
        ExtractedMenu.model_validate(
            {
                "metadata": {},
                "categories": [],
                "promotions": [],
                "unexpected": "field",
            }
        )


def test_extracted_menu_json_schema_has_required_fields() -> None:
    schema = ExtractedMenu.model_json_schema()
    assert "metadata" in schema["properties"]
    assert "categories" in schema["properties"]
    assert "promotions" in schema["properties"]
