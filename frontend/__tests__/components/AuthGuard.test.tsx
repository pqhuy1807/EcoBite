import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { AuthGuard } from '@/components/auth/AuthGuard';

const replaceMock = vi.fn();

vi.mock('next/navigation', () => ({
    useRouter: () => ({
        replace: replaceMock,
        push: vi.fn(),
    }),
}));

describe('AuthGuard', () => {
    beforeEach(() => {
        localStorage.clear();
        replaceMock.mockReset();
    });

    it('chuyển hướng về /login khi chưa có access_token', async () => {
        render(
            <AuthGuard allowedRoles={['ADMIN']}>
                <div>Noi dung bao mat</div>
            </AuthGuard>
        );

        await waitFor(() => {
            expect(replaceMock).toHaveBeenCalledWith('/login');
        });
        expect(screen.queryByText('Noi dung bao mat')).not.toBeInTheDocument();
    });

    it('chuyển hướng về / khi người dùng không đủ quyền truy cập', async () => {
        localStorage.setItem('access_token', 'fake-jwt-token');
        localStorage.setItem(
            'user',
            JSON.stringify({
                id: 'u1',
                email: 'consumer@ecobite.vn',
                full_name: 'Nguoi Mua',
                role: 'CONSUMER',
            })
        );

        render(
            <AuthGuard allowedRoles={['ADMIN']}>
                <div>Trang Admin KYC</div>
            </AuthGuard>
        );

        await waitFor(() => {
            expect(replaceMock).toHaveBeenCalledWith('/');
        });
        expect(screen.queryByText('Trang Admin KYC')).not.toBeInTheDocument();
    });

    it('hiển thị nội dung khi người dùng có đúng vai trò cho phép', async () => {
        localStorage.setItem('access_token', 'fake-jwt-token');
        localStorage.setItem(
            'user',
            JSON.stringify({
                id: 'u2',
                email: 'admin@ecobite.vn',
                full_name: 'Quan Tri Vien',
                role: 'ADMIN',
            })
        );

        render(
            <AuthGuard allowedRoles={['ADMIN']}>
                <div>Trang Admin KYC</div>
            </AuthGuard>
        );

        expect(await screen.findByText('Trang Admin KYC')).toBeInTheDocument();
        expect(replaceMock).not.toHaveBeenCalled();
    });
});