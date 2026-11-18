
from django.contrib import admin

from .models import (
    Machine,
    WaterOption,
    ContainerType,
    Inventory,
    WaterPrice,
    Order,
    Payment,
)



@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = (
        "machine_code",
        "location",
        "status",
        "water_level_percent",
        "machine_condition",
        "cups_quantity",
        "last_seen_at",
        "telemetry_updated_at",
    )

    list_filter = (
        "status",
        "machine_condition",
    )

    search_fields = (
        "machine_code",
        "location",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(WaterOption)
class WaterOptionAdmin(admin.ModelAdmin):
    list_display = ("name", "temperature_type", "is_available")
    list_filter = ("temperature_type", "is_available")
    search_fields = ("name",)


@admin.register(ContainerType)
class ContainerTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "container_fee_paisa", "is_available")
    list_filter = ("is_available",)
    search_fields = ("name",)


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        "machine",
        "container_type",
        "quantity_available",
        "updated_at",
    )
    list_filter = ("container_type",)
    search_fields = ("machine__machine_code", "container_type__name")


@admin.register(WaterPrice)
class WaterPriceAdmin(admin.ModelAdmin):
    list_display = (
        "water_option",
        "volume_ml",
        "price_paisa",
        "is_available",
        "updated_at",
    )
    list_filter = ("water_option", "is_available")
    search_fields = ("water_option__name",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "machine",
        "water_option",
        "volume_ml",
        "total_amount_paisa",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("machine__machine_code",)
    readonly_fields = (
        "machine",
        "water_option",
        "container_type",
        "volume_ml",
        "water_amount_paisa",
        "container_fee_paisa",
        "total_amount_paisa",
        "created_at",
    )
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_id",
        "order",
        "provider",
        "amount_paisa",
        "status",
        "created_at",
        "verified_at",
    )

    list_filter = (
        "provider",
        "status",
        "created_at",
    )

    search_fields = (
        "transaction_id",
        "gateway_reference",
    )

    readonly_fields = (
        "transaction_id",
        "created_at",
        "verified_at",
        "gateway_response",
    )