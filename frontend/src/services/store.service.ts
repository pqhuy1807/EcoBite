import { apiClient } from '@/lib/api-client';
import type { StoreOnboardRequest, StoreOnboardResponse } from '@/types/api';

export interface StoreDetailResponse {
    id: string;
    name: string;
    description?: string | null;
    address: string;
    latitude?: number | null;
    longitude?: number | null;
    phone?: string | null;
    kyc_status: 'PENDING' | 'APPROVED' | 'REJECTED';
    kyc_license_url?: string | null;
    created_at?: string;
}

export const storeService = {
    async onboardStore(payload: StoreOnboardRequest): Promise<StoreOnboardResponse> {
        const { data } = await apiClient.post<StoreOnboardResponse>('/stores/onboard', payload);
        return data;
    },

    async getStoreById(storeId: string): Promise<StoreDetailResponse> {
        const { data } = await apiClient.get<StoreDetailResponse>(`/stores/${storeId}`);
        return data;
    },
};
