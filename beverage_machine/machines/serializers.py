
from django.db import transaction
from rest_framework import serializers

from .models import (
    Machine,
    WaterOption,
    ContainerType,
    Inventory,
    WaterPrice,
    Order,
    Payment,
)



class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = [
            "id",
            "machine_code",
            "location",
            "status",
            "water_level_percent",
            "machine_condition",
            "cups_quantity",
            "last_seen_at",
            "telemetry_updated_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "water_level_percent",
            "machine_condition",
            "cups_quantity",
            "last_seen_at",
            "telemetry_updated_at",
            "created_at",
            "updated_at",
        ]


class WaterPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterPrice
        fields = [
            "id",
            "water_option",
            "volume_ml",
            "price_paisa",
            "is_available",
            "updated_at",
        ]


class WaterOptionSerializer(serializers.ModelSerializer):
    prices = WaterPriceSerializer(many=True, read_only=True)

    class Meta:
        model = WaterOption
        fields = [
            "id",
            "name",
            "temperature_type",
            "is_available",
            "prices",
        ]


class ContainerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContainerType
        fields = [
            "id",
            "name",
            "container_fee_paisa",
            "is_available",
        ]


class InventorySerializer(serializers.ModelSerializer):
    machine_code = serializers.CharField(
        source="machine.machine_code",
        read_only=True,
    )
    container_name = serializers.CharField(
        source="container_type.name",
        read_only=True,
    )

    class Meta:
        model = Inventory
        fields = [
            "id",
            "machine",
            "machine_code",
            "container_type",
            "container_name",
            "quantity_available",
            "updated_at",
        ]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "provider",
            "transaction_id",
            "amount_paisa",
            "status",
            "gateway_reference",
            "created_at",
            "verified_at",
        ]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    machine = serializers.PrimaryKeyRelatedField(
        queryset=Machine.objects.all()
    )
    water_option = serializers.PrimaryKeyRelatedField(
        queryset=WaterOption.objects.all()
    )
    container_type = serializers.PrimaryKeyRelatedField(
        queryset=ContainerType.objects.all()
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "machine",
            "water_option",
            "container_type",
            "volume_ml",
            "water_amount_paisa",
            "container_fee_paisa",
            "total_amount_paisa",
            "status",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "water_amount_paisa",
            "container_fee_paisa",
            "total_amount_paisa",
            "status",
            "created_at",
        ]

    def validate(self, attrs):
        machine = attrs["machine"]
        water_option = attrs["water_option"]
        container_type = attrs["container_type"]
        volume_ml = attrs["volume_ml"]

        if not water_option.is_available:
            raise serializers.ValidationError({
                "water_option": "This water option is unavailable."
            })

        if not container_type.is_available:
            raise serializers.ValidationError({
                "container_type": "This container type is unavailable."
            })

        if not WaterPrice.objects.filter(
            water_option=water_option,
            volume_ml=volume_ml,
            is_available=True,
        ).exists():
            raise serializers.ValidationError({
                "volume_ml": "No active price exists for this water option and volume."
            })

        # Disposable cups need stock. Own bottles do not.
        if container_type.name.strip().lower() != "own bottle":
            stock_exists = Inventory.objects.filter(
                machine=machine,
                container_type=container_type,
                quantity_available__gt=0,
            ).exists()

            if not stock_exists:
                raise serializers.ValidationError({
                    "container_type": "This container is out of stock at the selected machine."
                })

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        water_price = WaterPrice.objects.get(
            water_option=validated_data["water_option"],
            volume_ml=validated_data["volume_ml"],
            is_available=True,
        )

        container_fee = validated_data[
            "container_type"
        ].container_fee_paisa

        water_amount = water_price.price_paisa

        return Order.objects.create(
            **validated_data,
            water_amount_paisa=water_amount,
            container_fee_paisa=container_fee,
            total_amount_paisa=water_amount + container_fee,
        )
