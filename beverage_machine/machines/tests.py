from rest_framework import status
from rest_framework.test import APITestCase

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Machine

from machines.models import (
    Machine,
    WaterOption,
    ContainerType,
    Inventory,
    WaterPrice,
    Order,
)



class MachineModelTests(TestCase):

    def test_machine_uses_offline_as_default_status(self):
        machine = Machine.objects.create(
            machine_code="WATER-001",
            location="Pokhara",
        )

        self.assertEqual(machine.status, Machine.Status.OFFLINE)

    
    def test_machine_code_with_spaces_is_rejected(self):
        machine = Machine(
        machine_code=" water-002 ",
        location="Pokhara",
    )

        with self.assertRaises(ValidationError):
            machine.full_clean()
    
    def test_invalid_machine_code_is_rejected(self):
        machine = Machine(
            machine_code="WATER 003",
            location="Pokhara",
        )

        with self.assertRaises(ValidationError):
            machine.full_clean()

    def test_location_containing_only_spaces_is_rejected(self):
        machine = Machine(
            machine_code="WATER-004",
            location="   ",
        )

        with self.assertRaises(ValidationError):
            machine.full_clean()

    def test_invalid_status_is_rejected(self):
        machine = Machine(
            machine_code="WATER-005",
            location="Pokhara",
            status="broken",
        )

        with self.assertRaises(ValidationError):
            machine.full_clean()

    def test_duplicate_machine_code_is_rejected(self):
        Machine.objects.create(
            machine_code="WATER-006",
            location="Pokhara",
        )

        duplicate = Machine(
            machine_code="WATER-006",
            location="Kathmandu",
        )

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

class MachineAPITests(APITestCase):
    def setUp(self):
        self.machine = Machine.objects.create(
            machine_code="WATER-TEST-001",
            location="Pokhara",
            status=Machine.Status.ONLINE,
        )

    def test_machine_list_returns_machines(self):
        response = self.client.get("/api/machines/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["machine_code"],
            "WATER-TEST-001",
        )

    def test_machine_detail_returns_machine(self):
        response = self.client.get(
            f"/api/machines/{self.machine.pk}/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["machine_code"],
            "WATER-TEST-001",
        )

    def test_unknown_machine_returns_404(self):
        response = self.client.get("/api/machines/999999/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class OrderAPITests(APITestCase):
    def setUp(self):
        self.machine = Machine.objects.create(
            machine_code="WATER-ORDER-001",
            location="Pokhara",
            status=Machine.Status.ONLINE,
        )

        self.water = WaterOption.objects.create(
            name="Normal Water",
            temperature_type=WaterOption.TemperatureType.NORMAL,
            is_available=True,
        )

        self.cup = ContainerType.objects.create(
            name="Disposable cup",
            container_fee_paisa=500,
            is_available=True,
        )

        WaterPrice.objects.create(
            water_option=self.water,
            volume_ml=500,
            price_paisa=1500,
            is_available=True,
        )

        Inventory.objects.create(
            machine=self.machine,
            container_type=self.cup,
            quantity_available=10,
        )

    def test_order_uses_server_calculated_prices(self):
        response = self.client.post(
            "/api/orders/",
            {
                "machine": self.machine.pk,
                "water_option": self.water.pk,
                "container_type": self.cup.pk,
                "volume_ml": 500,
                "total_amount_paisa": 1,
                "water_amount_paisa": 1,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(response.data["water_amount_paisa"], 1500)
        self.assertEqual(response.data["container_fee_paisa"], 500)
        self.assertEqual(response.data["total_amount_paisa"], 2000)
        self.assertEqual(
            response.data["status"],
            Order.Status.PENDING_PAYMENT,
        )

    def test_order_rejects_unpriced_volume(self):
        response = self.client.post(
            "/api/orders/",
            {
                "machine": self.machine.pk,
                "water_option": self.water.pk,
                "container_type": self.cup.pk,
                "volume_ml": 2000,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_order_rejects_empty_container_inventory(self):
        Inventory.objects.filter(
            machine=self.machine,
            container_type=self.cup,
        ).update(quantity_available=0)

        response = self.client.post(
            "/api/orders/",
            {
                "machine": self.machine.pk,
                "water_option": self.water.pk,
                "container_type": self.cup.pk,
                "volume_ml": 500,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
