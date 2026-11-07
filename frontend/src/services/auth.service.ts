import { apiClient } from '@/lib/api-client';
import {
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    User,
} from '@/types/api';

export const authService = {
    async register(payload: RegisterRequest): Promise<User> {
        const { data } = await apiClient.post<User>('/auth/register', payload);
        return data;
    },

    async login(payload: LoginRequest): Promise<LoginResponse> {
        const { data } = await apiClient.post<LoginResponse>('/auth/login', payload);
        if (typeof window !== 'undefined') {
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            localStorage.setItem('user', JSON.stringify(data.user));
        }
        return data;
    },

    logout(): void {
        if (typeof window !== 'undefined') {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
        }
    },

    getCurrentUser(): User | null {
        if (typeof window === 'undefined') return null;
        const raw = localStorage.getItem('user');
        if (!raw) return null;
        try {
            return JSON.parse(raw) as User;
        } catch {
            return null;
        }
    },
};