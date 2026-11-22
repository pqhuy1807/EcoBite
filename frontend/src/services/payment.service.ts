import { apiClient } from '@/lib/api-client';

export interface VNPayCreateUrlResponse {
    payment_url: string;
    txn_ref: string;
}

export interface VNPayReturnResponse {
    is_valid: boolean;
    message: string;
    txn_ref: string | null;
}

export const paymentService = {
    async createVnpayUrl(
        orderId: string,
        bankCode?: string
    ): Promise<VNPayCreateUrlResponse> {
        const { data } = await apiClient.post<VNPayCreateUrlResponse>(
            '/payments/vnpay/create-url',
            null,
            {
                params: {
                    order_id: orderId,
                    ...(bankCode ? { bank_code: bankCode } : {}),
                },
            }
        );
        return data;
    },

    async verifyVnpayReturn(
        queryParams: Record<string, string>
    ): Promise<VNPayReturnResponse> {
        const { data } = await apiClient.get<VNPayReturnResponse>(
            '/payments/vnpay/return',
            { params: queryParams }
        );
        return data;
    },
};