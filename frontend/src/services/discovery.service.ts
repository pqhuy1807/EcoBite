import { apiClient } from '@/lib/api-client';

export interface NearbyStoreParams {
    latitude: number;
    longitude: number;
    radius_km?: number;
}

export interface NearbyStore {
    id: string;
    name: string;
    address: string;
    latitude: number;
    longitude: number;
    distance_meters: number;
    active_rescue_dishes_count: number;
}

export const discoveryService = {
    async getNearbyStores(params: NearbyStoreParams): Promise<NearbyStore[]> {
        const { data } = await apiClient.get<NearbyStore[]>('/discovery/nearby', {
            params: {
                latitude: params.latitude,
                longitude: params.longitude,
                radius_km: params.radius_km ?? 3,
            },
        });
        return data;
    },
};