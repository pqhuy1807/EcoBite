import { apiClient } from '@/lib/api-client';
import { FoodCategory, NearbyStoresResponse } from '@/types/api';

export interface NearbyStoreParams {
    lat: number;
    lng: number;
    radius_km?: number;
    category?: FoodCategory | 'ALL';
}

export const discoveryService = {
    async getNearbyStores(
        params: NearbyStoreParams
    ): Promise<NearbyStoresResponse> {
        const query: Record<string, string | number> = {
            lat: params.lat,
            lng: params.lng,
            radius_km: params.radius_km ?? 5,
        };
        if (params.category && params.category !== 'ALL') {
            query.category = params.category;
        }
        const { data } = await apiClient.get<NearbyStoresResponse>(
            '/stores/nearby',
            { params: query }
        );
        return data;
    },
};
