import { apiClient } from '@/lib/api-client';

export type DishCategory = 'ALL' | 'RICE' | 'NOODLES' | 'BAKERY' | 'VEGETARIAN';

export interface RadarQueryParams {
    lat: number;
    lng: number;
    radius_km?: number;
    category?: DishCategory;
}

export interface SurplusDish {
    id: string;
    name: string;
    description?: string;
    original_price: number;
    discounted_price: number;
    quantity_available: number;
    category: Exclude<DishCategory, 'ALL'>;
    expiry_time: string;
    image_url?: string;
    store: {
        id: string;
        name: string;
        address: string;
        latitude: number;
        longitude: number;
        distance_km?: number;
    };
}

export const radarService = {
    async getNearbyDishes(params: RadarQueryParams): Promise<SurplusDish[]> {
        const query = {
            lat: params.lat,
            lng: params.lng,
            radius_km: params.radius_km ?? 5,
            ...(params.category && params.category !== 'ALL' ? { category: params.category } : {}),
        };

        const { data } = await apiClient.get<SurplusDish[]>('/dishes/nearby', {
            params: query,
        });
        return data;
    },

    async getDishById(dishId: string): Promise<SurplusDish> {
        const { data } = await apiClient.get<SurplusDish>(`/dishes/${dishId}`);
        return data;
    },
};