import { apiClient } from '@/lib/api-client';

export interface MenuItemResponse {
    id: string;
    store_id: string;
    name: string;
    description?: string | null;
    category: string;
    original_price: number;
    image_url?: string | null;
    allergens?: string[];
    dietary_notes?: string[];
    is_active: boolean;
    created_at?: string;
}

export interface MenuItemCreatePayload {
    name: string;
    description?: string | null;
    category: string;
    original_price: number;
    image_url?: string | null;
    allergens?: string[];
    dietary_notes?: string[];
}

export type MenuItemUpdatePayload = Partial<MenuItemCreatePayload> & {
    is_active?: boolean;
};

interface MenuItemListResponse {
    total: number;
    items: MenuItemResponse[];
}

export const menuService = {
    async getStoreMenuItems(storeId: string): Promise<MenuItemResponse[]> {
        const { data } = await apiClient.get<MenuItemListResponse>(
            `/stores/${storeId}/menu-items`
        );
        return data.items;
    },

    async createMenuItem(
        storeId: string,
        payload: MenuItemCreatePayload
    ): Promise<MenuItemResponse> {
        const { data } = await apiClient.post<MenuItemResponse>(
            `/stores/${storeId}/menu-items`,
            payload
        );
        return data;
    },

    async updateMenuItem(
        itemId: string,
        payload: MenuItemUpdatePayload
    ): Promise<MenuItemResponse> {
        const { data } = await apiClient.put<MenuItemResponse>(
            `/menu-items/${itemId}`,
            payload
        );
        return data;
    },

    async deleteMenuItem(itemId: string): Promise<MenuItemResponse> {
        const { data } = await apiClient.delete<MenuItemResponse>(
            `/menu-items/${itemId}`
        );
        return data;
    },
};