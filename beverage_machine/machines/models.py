import uuid
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinValueValidator
from django.db import models


machine_code_validator = RegexValidator(
    regex=r"^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$",
    message="Use letters, numbers, and single hyphens, e.g. WATER-001.",
)


class Machine(models.Model):
    class Status(models.TextChoices):
        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"
        MAINTENANCE = "maintenance", "Maintenance"

    machine_code = models.CharField(
        max_length=50,
        unique=True,
        validators=[machine_code_validator],
    )
    location = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OFFLINE,
        db_index=True,
    )
    last_seen_at = models.DateTimeField(null=True, blank=True)
    
    water_level_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
            MinValueValidator(100),
        ],
        help_text="Water tank level from 0 to 100 percent.",
    )

    class Condition(models.TextChoices):
        NORMAL = "normal", "Normal"
        WARNING = "warning", "Warning"
        FAULT = "fault", "Fault"
        UNKNOWN = "unknown", "Unknown"

    machine_condition = models.CharField(
        max_length=20,
        choices=Condition.choices,
        default=Condition.UNKNOWN,
        db_index=True,
    )

    cups_quantity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Current disposable cup stock; null means unknown.",
    )

    telemetry_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the latest machine readings were received.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.machine_code:
            self.machine_code = self.machine_code.strip().upper()
        if self.location:
            self.location = self.location.strip()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.machine_code:
            self.machine_code = self.machine_code.strip().upper()
        if self.location:
            self.location = self.location.strip()
            if not self.location:
                raise ValidationError({
                    "location": "Location cannot contain only spaces."
                })

    class Meta:
        ordering = ["machine_code"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    status__in=["online", "offline", "maintenance"]
                ),
                name="machine_valid_status",
            ),
        ]

    def __str__(self):
        return self.machine_code


class WaterOption(models.Model):
    class TemperatureType(models.TextChoices):
        NORMAL = "normal", "Normal"
        COLD = "cold", "Cold"
        HOT = "hot", "Hot"

    name = models.CharField(max_length=100, unique=True)
    temperature_type = models.CharField(
        max_length=20,
        choices=TemperatureType.choices,
        default=TemperatureType.NORMAL,
    )
    is_available = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.strip()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.name:
            self.name = self.name.strip()
            if not self.name:
                raise ValidationError({
                    "name": "Water option name cannot be empty."
                })

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_temperature_type_display()})"


class ContainerType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    container_fee_paisa = models.PositiveIntegerField(
        default=0,
        help_text="100 paisa = NPR 1.",
    )
    is_available = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.strip()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.name:
            self.name = self.name.strip()
            if not self.name:
                raise ValidationError({
                    "name": "Container name cannot be empty."
                })

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Inventory(models.Model):
    machine = models.ForeignKey(
        Machine,
        on_delete=models.PROTECT,
        related_name="inventory_items",
    )
    container_type = models.ForeignKey(
        ContainerType,
        on_delete=models.PROTECT,
        related_name="inventory_records",
    )
    quantity_available = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["machine", "container_type"]
        constraints = [
            models.UniqueConstraint(
                fields=["machine", "container_type"],
                name="unique_machine_container_inventory",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity_available__gte=0),
                name="inventory_quantity_nonnegative",
            ),
        ]

    def __str__(self):
        return (
            f"{self.machine.machine_code} - {self.container_type.name}: "
            f"{self.quantity_available}"
        )


class WaterPrice(models.Model):
    water_option = models.ForeignKey(
        WaterOption,
        on_delete=models.PROTECT,
        related_name="prices",
    )
    volume_ml = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Water volume in millilitres.",
    )
    price_paisa = models.PositiveIntegerField(
        help_text="Water price in paisa. 100 paisa = NPR 1.",
    )
    is_available = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["water_option", "volume_ml"]
        constraints = [
            models.UniqueConstraint(
                fields=["water_option", "volume_ml"],
                name="unique_water_option_volume",
            ),
            models.CheckConstraint(
                condition=models.Q(volume_ml__gt=0),
                name="water_price_volume_positive",
            ),
        ]

    def __str__(self):
        return (
            f"{self.water_option.name} - {self.volume_ml} ml - "
            f"NPR {self.price_paisa / 100:.2f}"
        )


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Pending payment"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"
        DISPENSING = "dispensing", "Dispensing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    machine = models.ForeignKey(
        Machine,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    water_option = models.ForeignKey(
        WaterOption,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    container_type = models.ForeignKey(
        ContainerType,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    volume_ml = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )
    water_amount_paisa = models.PositiveIntegerField()
    container_fee_paisa = models.PositiveIntegerField()
    total_amount_paisa = models.PositiveIntegerField()
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING_PAYMENT,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(volume_ml__gt=0),
                name="order_volume_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    total_amount_paisa=models.F(
                        "water_amount_paisa"
                    ) + models.F("container_fee_paisa")
                ),
                name="order_total_matches_components",
            ),
        ]

    def __str__(self):
        return f"Order #{self.pk} - {self.total_amount_paisa} paisa"

class Payment(models.Model):
    class Provider(models.TextChoices):
        ESEWA = "esewa", "eSewa"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        EXPIRED = "expired", "Expired"

    order = models.OneToOneField(
        "Order",
        on_delete=models.PROTECT,
        related_name="payment",
    )

    provider = models.CharField(
        max_length=20,
        choices=Provider.choices,
        default=Provider.ESEWA,
    )

    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    amount_paisa = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    gateway_reference = models.CharField(
        max_length=150,
        blank=True,
        default="",
    )

    gateway_response = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.transaction_id} - {self.status}"

    class Meta:
        ordering = ["-created_at"]
