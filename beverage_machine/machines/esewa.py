
import base64
import hashlib
import hmac
from decimal import Decimal

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone


def amount_in_rupees(amount_paisa):
    """Convert integer paisa to a two-decimal rupee string."""
    amount = Decimal(amount_paisa) / Decimal("100")
    return f"{amount:.2f}"


def generate_signature(message):
    """Generate an eSewa HMAC-SHA256 signature."""
    digest = hmac.new(
        settings.ESEWA_SECRET_KEY.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    return base64.b64encode(digest).decode("utf-8")


def create_esewa_form(payment):
    """Build the signed ePay V2 payment form."""
    total_amount = amount_in_rupees(payment.amount_paisa)
    transaction_uuid = str(payment.transaction_id)
    product_code = settings.ESEWA_PRODUCT_CODE

    signed_field_names = (
        "total_amount,transaction_uuid,product_code"
    )

    message = (
        f"total_amount={total_amount},"
        f"transaction_uuid={transaction_uuid},"
        f"product_code={product_code}"
    )

    return {
        "amount": total_amount,
        "tax_amount": "0",
        "total_amount": total_amount,
        "transaction_uuid": transaction_uuid,
        "product_code": product_code,
        "product_service_charge": "0",
        "product_delivery_charge": "0",
        "success_url": settings.ESEWA_SUCCESS_URL,
        "failure_url": settings.ESEWA_FAILURE_URL,
        "signed_field_names": signed_field_names,
        "signature": generate_signature(message),
    }


def verify_callback_signature(data):
    """Check the signature returned in eSewa's callback."""
    signature = data.get("signature")
    signed_field_names = data.get("signed_field_names", "")

    if not signature or not signed_field_names:
        return False

    field_names = [
        field.strip()
        for field in signed_field_names.split(",")
        if field.strip()
    ]

    if not field_names:
        return False

    # Reject missing fields and duplicate field names.
    if len(field_names) != len(set(field_names)):
        return False

    if any(field not in data for field in field_names):
        return False

    message = ",".join(
        f"{field}={data[field]}"
        for field in field_names
    )

    expected_signature = generate_signature(message)

    return hmac.compare_digest(
        signature,
        expected_signature,
    )


def verify_payment_with_esewa(payment):
    """
    Query eSewa directly.
    A browser redirect alone never marks an order as paid.
    """
    total_amount = amount_in_rupees(payment.amount_paisa)
    transaction_uuid = str(payment.transaction_id)
    product_code = settings.ESEWA_PRODUCT_CODE

    try:
        response = requests.get(
            settings.ESEWA_STATUS_URL,
            params={
                "product_code": product_code,
                "total_amount": total_amount,
                "transaction_uuid": transaction_uuid,
            },
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()

    except (requests.RequestException, ValueError):
        return {
            "verified": False,
            "message": "Could not confirm payment with eSewa.",
        }

    remote_status = str(result.get("status", "")).upper()

    # ePay V2's response may use these field names.
    remote_uuid = result.get("transaction_uuid")
    remote_product_code = result.get("product_code")

    try:
        remote_amount = Decimal(
            str(result.get("total_amount"))
        )
    except Exception:
        remote_amount = None

    amount_matches = (
        remote_amount is not None
        and remote_amount == Decimal(total_amount)
    )

    transaction_matches = (
        str(remote_uuid) == transaction_uuid
    )

    product_matches = (
        str(remote_product_code) == product_code
    )

    if remote_status == "COMPLETE":
        if not (
            amount_matches
            and transaction_matches
            and product_matches
        ):
            return {
                "verified": False,
                "message": (
                    "Payment details did not match this order."
                ),
            }

        # Lock the records while updating their payment state.
        with transaction.atomic():
            locked_payment = (
                type(payment).objects
                .select_for_update()
                .get(pk=payment.pk)
            )

            if locked_payment.status == "pending":
                locked_payment.status = "paid"
                locked_payment.gateway_reference = str(
                    result.get("ref_id")
                    or result.get("refId")
                    or ""
                )
                locked_payment.gateway_response = result
                locked_payment.verified_at = timezone.now()
                locked_payment.save(
                    update_fields=[
                        "status",
                        "gateway_reference",
                        "gateway_response",
                        "verified_at",
                    ]
                )

            if locked_payment.status == "paid":
                order = locked_payment.order
                if order.status == "pending_payment":
                    order.status = "paid"
                    order.save(update_fields=["status"])

        return {
            "verified": True,
            "status": "paid",
            "message": "Payment verified successfully.",
        }

    if remote_status in {"CANCELED", "NOT_FOUND", "FAILED"}:
        with transaction.atomic():
            locked_payment = (
                type(payment).objects
                .select_for_update()
                .get(pk=payment.pk)
            )

            if locked_payment.status == "pending":
                locked_payment.status = "failed"
                locked_payment.gateway_response = result
                locked_payment.save(
                    update_fields=["status", "gateway_response"]
                )

        return {
            "verified": False,
            "status": "failed",
            "message": "eSewa did not confirm a successful payment.",
        }

    # PENDING, AMBIGUOUS and unknown responses are not successes.
    return {
        "verified": False,
        "status": "pending",
        "message": "Payment is not confirmed yet.",
    }
