import { apiClient } from '@/lib/api-client';

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
    created_at: string;
}

export const storeService = {
    async submitKyc(payload: StoreKycPayload): Promise<StoreProfile> {
        const formData = new FormData();
        formData.append('store_name', payload.store_name);
        formData.append('address', payload.address);
        formData.append('phone', payload.phone);
        formData.append('latitude', String(payload.latitude));
        formData.append('longitude', String(payload.longitude));
        formData.append('license_number', payload.license_number);
        formData.append('certificate_file', payload.certificate_file);

        // Không cần gán cứng Content-Type, axios sẽ tự sinh boundary cho multipart/form-data
        const { data } = await apiClient.post<StoreProfile>('/stores/kyc', formData);
        return data;
    },

    async getMyStoreStatus(): Promise<StoreProfile> {
        const { data } = await apiClient.get<StoreProfile>('/stores/me');
        return data;
    },
};