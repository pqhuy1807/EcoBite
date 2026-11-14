export type UserRole = 'CONSUMER' | 'STORE_PARTNER' | 'ADMIN';
export type KycStatus = 'PENDING' | 'APPROVED' | 'REJECTED';
export type FoodCategory =
    | 'RICE'
    | 'NOODLES'
    | 'BAKERY'
    | 'VEGETARIAN'
    | 'DRINKS'
    | 'OTHER';
export type OrderStatus =
    | 'CONFIRMED'
    | 'READY_FOR_PICKUP'
    | 'COMPLETED'
    | 'CANCELLED'
    | 'EXPIRED';
export type PaymentMethod = 'VNPAY' | 'COD';
export type PaymentStatus = 'PENDING' | 'PAID' | 'FAILED' | 'REFUNDED';

export interface User {
    id: string;
    email: string;
    full_name: string;
    role: UserRole;
    green_points_balance?: number;
    created_at?: string;
}

export interface RegisterRequest {
    email: string;
    password: string;
    full_name: string;
    phone: string;
    role: UserRole;
}

export interface LoginRequest {
    email: string;
    password: string;
}

export interface LoginResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
    user: User;
}

export interface StoreOnboardRequest {
    name: string;
    description: string;
    address: string;
    latitude: number;
    longitude: number;
    phone: string;
    kyc_license_url: string;
}

export interface StoreOnboardResponse {
    id: string;
    name: string;
    kyc_status: KycStatus;
    message: string;
}

export interface DishAllergenNote {
    allergen: string;
    risk_level?: string;
    source?: string;
    reason?: string;
}

export interface NearbyDishItem {
    id: string;
    name: string;
    category: FoodCategory | string;
    image_url: string | null;
    original_price: number;
    current_price: number;
    rule_discount_price: number;
    is_rule_discount_active: boolean;
    pickup_window: string;
    remaining_quantity: number;
    allergens: Array<string | DishAllergenNote>;
    dietary_notes: string[];
}

export interface NearbyStore {
    id: string;
    name: string;
    address: string;
    latitude: number;
    longitude: number;
    distance_meters: number;
    rating_avg: number;
    total_co2_saved_kg: number;
    dishes: NearbyDishItem[];
}

export interface NearbyStoresResponse {
    total: number;
    radius_km: number;
    user_location: {
        lat: number;
        lng: number;
    };
    results: NearbyStore[];
}

export interface CreateOrderPayload {
    dish_id: string;
    quantity: number;
    payment_method?: PaymentMethod;
}

export interface OrderResponse {
    id: string;
    order_code: string;
    consumer_id: string;
    store_id: string;
    dish_id: string;
    quantity: number;
    unit_price: string | number;
    total_amount: string | number;
    payment_method: PaymentMethod;
    payment_status: PaymentStatus;
    status: OrderStatus;
    co2_saved_kg: string | number;
    green_points_earned: number;
    pickup_deadline: string;
    completed_at?: string | null;
    created_at: string;
}

export interface QRTokenResponse {
    id: string;
    order_id: string;
    token_hash: string;
    nonce: string;
    expires_at: string;
    is_used: boolean;
    used_at?: string | null;
    created_at: string;
}

export interface OrderDetailResponse extends OrderResponse {
    qr_token: QRTokenResponse | null;
}

export interface QRPayloadResponse {
    order_id: string;
    order_code: string;
    qr_payload: string;
    nonce: string;
    expires_at: string;
    is_used: boolean;
}

export interface QRVerificationResponse {
    success: boolean;
    order_id: string;
    order_code: string;
    status: OrderStatus;
    points_awarded: number;
    co2_saved_kg: string | number;
    message: string;
    order?: OrderResponse | null;
}
