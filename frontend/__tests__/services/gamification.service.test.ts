import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '@/lib/api-client';
import { gamificationService } from '@/services/gamification.service';

vi.mock('@/lib/api-client', () => ({
    apiClient: {
        get: vi.fn(),
        post: vi.fn(),
    },
}));

describe('gamificationService', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('gọi đúng endpoint lấy tóm tắt Điểm Xanh với tham số limit', async () => {
        vi.mocked(apiClient.get).mockResolvedValue({
            data: {
                balance_points: 150,
                total_co2_saved_kg: '7.5',
                total_meals_saved: 3,
                rank_title: 'Chiến binh Xanh',
                recent_ledger: [],
            },
        });

        const res = await gamificationService.getMyGreenPoints(30);

        expect(apiClient.get).toHaveBeenCalledWith('/green-points/me', {
            params: { limit: 30 },
        });
        expect(res.balance_points).toBe(150);
    });

    it('gọi đúng endpoint danh sách voucher khả dụng và voucher của tôi', async () => {
        vi.mocked(apiClient.get).mockResolvedValueOnce({ data: [] });
        vi.mocked(apiClient.get).mockResolvedValueOnce({ data: [] });

        await gamificationService.listAvailableVouchers();
        await gamificationService.listMyVouchers(0, 50);

        expect(apiClient.get).toHaveBeenNthCalledWith(1, '/vouchers');
        expect(apiClient.get).toHaveBeenNthCalledWith(2, '/vouchers/me', {
            params: { skip: 0, limit: 50 },
        });
    });

    it('gọi POST đổi voucher theo đúng voucherId', async () => {
        vi.mocked(apiClient.post).mockResolvedValue({
            data: {
                user_voucher_id: 'uv-1',
                voucher_id: 'v-1',
                voucher_code: 'ECO20K',
                title: 'Giảm 20K',
                discount_amount: '20000',
                points_deducted: 100,
                remaining_balance: 50,
                claimed_at: '2026-11-26T10:00:00Z',
            },
        });

        const res = await gamificationService.redeemVoucher('v-1');

        expect(apiClient.post).toHaveBeenCalledWith('/vouchers/v-1/redeem');
        expect(res.voucher_code).toBe('ECO20K');
    });
});