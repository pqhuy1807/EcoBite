import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import GreenPointsPage from '@/app/green-points/page';
import { gamificationService } from '@/services/gamification.service';
import type {
    GreenPointsSummaryResponse,
    UserVoucherResponse,
    VoucherRedeemResponse,
    VoucherResponse,
} from '@/types/api';

vi.mock('@/components/auth/AuthGuard', () => ({
    AuthGuard: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('@/services/gamification.service', () => ({
    gamificationService: {
        getMyGreenPoints: vi.fn(),
        listVouchers: vi.fn(),
        getMyVouchers: vi.fn(),
        redeemVoucher: vi.fn(),
    },
}));

function makeVoucher(overrides: Partial<VoucherResponse> = {}): VoucherResponse {
    return {
        id: 'vouch-1',
        code: 'ECO15K',
        title: 'Giảm 15.000đ cho đơn giải cứu',
        description: 'Áp dụng cho mọi đơn từ 30k',
        points_required: 100,
        discount_amount: '15000',
        min_order_amount: '30000',
        expires_at: '2026-12-31T23:59:59Z',
        is_active: true,
        created_at: '2026-11-28T08:00:00Z',
        ...overrides,
    };
}

function makeSummary(
    overrides: Partial<GreenPointsSummaryResponse> = {}
): GreenPointsSummaryResponse {
    return {
        balance_points: 180,
        total_co2_saved_kg: '7.50',
        total_meals_saved: 5,
        rank_title: 'Chiến binh Xanh',
        recent_ledger: [
            {
                id: 'led-1',
                user_id: 'user-1',
                points_change: 100,
                balance_after: 180,
                action_type: 'ORDER_COMPLETED',
                co2_saved_kg: '5.00',
                created_at: '2026-11-28T10:00:00Z',
            },
            {
                id: 'led-2',
                user_id: 'user-1',
                points_change: -50,
                balance_after: 80,
                action_type: 'VOUCHER_REDEEM',
                co2_saved_kg: '0.00',
                created_at: '2026-11-27T15:30:00Z',
            },
        ],
        ...overrides,
    };
}

function makeUserVoucher(
    overrides: Partial<UserVoucherResponse> = {}
): UserVoucherResponse {
    return {
        id: 'uv-1',
        user_id: 'user-1',
        voucher_id: 'vouch-1',
        is_used: false,
        claimed_at: '2026-11-28T09:00:00Z',
        voucher: makeVoucher({
            code: 'MY-ECO-999',
            title: 'Voucher Đã Đổi 20K',
        }),
        ...overrides,
    };
}

function renderPage(customClient?: QueryClient) {
    const client =
        customClient ??
        new QueryClient({
            defaultOptions: {
                queries: { retry: false },
                mutations: { retry: false },
            },
        });

    return {
        queryClient: client,
        ...render(
            <QueryClientProvider client={client}>
                <GreenPointsPage />
            </QueryClientProvider>
        ),
    };
}

describe('GreenPointsPage Flow & Component Tests', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        // Mock clipboard
        Object.assign(navigator, {
            clipboard: {
                writeText: vi.fn().mockResolvedValue(undefined),
            },
        });
    });

    it('render chính xác số dư điểm, danh hiệu rank, lượng CO2 và số bữa ăn đã cứu', async () => {
        vi.mocked(gamificationService.getMyGreenPoints).mockResolvedValue(makeSummary());
        vi.mocked(gamificationService.listVouchers).mockResolvedValue([]);
        vi.mocked(gamificationService.getMyVouchers).mockResolvedValue([]);

        renderPage();

        expect(await screen.findByText('180')).toBeInTheDocument();
        expect(screen.getByText('Chiến binh Xanh')).toBeInTheDocument();
        expect(screen.getByText(/7.5/)).toBeInTheDocument();
        expect(screen.getByText('5')).toBeInTheDocument();
    });

    it('hiển thị thông báo lỗi khi tải dữ liệu Điểm Xanh thất bại', async () => {
        vi.mocked(gamificationService.getMyGreenPoints).mockRejectedValue(
            new Error('Lỗi kết nối cơ sở dữ liệu')
        );
        vi.mocked(gamificationService.listVouchers).mockResolvedValue([]);
        vi.mocked(gamificationService.getMyVouchers).mockResolvedValue([]);

        renderPage();

        expect(
            await screen.findByText(/Lỗi kết nối cơ sở dữ liệu|Không thể tải dữ liệu Điểm Xanh/i)
        ).toBeInTheDocument();
    });

    it('hiển thị trạng thái empty khi kho voucher khả dụng không có mục nào', async () => {
        vi.mocked(gamificationService.getMyGreenPoints).mockResolvedValue(makeSummary());
        vi.mocked(gamificationService.listVouchers).mockResolvedValue([]);
        vi.mocked(gamificationService.getMyVouchers).mockResolvedValue([]);

        renderPage();

        expect(
            await screen.findByText('Hiện chưa có voucher nào đang mở đổi')
        ).toBeInTheDocument();
    });

    it('hiển thị voucher và vô hiệu hóa nút đổi khi người dùng không đủ điểm', async () => {
        // User có 50 điểm
        vi.mocked(gamificationService.getMyGreenPoints).mockResolvedValue(
            makeSummary({ balance_points: 50 })
        );
        // Voucher cần 100 điểm
        vi.mocked(gamificationService.listVouchers).mockResolvedValue([
            makeVoucher({ id: 'v-expensive', title: 'Voucher Giảm 50K', points_required: 100 }),
        ]);
        vi.mocked(gamificationService.getMyVouchers).mockResolvedValue([]);

        renderPage();

        expect(await screen.findByText('Voucher Giảm 50K')).toBeInTheDocument();
        const button = screen.getByRole('button', { name: 'Chưa đủ điểm' });
        expect(button).toBeInTheDocument();
        expect(button).toBeDisabled();
    });

    it('cho phép đổi voucher khi đủ điểm, invalidate cache và hiển thị toast thành công', async () => {
        const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

        // User có 200 điểm
        vi.mocked(gamificationService.getMyGreenPoints).mockResolvedValue(
            makeSummary({ balance_points: 200 })
        );
        // Voucher cần 100 điểm
        const voucher = makeVoucher({
            id: 'v-cheap',
            title: 'Voucher Giảm 15K',
            points_required: 100,
        });
        vi.mocked(gamificationService.listVouchers).mockResolvedValue([voucher]);
        vi.mocked(gamificationService.getMyVouchers).mockResolvedValue([]);

        const redeemResult: VoucherRedeemResponse = {
            user_voucher_id: 'uv-new',
            voucher_id: 'v-cheap',
            voucher_code: 'ECO15K-SUCCESS',
            title: 'Voucher Giảm 15K',
            discount_amount: '15000',
            points_deducted: 100,
            remaining_balance: 100,
            claimed_at: '2026-11-28T12:00:00Z',
        };
        vi.mocked(gamificationService.redeemVoucher).mockResolvedValue(redeemResult);

        const customClient = new QueryClient({
            defaultOptions: {
                queries: { retry: false },
                mutations: { retry: false },
            },
        });
        const invalidateSpy = vi.spyOn(customClient, 'invalidateQueries');

        renderPage(customClient);

        // Nút "Đổi ngay" khả dụng
        const redeemBtn = await screen.findByRole('button', { name: 'Đổi ngay' });
        expect(redeemBtn).toBeEnabled();

        fireEvent.click(redeemBtn);

        expect(confirmSpy).toHaveBeenCalled();
        await waitFor(() => {
            expect(gamificationService.redeemVoucher).toHaveBeenCalledWith('v-cheap');
        });

        // Kiểm tra invalidate các queries quan trọng
        expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['green-points-summary'] });
        expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['my-vouchers'] });
        expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['vouchers-catalog'] });

        // Hiển thị thông báo thành công
        expect(
            await screen.findByText(/Đổi thành công voucher ECO15K-SUCCESS/i)
        ).toBeInTheDocument();

        confirmSpy.mockRestore();
    });

    it('hiển thị danh sách voucher của tôi và hỗ trợ sao chép mã voucher', async () => {
        vi.mocked(gamificationService.getMyGreenPoints).mockResolvedValue(makeSummary());
        vi.mocked(gamificationService.listVouchers).mockResolvedValue([]);
        vi.mocked(gamificationService.getMyVouchers).mockResolvedValue([
            makeUserVoucher({
                id: 'uv-my-1',
                voucher: makeVoucher({
                    code: 'MY-ECO-999',
                    title: 'Voucher Đã Đổi 20K',
                }),
            }),
        ]);

        renderPage();

        // Chuyển sang Tab "Voucher của tôi"
        const myVouchersTabBtn = await screen.findByRole('button', {
            name: /Voucher của tôi/i,
        });
        fireEvent.click(myVouchersTabBtn);

        expect(await screen.findByText('MY-ECO-999')).toBeInTheDocument();
        expect(screen.getByText('Voucher Đã Đổi 20K')).toBeInTheDocument();
        expect(screen.getByText('Sẵn sàng dùng')).toBeInTheDocument();

        // Nhấn nút Sao chép
        const copyBtn = screen.getByRole('button', { name: /Sao chép/i });
        fireEvent.click(copyBtn);

        await waitFor(() => {
            expect(navigator.clipboard.writeText).toHaveBeenCalledWith('MY-ECO-999');
        });
        expect(await screen.findByText(/Đã sao chép mã voucher MY-ECO-999/i)).toBeInTheDocument();
    });

    it('hiển thị lịch sử giao dịch Điểm Xanh gần nhất trong tab Lịch sử điểm', async () => {
        vi.mocked(gamificationService.getMyGreenPoints).mockResolvedValue(
            makeSummary({
                recent_ledger: [
                    {
                        id: 'led-spec-1',
                        user_id: 'user-1',
                        points_change: 150,
                        balance_after: 250,
                        action_type: 'ORDER_COMPLETED',
                        co2_saved_kg: '6.00',
                        created_at: '2026-11-28T12:00:00Z',
                    },
                ],
            })
        );
        vi.mocked(gamificationService.listVouchers).mockResolvedValue([]);
        vi.mocked(gamificationService.getMyVouchers).mockResolvedValue([]);

        renderPage();

        // Chuyển sang Tab "Lịch sử điểm"
        const ledgerTabBtn = await screen.findByRole('button', {
            name: /Lịch sử điểm/i,
        });
        fireEvent.click(ledgerTabBtn);

        expect(await screen.findByText('Giải cứu đơn hàng')).toBeInTheDocument();
        expect(screen.getByText('+150 điểm')).toBeInTheDocument();
        expect(screen.getByText(/Số dư: 250/i)).toBeInTheDocument();
    });
});
