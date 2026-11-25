import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Navbar } from '@/components/ui/Navbar';

vi.mock('next/navigation', () => ({
    usePathname: () => '/',
    useRouter: () => ({
        push: vi.fn(),
        replace: vi.fn(),
    }),
}));

vi.mock('@/services/auth.service', () => ({
    authService: {
        logout: vi.fn(),
    },
}));

describe('Navbar phân quyền theo vai trò', () => {
    beforeEach(() => {
        localStorage.clear();
    });

    it('hiển thị nút Đăng nhập và Đăng ký khi là khách vãng lai', () => {
        render(<Navbar />);

        expect(screen.getByText('Đăng nhập')).toBeInTheDocument();
        expect(screen.getByText('Đăng ký')).toBeInTheDocument();
        expect(screen.queryByText('Duyệt KYC')).not.toBeInTheDocument();
    });

    it('hiển thị Đơn của tôi và Điểm Xanh cho vai trò CONSUMER', () => {
        localStorage.setItem(
            'user',
            JSON.stringify({
                id: 'c1',
                email: 'c@ecobite.vn',
                full_name: 'Khach Hang',
                role: 'CONSUMER',
            })
        );

        render(<Navbar />);

        expect(screen.getAllByText('Đơn của tôi').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Điểm Xanh').length).toBeGreaterThan(0);
        expect(screen.queryByText('Thực đơn gốc')).not.toBeInTheDocument();
    });

    it('hiển thị bộ menu đối tác cho vai trò STORE_PARTNER', () => {
        localStorage.setItem(
            'user',
            JSON.stringify({
                id: 's1',
                email: 's@ecobite.vn',
                full_name: 'Chu Quan',
                role: 'STORE_PARTNER',
            })
        );

        render(<Navbar />);

        expect(screen.getAllByText('Thực đơn gốc').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Món dư cuối ca').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Quét QR Quán').length).toBeGreaterThan(0);
    });

    it('hiển thị Duyệt KYC cho vai trò ADMIN', () => {
        localStorage.setItem(
            'user',
            JSON.stringify({
                id: 'a1',
                email: 'a@ecobite.vn',
                full_name: 'Admin EcoBite',
                role: 'ADMIN',
            })
        );

        render(<Navbar />);

        expect(screen.getAllByText('Duyệt KYC').length).toBeGreaterThan(0);
    });
});