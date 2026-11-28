import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '@/lib/api-client';
import { paymentService } from '@/services/payment.service';

vi.mock('@/lib/api-client', () => ({
    apiClient: {
        post: vi.fn(),
        get: vi.fn(),
    },
}));

describe('paymentService', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('gửi đúng query params order_id và bank_code khi tạo URL VNPay', async () => {
        vi.mocked(apiClient.post).mockResolvedValue({
            data: {
                payment_url: 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html',
                txn_ref: 'ORDER_123',
            },
        });

        const res = await paymentService.createVnpayUrl('order-123', 'NCB');

        expect(apiClient.post).toHaveBeenCalledWith(
            '/payments/vnpay/create-url',
            null,
            {
                params: {
                    order_id: 'order-123',
                    bank_code: 'NCB',
                },
            }
        );
        expect(res.txn_ref).toBe('ORDER_123');
    });

    it('chuyển tiếp đầy đủ query params vnp_* khi xác thực kết quả trả về', async () => {
        const query = {
            vnp_ResponseCode: '00',
            vnp_TxnRef: 'ORDER_123',
            vnp_SecureHash: 'abc123',
        };
        vi.mocked(apiClient.get).mockResolvedValue({
            data: {
                is_valid: true,
                message: 'Thanh toán thành công',
                txn_ref: 'ORDER_123',
            },
        });

        const res = await paymentService.verifyVnpayReturn(query);

        expect(apiClient.get).toHaveBeenCalledWith('/payments/vnpay/return', {
            params: query,
        });
        expect(res.is_valid).toBe(true);
    });
});