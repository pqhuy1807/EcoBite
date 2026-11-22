import { apiClient } from '@/lib/api-client';
import type { StoreOnboardRequest, StoreOnboardResponse } from '@/types/api';

export interface StoreDetailResponse {
    id: string;
    owner_id?: string;
    name: string;
    description?: string | null;
    address: string;
    latitude?: number | null;
    longitude?: number | null;
    phone?: string | null;
    kyc_status: 'PENDING' | 'APPROVED' | 'REJECTED';
    kyc_license_url?: string | null;
    kyc_reject_reason?: string | null;
    created_at?: string;
}

export interface PendingStoresResponse {
    total: number;
    items: StoreDetailResponse[];
}

export interface ReviewKycResponse {
    store_id: string;
    kyc_status: 'PENDING' | 'APPROVED' | 'REJECTED';
    reject_reason: string | null;
    reviewed_at: string;
}

export interface StoreKycPayload {
    store_name: string;
    address: string;
    phone: string;
    latitude: number;
    longitude: number;
    license_number: string;
    certificate_file: File;
}

export interface StoreProfile {
    id: string;
    store_name: string;
    address: string;
    kyc_status: 'PENDING' | 'APPROVED' | 'REJECTED';
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

    async getMyStore(): Promise<StoreDetailResponse> {
        const { data } = await apiClient.get<StoreDetailResponse>('/stores/me');
        return data;
    },

    async getPendingStores(): Promise<StoreDetailResponse[]> {
        const { data } = await apiClient.get<PendingStoresResponse>('/admin/stores/pending');
        return data.items;
    },

    async reviewStoreKyc(
        storeId: string,
        decision: 'APPROVED' | 'REJECTED',
        rejectReason?: string
    ): Promise<ReviewKycResponse> {
        const { data } = await apiClient.patch<ReviewKycResponse>(
            `/admin/stores/${storeId}/review`,
            {
                decision,
                reject_reason: rejectReason ?? null,
            }
        );
        return data;
    },

    async submitKyc(payload: StoreKycPayload): Promise<StoreProfile> {
        const formData = new FormData();
        formData.append('store_name', payload.store_name);
        formData.append('address', payload.address);
        formData.append('phone', payload.phone);
        formData.append('latitude', String(payload.latitude));
        formData.append('longitude', String(payload.longitude));
        formData.append('license_number', payload.license_number);
        formData.append('certificate_file', payload.certificate_file);

        const { data } = await apiClient.post<StoreProfile>('/stores/kyc', formData);
        return data;
    },

    async getMyStoreStatus(): Promise<StoreProfile> {
        const { data } = await apiClient.get<StoreProfile>('/stores/me');
        return data;
    },
};