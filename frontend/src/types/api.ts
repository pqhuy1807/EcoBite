export type UserRole = 'CONSUMER' | 'STORE_PARTNER' | 'ADMIN';
export type KycStatus = 'PENDING' | 'APPROVED' | 'REJECTED';
export type FoodCategory = 'RICE' | 'NOODLES' | 'BAKERY' | 'VEGETARIAN';

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

export interface NearbyDishItem {
    id: string;
    name: string;
    category: FoodCategory | string;
    image_url: string;
    original_price: number;
    current_price: number;
    rule_discount_price: number;
    is_rule_discount_active: boolean;
    pickup_window: string;
    remaining_quantity: number;
    allergens: string[];
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