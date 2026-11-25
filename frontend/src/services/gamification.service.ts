import { apiClient } from '@/lib/api-client';
import type {
    GreenPointsSummaryResponse,
    UserVoucherResponse,
    VoucherRedeemResponse,
    VoucherResponse,
} from '@/types/api';

export const gamificationService = {
    async getMyGreenPoints(limit = 20): Promise<GreenPointsSummaryResponse> {
        const { data } = await apiClient.get<GreenPointsSummaryResponse>(
            '/green-points/me',
            { params: { limit } }
        );
        return data;
    },

    async listAvailableVouchers(): Promise<VoucherResponse[]> {
        const { data } = await apiClient.get<VoucherResponse[]>('/vouchers');
        return data;
    },

    async listMyVouchers(skip = 0, limit = 20): Promise<UserVoucherResponse[]> {
        const { data } = await apiClient.get<UserVoucherResponse[]>(
            '/vouchers/me',
            { params: { skip, limit } }
        );
        return data;
    },

    async redeemVoucher(voucherId: string): Promise<VoucherRedeemResponse> {
        const { data } = await apiClient.post<VoucherRedeemResponse>(
            `/vouchers/${voucherId}/redeem`
        );
        return data;
    },
};