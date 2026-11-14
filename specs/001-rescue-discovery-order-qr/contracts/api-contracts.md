# API & UI Contracts: Consumer Surplus Discovery, Anti-Overselling Order & Dynamic QR Pickup

**Base URL**: `/api/v1`

## 1. Authentication
- `POST /auth/login`
  - Request: `{ "email": string, "password": string }` (JSON or OAuth2 form)
  - Response `200`: `{ access_token, refresh_token, token_type, expires_in, user }`
- `POST /auth/register`
  - Request: `{ email, password, full_name, phone, role }`
  - Response `201`: `User`

## 2. Spatial Discovery
- `GET /stores/nearby?lat={float}&lng={float}&radius_km={1..10}&category={optional}`
  - Public endpoint using PostGIS `ST_DWithin` / `ST_Distance` (Haversine fallback on SQLite).
  - Response `200` (`NearbyStoresResponse`):
    ```json
    {
      "total": 1,
      "radius_km": 3.0,
      "user_location": { "lat": 10.7769, "lng": 106.7009 },
      "results": [
        {
          "id": "uuid",
          "name": "string",
          "address": "string",
          "latitude": 10.7792,
          "longitude": 106.7005,
          "distance_meters": 259.4,
          "rating_avg": 4.85,
          "total_co2_saved_kg": 355.0,
          "dishes": [
            {
              "id": "uuid",
              "name": "string",
              "category": "RICE",
              "image_url": "string",
              "original_price": 55000,
              "current_price": 30000,
              "rule_discount_price": 16500,
              "is_rule_discount_active": false,
              "pickup_window": "06:00 - 23:59",
              "remaining_quantity": 6,
              "allergens": [],
              "dietary_notes": []
            }
          ]
        }
      ]
    }
    ```

## 3. Order Placement, History, Cancellation & QR Issuance
- `POST /orders` (`CONSUMER` only)
  - Request: `{ "dish_id": "uuid", "quantity": int (> 0), "payment_method": "COD" | "VNPAY" }`
  - Response `201`: `OrderResponse` (`id`, `order_code`, `status`, `unit_price`, `total_amount`, `co2_saved_kg`, `green_points_earned`, `pickup_deadline`, ...)
  - Errors: `400` outside pickup window, `404` dish not found, `409` inactive / insufficient stock.
- `GET /orders/me?status={optional}&skip=0&limit=20` (`CONSUMER` only)
  - Response `200`: `OrderResponse[]`
- `GET /orders/{order_id}` (`CONSUMER` owner / `STORE_PARTNER` owner / `ADMIN`)
  - Response `200`: `OrderDetailResponse` (includes `qr_token` if valid & unused)
- `POST /orders/{order_id}/qr` (**NEW** — `CONSUMER` owner only)
  - Idempotently generates or retrieves the active signed pickup QR payload for an eligible order (`CONFIRMED` / `READY_FOR_PICKUP`, unexpired).
  - Response `200` (`QRPayloadResponse`):
    ```json
    {
      "order_id": "uuid",
      "order_code": "EB-20261114-XXXXXXXX",
      "qr_payload": "ecobite://pickup?order_id=...&user_id=...&nonce=...&expires_at=...&sig=...",
      "nonce": "string",
      "expires_at": "2026-11-14T16:59:00Z",
      "is_used": false
    }
    ```
  - Errors: `403` not owner, `404` not found, `409` order cancelled/completed/expired or QR already used.
- `PATCH /orders/{order_id}/cancel` (`CONSUMER` owner or `STORE_PARTNER` owner)
  - Response `200`: `OrderResponse` (`status: "CANCELLED"`)
  - Errors: `409` already cancelled/completed or past `pickup_deadline`.

## 4. Store Partner QR Verification
- `POST /orders/verify-qr` (`STORE_PARTNER` owner only)
  - Request: `{ "qr_token": "ecobite://pickup?..." }`
  - Response `200`: `QRVerificationResponse` (`success`, `order_id`, `order_code`, `status: "COMPLETED"`, `points_awarded`, `co2_saved_kg`, `message`, `order`)
  - Errors: `400` malformed / invalid HMAC signature / expired / already used (`is_used == True`), `403` wrong store, `409` invalid order status.
