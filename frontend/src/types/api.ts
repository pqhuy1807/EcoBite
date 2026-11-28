export type UserRole = 'CONSUMER' | 'STORE_PARTNER' | 'ADMIN';
export type KycStatus = 'PENDING' | 'APPROVED' | 'REJECTED';
export type FoodCategory =
    | 'RICE'
    | 'NOODLES'
    | 'BAKERY'
    | 'VEGETARIAN'
    | 'DRINKS'
    | 'OTHER';
export type DietaryType = 'VEGAN' | 'VEGETARIAN' | 'NON_VEGAN';
export type DishStatus = 'ACTIVE' | 'SOLD_OUT' | 'EXPIRED' | 'HIDDEN';
export type OrderStatus =
    | 'CONFIRMED'
    | 'READY_FOR_PICKUP'
    | 'COMPLETED'
    | 'CANCELLED'
    | 'EXPIRED';
export type PaymentMethod = 'VNPAY' | 'COD';
export type PaymentStatus = 'PENDING' | 'PAID' | 'FAILED';

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

export interface StoreDetailResponse {
    id: string;
    owner_id?: string;
    name: string;
    description?: string | null;
    address: string;
    latitude?: number | null;
    longitude?: number | null;
    phone?: string | null;
    kyc_status: KycStatus;
    kyc_license_url?: string | null;
    kyc_reject_reason?: string | null;
    rating_avg?: number;
    total_co2_saved_kg?: number;
    created_at?: string;
}

export interface PendingStoresResponse {
    total: number;
    items: StoreDetailResponse[];
}

export interface ReviewKycPayload {
    decision: 'APPROVED' | 'REJECTED';
    reject_reason?: string | null;
}

export interface ReviewKycResponse {
    store_id: string;
    kyc_status: KycStatus;
    reject_reason: string | null;
    reviewed_at: string;
}

export interface DishAllergenNote {
    allergen: string;
    risk_level?: string;
    source?: 'EXPLICIT' | 'INFERRED' | string;
    reason?: string | null;
}

export interface MenuItemResponse {
    id: string;
    store_id: string;
    name: string;
    description?: string | null;
    category: FoodCategory | string;
    original_price: string | number;
    image_url: string;
    standard_ingredients: string[];
    base_allergens: string[];
    dietary_type: DietaryType;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface MenuItemCreatePayload {
    name: string;
    description?: string | null;
    category: FoodCategory | string;
    original_price: number;
    image_url: string;
    standard_ingredients?: string[];
    base_allergens?: string[];
    dietary_type?: DietaryType;
    is_active?: boolean;
}

export type MenuItemUpdatePayload = Partial<MenuItemCreatePayload>;

export interface MenuItemListResponse {
    total: number;
    items: MenuItemResponse[];
}

export interface SurplusDishResponse {
    id: string;
    store_id: string;
    menu_item_id?: string | null;
    name: string;
    description?: string | null;
    category: FoodCategory | string;
    original_price: string | number;
    rescue_price: string | number;
    rule_discount_price?: string | number | null;
    override_discounted_price?: string | number | null;
    current_price?: string | number | null;
    is_rule_discount_active: boolean;
    pickup_start_time: string;
    pickup_end_time: string;
    rule_discount_start_time?: string | null;
    image_url?: string | null;
    ingredients: string[];
    allergens: DishAllergenNote[];
    dietary_notes: string[];
    dietary_type: DietaryType;
    estimated_co2_kg_per_dish: string | number;
    total_quantity: number;
    remaining_quantity: number;
    status: DishStatus | string;
    created_at: string;
    updated_at: string;
}

export interface DishPublishPayload {
    menu_item_id: string;
    total_quantity: number;
    remaining_quantity?: number;
    pickup_start_time: string;
    pickup_end_time: string;
    rule_discount_start_time?: string | null;
    override_discounted_price?: number | null;
    allergens?: DishAllergenNote[];
    dietary_notes?: string[];
}

export interface DishBatchPublishPayload {
    pickup_start_time: string;
    pickup_end_time: string;
    rule_discount_start_time?: string | null;
    dishes: Array<{
        menu_item_id: string;
        quantity: number;
        remaining_quantity?: number;
        override_discounted_price?: number | null;
        allergens?: DishAllergenNote[];
        dietary_notes?: string[];
    }>;
}

export interface ActiveStoreDishesResponse {
    store_id: string;
    dishes: SurplusDishResponse[];
}

export interface UpdateDishQuantityResponse {
    dish_id?: string;
    id?: string;
    remaining_quantity: number;
    message: string;
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
    store_name?: string | null;
    store_address?: string | null;
    dish_id: string;
    dish_name?: string | null;
    dish_image_url?: string | null;
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

export interface VNPayCreateUrlResponse {
    payment_url: string;
    txn_ref: string;
}

export interface VNPayReturnResponse {
    is_valid: boolean;
    message: string;
    txn_ref: string | null;
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

export interface GreenPointsLedgerResponse {
    id: string;
    user_id: string;
    order_id?: string | null;
    points_change: number;
    action_type: string;
    co2_saved_kg: string | number;
    note?: string | null;
    balance_after: number;
    created_at: string;
}

export interface VoucherResponse {
    id: string;
    code: string;
    title: string;
    description?: string | null;
    discount_amount: string | number;
    points_required: number;
    min_order_amount: string | number;
    expires_at: string;
    is_active: boolean;
    created_at: string;
}

export interface UserVoucherResponse {
    id: string;
    user_id: string;
    voucher_id: string;
    is_used: boolean;
    used_at?: string | null;
    claimed_at: string;
    voucher?: VoucherResponse | null;
}

export interface GreenPointsSummaryResponse {
    balance_points: number;
    total_co2_saved_kg: string | number;
    total_meals_saved: number;
    rank_title: string;
    recent_ledger: GreenPointsLedgerResponse[];
}

export interface VoucherRedeemResponse {
    user_voucher_id: string;
    voucher_id: string;
    voucher_code: string;
    title: string;
    discount_amount: string | number;
    points_deducted: number;
    remaining_balance: number;
    claimed_at: string;
}

export interface ReviewCreatePayload {
    rating: number;
    comment?: string | null;
    tags?: string[];
    photo_urls?: string[];
}

export interface ReviewResponse {
    id: string;
    order_id: string;
    consumer_id: string;
    store_id: string;
    dish_id: string;
    rating: number;
    comment?: string | null;
    tags: string[];
    photo_urls: string[];
    created_at: string;
}