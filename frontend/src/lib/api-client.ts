import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 15000,
    headers: {
        'Content-Type': 'application/json',
    },
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    if (typeof window !== 'undefined') {
        const token = localStorage.getItem('access_token');
        if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        // Let the browser set multipart boundary for FormData uploads
        if (config.data instanceof FormData && config.headers) {
            delete config.headers['Content-Type'];
        }
    }
    return config;
});

apiClient.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        const originalRequest = error.config as
            | (InternalAxiosRequestConfig & { _retry?: boolean })
            | undefined;

        if (
            error.response?.status === 401 &&
            originalRequest &&
            !originalRequest._retry &&
            !originalRequest.url?.includes('/auth/login') &&
            !originalRequest.url?.includes('/auth/refresh') &&
            typeof window !== 'undefined'
        ) {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
                originalRequest._retry = true;
                try {
                    const { data } = await axios.post<{
                        access_token: string;
                        refresh_token?: string;
                        user?: unknown;
                    }>(`${API_BASE_URL}/auth/refresh`, {
                        refresh_token: refreshToken,
                    });
                    localStorage.setItem('access_token', data.access_token);
                    if (data.refresh_token) {
                        localStorage.setItem('refresh_token', data.refresh_token);
                    }
                    if (data.user) {
                        localStorage.setItem('user', JSON.stringify(data.user));
                    }
                    if (originalRequest.headers) {
                        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
                    }
                    return apiClient(originalRequest);
                } catch {
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    localStorage.removeItem('user');
                    window.dispatchEvent(new Event('ecobite-auth-change'));
                }
            }
        }
        return Promise.reject(error);
    }
);

export function extractApiErrorMessage(err: unknown, fallback: string): string {
    if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        if (typeof detail === 'string') return detail;
        if (Array.isArray(detail) && detail.length > 0) {
            const first = detail[0];
            if (typeof first?.msg === 'string') return first.msg;
        }
    }
    if (err instanceof Error && err.message) return err.message;
    return fallback;
}
