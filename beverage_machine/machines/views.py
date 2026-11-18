from uuid import UUID
import base64
import json
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Machine,
    WaterOption,
    ContainerType,
    Inventory,
    Order,
    Payment,
)


from .serializers import (
    MachineSerializer,
    OrderSerializer,
    WaterOptionSerializer,
    ContainerTypeSerializer,
    InventorySerializer,
    PaymentSerializer,
)
from .esewa import (
    amount_in_rupees,
    create_esewa_form,
    verify_callback_signature,
    verify_payment_with_esewa,
)


class MachineListAPIView(generics.ListAPIView):
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    permission_classes = [AllowAny]


class MachineDetailAPIView(generics.RetrieveAPIView):
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    permission_classes = [AllowAny]

class WaterOptionListAPIView(generics.ListAPIView):
    queryset = WaterOption.objects.prefetch_related("prices").all()
    serializer_class = WaterOptionSerializer
    permission_classes = [AllowAny]


class ContainerTypeListAPIView(generics.ListAPIView):
    queryset = ContainerType.objects.all()
    serializer_class = ContainerTypeSerializer
    permission_classes = [AllowAny]


class InventoryListAPIView(generics.ListAPIView):
    queryset = Inventory.objects.select_related(
        "machine",
        "container_type",
    ).all()
    serializer_class = InventorySerializer
    permission_classes = [AllowAny]


class OrderListAPIView(generics.ListAPIView):
    queryset = Order.objects.select_related(
        "machine",
        "water_option",
        "container_type",
    ).all()
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]


class PaymentListAPIView(generics.ListAPIView):
    queryset = Payment.objects.select_related("order").all()
    serializer_class = PaymentSerializer
    permission_classes = [AllowAny]


class OrderCreateAPIView(generics.CreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]


class PaymentInitiateAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        order_id = request.data.get("order_id")

        if not order_id:
            return Response(
                {"error": "order_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            order = get_object_or_404(
                Order.objects.select_for_update(),
                pk=order_id,
            )

            if order.status != "pending_payment":
                return Response(
                    {"error": "This order cannot be paid."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            payment = Payment.objects.filter(
                order=order
            ).first()

            if payment:
                if payment.status != "pending":
                    return Response(
                        {
                            "error": (
                                "Payment is no longer pending. "
                                "Create a new order to retry."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if payment.amount_paisa != order.total_amount_paisa:
                    return Response(
                        {"error": "Order amount mismatch."},
                        status=status.HTTP_409_CONFLICT,
                    )

            else:
                payment = Payment.objects.create(
                    order=order,
                    provider="esewa",
                    amount_paisa=order.total_amount_paisa,
                    status="pending",
                )

            form_data = create_esewa_form(payment)

        return Response(
            {
                "payment_id": str(payment.transaction_id),
                "order_id": order.id,
                "amount_paisa": payment.amount_paisa,
                "amount_npr": (
                    payment.amount_paisa / 100
                ),
                "payment_url": settings.ESEWA_FORM_URL,
                "method": "POST",
                "form_data": form_data,
                "message": (
                    "Submit these form fields to the eSewa "
                    "sandbox checkout."
                ),
            },
            status=status.HTTP_201_CREATED,
        )


class PaymentVerifyAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        transaction_uuid = request.data.get(
            "transaction_uuid"
        )

        if not transaction_uuid:
            return Response(
                {"error": "transaction_uuid is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            parsed_uuid = UUID(str(transaction_uuid))
        except (ValueError, TypeError, AttributeError):
            return Response(
                {"error": "Invalid transaction UUID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = get_object_or_404(
            Payment.objects.select_related("order"),
            transaction_id=parsed_uuid,
        )

        if payment.status == "paid":
            return Response({
                "verified": True,
                "status": "paid",
                "message": "Payment was already verified.",
            })

        if payment.status != "pending":
            return Response({
                "verified": False,
                "status": payment.status,
                "message": "This payment is not pending.",
            })

        result = verify_payment_with_esewa(payment)

        http_status = (
            status.HTTP_200_OK
            if result.get("verified")
            else status.HTTP_202_ACCEPTED
        )

        return Response(result, status=http_status)


class EsewaReturnAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        encoded_data = request.query_params.get("data")

        if not encoded_data:
            return Response(
                {
                    "message": (
                        "No eSewa callback data supplied. "
                        "Check the payment status before retrying."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            padding = "=" * (-len(encoded_data) % 4)
            decoded = base64.b64decode(
                encoded_data + padding,
                validate=True,
            ).decode("utf-8")
            callback_data = json.loads(decoded)

        except (ValueError, UnicodeDecodeError):
            return Response(
                {"error": "Invalid eSewa callback data."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(callback_data, dict):
            return Response(
                {"error": "Invalid callback format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not verify_callback_signature(callback_data):
            return Response(
                {"error": "Invalid callback signature."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            parsed_uuid = UUID(
                str(callback_data.get("transaction_uuid", ""))
            )
        except (ValueError, TypeError, AttributeError):
            return Response(
                {"error": "Invalid transaction UUID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = get_object_or_404(
            Payment.objects.select_related("order"),
            transaction_id=parsed_uuid,
        )

        callback_product = callback_data.get("product_code")
        callback_amount = callback_data.get("total_amount")

        try:
            callback_amount_matches = (
                Decimal(str(callback_amount))
                == Decimal(amount_in_rupees(payment.amount_paisa))
            )
        except Exception:
            callback_amount_matches = False

        if (
            str(callback_product) != settings.ESEWA_PRODUCT_CODE
            or not callback_amount_matches
        ):
            return Response(
                {
                    "error": (
                        "Callback product or amount "
                        "does not match the order."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Callback signature alone is not enough.
        # Confirm the transaction directly with eSewa.
        result = verify_payment_with_esewa(payment)

        return Response({
            "order_id": payment.order_id,
            "payment_id": str(payment.transaction_id),
            "payment": result,
            "dispensing_authorized": False,
            "note": (
                "Hardware dispensing is not enabled yet."
            ),
        })
