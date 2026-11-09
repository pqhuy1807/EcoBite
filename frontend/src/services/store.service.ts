import { apiClient } from '@/lib/api-client';
import {
    NearbyStoresResponse,
    StoreOnboardRequest,
    StoreOnboardResponse,
} from '@/types/api';

// Dữ liệu mẫu chuẩn theo đúng Đặc tả JSON Phần 2.5 để hiển thị khi chạy độc lập Frontend
export const FALLBACK_NEARBY_STORES: NearbyStoresResponse = {
    total: 2,
    radius_km: 3.0,
    user_location: { lat: 10.7769, lng: 106.7009 },
    results: [
        {
            id: 'e4f8d2a1-3c4b-5a6d-7e8f-9a0b1c2d3e4f',
            name: 'Tiệm Bánh Mì & Cơm Trưa Sài Gòn',
            address: '123 Đường Nguyễn Huệ, Phường Bến Nghé, Quận 1, TP.HCM',
            latitude: 10.776889,
            longitude: 106.700806,
            distance_meters: 320.5,
            rating_avg: 4.9,
            total_co2_saved_kg: 145.2,
            dishes: [
                {
                    id: 'd7a1b3c9-4e5f-6a7b-8c9d-0e1f2a3b4c5d',
                    name: 'Cơm sườn bì chả',
                    category: 'RICE',
                    image_url: 'https://cdn.ecobite.vn/menu/com_suon_bi_cha.jpg',
                    original_price: 45000,
                    current_price: 22000,
                    rule_discount_price: 13500,
                    is_rule_discount_active: false,
                    pickup_window: '14:00 - 15:00',
                    remaining_quantity: 5,
                    allergens: ['Eggs (Trứng)', 'Fish (Cá/Nước mắm)'],
                    dietary_notes: ['Có mỡ hành (Allium)', 'Có dưa chua'],
                },
            ],
        },
        {
            id: 'b9c8d7e6-5f4a-3b2c-1d0e-9f8a7b6c5d4e',
            name: 'Bún Thịt Nướng & Đồ Chay Đa Kao',
            address: '45 Đinh Tiên Hoàng, Phường Đa Kao, Quận 1, TP.HCM',
            latitude: 10.7882,
            longitude: 106.6985,
            distance_meters: 1280.0,
            rating_avg: 4.8,
            total_co2_saved_kg: 98.5,
            dishes: [
                {
                    id: 'c2b3d4e5-6f7a-8b9c-0d1e-2f3a4b5c6d7e',
                    name: 'Bún thịt nướng chả giò',
                    category: 'NOODLES',
                    image_url: 'https://cdn.ecobite.vn/menu/bun_thit_nuong.jpg',
                    original_price: 50000,
                    current_price: 15000,
                    rule_discount_price: 15000,
                    is_rule_discount_active: true,
                    pickup_window: '14:30 - 15:00',
                    remaining_quantity: 3,
                    allergens: ['Peanuts (Đậu phộng)', 'Fish (Nước mắm)'],
                    dietary_notes: ['Có hành phi', 'Có đậu phộng'],
                },
            ],
        },
    ],
};

export const storeService = {
    async onboardStore(
        payload: StoreOnboardRequest
    ): Promise<StoreOnboardResponse> {
        const { data } = await apiClient.post<StoreOnboardResponse>(
            '/stores/onboard',
            payload
        );
        return data;
    },

    async getNearbyStores(params: {
        lat: number;
        lng: number;
        radius_km?: number;
        category?: string;
    }): Promise<NearbyStoresResponse> {
        try {
            const { data } = await apiClient.get<NearbyStoresResponse>(
                '/stores/nearby',
                { params }
            );
            return data;
        } catch {
            // Nếu Backend chưa bật khi test độc lập, trả về dữ liệu mẫu chuẩn để Map vẫn hiển thị
            return {
                ...FALLBACK_NEARBY_STORES,
                radius_km: params.radius_km ?? 3.0,
                user_location: { lat: params.lat, lng: params.lng },
            };
        }
    },
};
