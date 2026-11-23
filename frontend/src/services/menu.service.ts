import { apiClient } from '@/lib/api-client';
import type {
    MenuItemCreatePayload,
    MenuItemListResponse,
    MenuItemResponse,
    MenuItemUpdatePayload,
} from '@/types/api';

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