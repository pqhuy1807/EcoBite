"""VNPay payment endpoints: create URL, IPN, return verification."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import DBSession, require_roles
from app.models.user import User, UserRole
from app.schemas.payment import VNPayCreateUrlResponse, VNPayIPNResponse, VNPayReturnResponse
from app.services.payment_service import PaymentService

router = APIRouter()


def _get_client_ip(request: Request) -> str:
    """Lấy địa chỉ IP của client từ request.

    Ưu tiên header ``X-Forwarded-For`` (lấy giá trị trái đầu, tức client gốc
    khi đi qua proxy), fallback ``request.client.host``; cuối cùng là
    ``"127.0.0.1"`` khi không xác định được.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client is not None and request.client.host:
        return request.client.host
    return "127.0.0.1"


@router.post(
    "/vnpay/create-url",
    response_model=VNPayCreateUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Create VNPay payment URL for consumer orders",
)
async def create_vnpay_payment_url(
    *,
    request: Request,
    current_user: Annotated[User, Depends(require_roles(UserRole.CONSUMER))],
    order_id: str,
    bank_code: str | None = Query(None, description="Optional bank code (e.g., VNPAYQR, NCB)"),
    db: DBSession,
) -> dict[str, Any]:
    """Generate a VNPay payment URL for an eligible order.

    Only consumers can create payment URLs for their own orders.

    Requirements:
    - Order must be owned by the current user
    - Order payment method must be VNPAY
    - Order payment status must be PENDING
    - Order must not be cancelled/expired/completed

    Args:
        request: FastAPI Request (used to extract the client IP for VNPay audit)
        current_user: Current authenticated consumer (via JWT + role guard)
        order_id: Order ID to generate payment URL for
        bank_code: Optional VNPay bank code
        db: Database session

    Returns:
        dict with payment_url and txn_ref

    Raises:
        HTTPException 401: Not authenticated
        HTTPException 403: User is not a consumer
        HTTPException 404: Order not found
        HTTPException 403: Order not owned by consumer
        HTTPException 409: Invalid payment method or status
        HTTPException 410: Order expired or cancelled
    """
    payment_service = PaymentService(db)
    client_ip = _get_client_ip(request)

    return await payment_service.create_vnpay_payment_url(
        order_id=order_id,
        consumer_id=str(current_user.id),
        client_ip=client_ip,
        bank_code=bank_code,
    )


@router.get(
    "/vnpay/ipn",
    response_model=VNPayIPNResponse,
    summary="VNPay Instant Payment Notification (IPN) endpoint",
)
async def vnpay_ipn(
    request: Request,
    db: DBSession,
) -> dict[str, Any]:
    """Process VNPay IPN webhook for payment notifications.

    This endpoint must be publicly accessible at your domain for VNPay
    to send payment status updates. It handles idempotent processing
    using Redis distributed locks.

    Args:
        request: FastAPI Request containing VNPay query parameters
        db: Database session

    Returns:
        dict with RspCode and Message for VNPay
    """
    query_params = dict(request.query_params)
    payment_service = PaymentService(db)
    return await payment_service.process_vnpay_ipn(query_params)


@router.get(
    "/vnpay/return",
    response_model=VNPayReturnResponse,
    summary="VNPay return URL handler for client feedback",
)
async def vnpay_return(
    request: Request,
) -> dict[str, Any]:
    """Verify VNPay return URL signature and return payment result.

    This endpoint handles client-side redirect after payment and
    supports debugging when IPN is not publicly accessible.

    Args:
        request: FastAPI Request containing VNPay return URL query parameters

    Returns:
        dict with is_valid, message, txn_ref, and payment status
    """
    query_params = dict(request.query_params)
    # Signature verification is stateless and needs no DB session.
    is_valid, message, txn_ref = PaymentService.verify_vnpay_return(query_params)

    return {
        "is_valid": is_valid,
        "message": message,
        "txn_ref": txn_ref,
    }
