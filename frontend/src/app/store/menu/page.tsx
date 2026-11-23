'use client';

import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import {
    AlertTriangle,
    BookOpen,
    CheckCircle2,
    Clock,
    Edit3,
    Plus,
    Store,
    Trash2,
    X,
} from 'lucide-react';
import { AuthGuard } from '@/components/auth/AuthGuard';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Toast } from '@/components/ui/Toast';
import { extractApiErrorMessage } from '@/lib/api-client';
import { formatVND } from '@/lib/utils';
import { menuService } from '@/services/menu.service';
import { storeService } from '@/services/store.service';
import type {
    DietaryType,
    FoodCategory,
    MenuItemCreatePayload,
    MenuItemResponse,
    StoreDetailResponse,
} from '@/types/api';

const PARTNER_ROLES = ['STORE_PARTNER', 'ADMIN'];

const CATEGORY_OPTIONS: Array<{ value: FoodCategory; label: string }> = [
    { value: 'RICE', label: 'Cơm / Món mặn' },
    { value: 'NOODLES', label: 'Bún / Phở / Mì' },
    { value: 'BAKERY', label: 'Bánh ngọt / Bánh mì' },
    { value: 'VEGETARIAN', label: 'Món chay' },
    { value: 'DRINKS', label: 'Đồ uống' },
    { value: 'OTHER', label: 'Khác' },
];

const DIETARY_OPTIONS: Array<{ value: DietaryType; label: string }> = [
    { value: 'NON_VEGAN', label: 'Món thường (Non-Vegan)' },
    { value: 'VEGETARIAN', label: 'Ăn chay có trứng/sữa (Vegetarian)' },
    { value: 'VEGAN', label: 'Thuần chay (Vegan)' },
];

const DEFAULT_FOOD_IMAGE =
    'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=800&q=80';

export default function StoreMenuPage() {
    const [store, setStore] = useState<StoreDetailResponse | null>(null);
    const [storeNotFound, setStoreNotFound] = useState(false);
    const [menuItems, setMenuItems] = useState<MenuItemResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [editingItem, setEditingItem] = useState<MenuItemResponse | null>(null);
    const [toast, setToast] = useState<{
        message: string;
        type: 'success' | 'error' | 'info';
    } | null>(null);

    // Form state
    const [name, setName] = useState('');
    const [category, setCategory] = useState<FoodCategory>('RICE');
    const [originalPrice, setOriginalPrice] = useState('');
    const [imageUrl, setImageUrl] = useState(DEFAULT_FOOD_IMAGE);
    const [description, setDescription] = useState('');
    const [dietaryType, setDietaryType] = useState<DietaryType>('NON_VEGAN');
    const [ingredientsText, setIngredientsText] = useState('');
    const [allergensText, setAllergensText] = useState('');

    const resetForm = () => {
        setEditingItem(null);
        setName('');
        setCategory('RICE');
        setOriginalPrice('');
        setImageUrl(DEFAULT_FOOD_IMAGE);
        setDescription('');
        setDietaryType('NON_VEGAN');
        setIngredientsText('');
        setAllergensText('');
    };

    const loadStoreAndMenu = useCallback(async () => {
        setLoading(true);
        setStoreNotFound(false);
        try {
            const myStore = await storeService.getMyStore();
            setStore(myStore);
            if (myStore.kyc_status === 'APPROVED') {
                const items = await menuService.getStoreMenuItems(myStore.id);
                setMenuItems(items);
            }
        } catch (err: unknown) {
            const status = (err as { response?: { status?: number } })?.response?.status;
            if (status === 404) {
                setStoreNotFound(true);
            } else {
                setToast({
                    message: extractApiErrorMessage(err, 'Không thể tải thông tin cửa hàng.'),
                    type: 'error',
                });
            }
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        void loadStoreAndMenu();
    }, [loadStoreAndMenu]);

    const handleEditClick = (item: MenuItemResponse) => {
        setEditingItem(item);
        setName(item.name);
        setCategory((item.category as FoodCategory) || 'RICE');
        setOriginalPrice(String(Number(item.original_price)));
        setImageUrl(item.image_url || DEFAULT_FOOD_IMAGE);
        setDescription(item.description || '');
        setDietaryType(item.dietary_type || 'NON_VEGAN');
        setIngredientsText((item.standard_ingredients || []).join(', '));
        setAllergensText((item.base_allergens || []).join(', '));
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!store) return;

        const priceNum = Number(originalPrice);
        if (!name.trim() || name.trim().length < 2) {
            setToast({ message: 'Tên món ăn phải có ít nhất 2 ký tự.', type: 'error' });
            return;
        }
        if (Number.isNaN(priceNum) || priceNum <= 0) {
            setToast({ message: 'Giá gốc phải lớn hơn 0 VNĐ.', type: 'error' });
            return;
        }
        if (!imageUrl.trim() || imageUrl.trim().length < 5) {
            setToast({ message: 'Vui lòng nhập đường dẫn hình ảnh hợp lệ.', type: 'error' });
            return;
        }

        const payload: MenuItemCreatePayload = {
            name: name.trim(),
            category,
            original_price: priceNum,
            image_url: imageUrl.trim(),
            description: description.trim() || null,
            dietary_type: dietaryType,
            standard_ingredients: ingredientsText
                .split(',')
                .map((s) => s.trim())
                .filter(Boolean),
            base_allergens: allergensText
                .split(',')
                .map((s) => s.trim())
                .filter(Boolean),
        };

        setSubmitting(true);
        try {
            if (editingItem) {
                const updated = await menuService.updateMenuItem(editingItem.id, payload);
                setMenuItems((prev) =>
                    prev.map((item) => (item.id === updated.id ? updated : item))
                );
                setToast({ message: `Đã cập nhật món "${updated.name}".`, type: 'success' });
            } else {
                const created = await menuService.createMenuItem(store.id, payload);
                setMenuItems((prev) => [created, ...prev]);
                setToast({ message: `Đã thêm "${created.name}" vào thực đơn gốc.`, type: 'success' });
            }
            resetForm();
        } catch (err: unknown) {
            setToast({
                message: extractApiErrorMessage(err, 'Không thể lưu món ăn vào thực đơn.'),
                type: 'error',
            });
        } finally {
            setSubmitting(false);
        }
    };

    const handleDelete = async (item: MenuItemResponse) => {
        if (!window.confirm(`Xóa món "${item.name}" khỏi thực đơn đang phục vụ?`)) return;
        try {
            await menuService.deleteMenuItem(item.id);
            setMenuItems((prev) => prev.filter((m) => m.id !== item.id));
            if (editingItem?.id === item.id) resetForm();
            setToast({ message: `Đã xóa "${item.name}" khỏi thực đơn.`, type: 'success' });
        } catch (err: unknown) {
            setToast({
                message: extractApiErrorMessage(err, 'Xóa món thất bại.'),
                type: 'error',
            });
        }
    };

    return (
        <AuthGuard allowedRoles={PARTNER_ROLES}>
            <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
                <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
                    <div>
                        <div className="mb-2 inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
                            <BookOpen className="h-3.5 w-3.5" />
                            Menu Grounding • Chống nâng khống giá gốc
                        </div>
                        <h1 className="text-2xl font-bold text-gray-900">
                            Quản lý Thực đơn Gốc của Quán
                        </h1>
                        <p className="mt-1 text-sm text-gray-500">
                            Niêm yết danh mục món chuẩn và giá bán gốc làm cơ sở tính mức giảm giá giải cứu.
                        </p>
                    </div>

                    {store?.kyc_status === 'APPROVED' && (
                        <Link href="/store/dishes">
                            <Button variant="outline">Sang trang Mở bán Món dư →</Button>
                        </Link>
                    )}
                </div>

                {loading ? (
                    <div className="space-y-4">
                        <div className="h-44 animate-pulse rounded-xl bg-gray-100" />
                        <div className="h-64 animate-pulse rounded-xl bg-gray-100" />
                    </div>
                ) : storeNotFound || !store ? (
                    <Card className="p-8 text-center">
                        <Store className="mx-auto h-10 w-10 text-emerald-600" />
                        <h2 className="mt-3 text-lg font-bold text-gray-900">
                            Tài khoản chưa liên kết cửa hàng
                        </h2>
                        <p className="mt-1 text-sm text-gray-600">
                            Vui lòng hoàn tất hồ sơ đăng ký đối tác và giấy chứng nhận ATVSTP trước khi tạo thực đơn.
                        </p>
                        <div className="mt-5">
                            <Link href="/store/onboard">
                                <Button>Đăng ký Cửa hàng (KYC)</Button>
                            </Link>
                        </div>
                    </Card>
                ) : store.kyc_status === 'PENDING' ? (
                    <Card className="border-amber-300 bg-amber-50/70 p-6">
                        <div className="flex items-start gap-3">
                            <Clock className="mt-0.5 h-6 w-6 shrink-0 text-amber-600" />
                            <div>
                                <h2 className="text-base font-bold text-amber-900">
                                    Hồ sơ cửa hàng &ldquo;{store.name}&rdquo; đang chờ Admin duyệt KYC
                                </h2>
                                <p className="mt-1 text-sm text-amber-800">
                                    Chức năng thêm thực đơn và đăng món dư sẽ tự động mở khóa ngay sau khi Admin phê duyệt chứng nhận ATVSTP.
                                </p>
                            </div>
                        </div>
                    </Card>
                ) : store.kyc_status === 'REJECTED' ? (
                    <Card className="border-red-300 bg-red-50 p-6">
                        <div className="flex items-start gap-3">
                            <AlertTriangle className="mt-0.5 h-6 w-6 shrink-0 text-red-600" />
                            <div>
                                <h2 className="text-base font-bold text-red-900">
                                    Hồ sơ KYC của &ldquo;{store.name}&rdquo; đã bị từ chối
                                </h2>
                                {store.kyc_reject_reason && (
                                    <p className="mt-1 text-sm text-red-800">
                                        Lý do: {store.kyc_reject_reason}
                                    </p>
                                )}
                                <div className="mt-4">
                                    <Link href="/store/onboard">
                                        <Button variant="danger" size="sm">
                                            Cập nhật lại hồ sơ KYC
                                        </Button>
                                    </Link>
                                </div>
                            </div>
                        </div>
                    </Card>
                ) : (
                    <div className="grid gap-8 lg:grid-cols-12">
                        {/* Form Thêm / Sửa Món Gốc */}
                        <Card className="h-fit p-6 lg:col-span-5">
                            <div className="mb-4 flex items-center justify-between">
                                <h2 className="text-base font-bold text-gray-900">
                                    {editingItem ? 'Cập nhật món trong thực đơn' : 'Thêm món mới vào thực đơn'}
                                </h2>
                                {editingItem && (
                                    <button
                                        type="button"
                                        onClick={resetForm}
                                        className="inline-flex items-center gap-1 text-xs font-medium text-gray-500 hover:text-gray-800"
                                    >
                                        <X className="h-3.5 w-3.5" /> Hủy sửa
                                    </button>
                                )}
                            </div>

                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div>
                                    <label className="mb-1 block text-xs font-semibold text-gray-700">
                                        Tên món ăn *
                                    </label>
                                    <input
                                        type="text"
                                        required
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        placeholder="Ví dụ: Cơm tấm sườn bì chả"
                                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
                                    />
                                </div>

                                <div className="grid grid-cols-2 gap-3">
                                    <div>
                                        <label className="mb-1 block text-xs font-semibold text-gray-700">
                                            Danh mục *
                                        </label>
                                        <select
                                            value={category}
                                            onChange={(e) => setCategory(e.target.value as FoodCategory)}
                                            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
                                        >
                                            {CATEGORY_OPTIONS.map((opt) => (
                                                <option key={opt.value} value={opt.value}>
                                                    {opt.label}
                                                </option>
                                            ))}
                                        </select>
                                    </div>

                                    <div>
                                        <label className="mb-1 block text-xs font-semibold text-gray-700">
                                            Giá gốc niêm yết (VNĐ) *
                                        </label>
                                        <input
                                            type="number"
                                            required
                                            min={1000}
                                            step={500}
                                            value={originalPrice}
                                            onChange={(e) => setOriginalPrice(e.target.value)}
                                            placeholder="45000"
                                            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="mb-1 block text-xs font-semibold text-gray-700">
                                        Chế độ ăn
                                    </label>
                                    <select
                                        value={dietaryType}
                                        onChange={(e) => setDietaryType(e.target.value as DietaryType)}
                                        className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
                                    >
                                        {DIETARY_OPTIONS.map((opt) => (
                                            <option key={opt.value} value={opt.value}>
                                                {opt.label}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div>
                                    <label className="mb-1 block text-xs font-semibold text-gray-700">
                                        Đường dẫn ảnh món ăn (URL) *
                                    </label>
                                    <input
                                        type="url"
                                        required
                                        value={imageUrl}
                                        onChange={(e) => setImageUrl(e.target.value)}
                                        placeholder="https://..."
                                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
                                    />
                                </div>

                                <div>
                                    <label className="mb-1 block text-xs font-semibold text-gray-700">
                                        Nguyên liệu chính (cách nhau bằng dấu phẩy)
                                    </label>
                                    <input
                                        type="text"
                                        value={ingredientsText}
                                        onChange={(e) => setIngredientsText(e.target.value)}
                                        placeholder="Gạo tấm, sườn cốt lết, trứng, đồ chua"
                                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
                                    />
                                </div>

                                <div>
                                    <label className="mb-1 block text-xs font-semibold text-gray-700">
                                        Cảnh báo dị ứng (cách nhau bằng dấu phẩy)
                                    </label>
                                    <input
                                        type="text"
                                        value={allergensText}
                                        onChange={(e) => setAllergensText(e.target.value)}
                                        placeholder="Đậu phộng, Hải sản, Trứng"
                                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
                                    />
                                </div>

                                <div>
                                    <label className="mb-1 block text-xs font-semibold text-gray-700">
                                        Mô tả ngắn
                                    </label>
                                    <textarea
                                        rows={2}
                                        value={description}
                                        onChange={(e) => setDescription(e.target.value)}
                                        placeholder="Khẩu phần đầy đủ kèm canh và nước mắm pha..."
                                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
                                    />
                                </div>

                                <Button type="submit" className="w-full" isLoading={submitting}>
                                    <Plus className="h-4 w-4" />
                                    {editingItem ? 'Lưu thay đổi' : 'Thêm vào Thực đơn gốc'}
                                </Button>
                            </form>
                        </Card>

                        {/* Danh sách Món Gốc Hiện Có */}
                        <div className="space-y-4 lg:col-span-7">
                            <div className="flex items-center justify-between">
                                <h2 className="text-base font-bold text-gray-900">
                                    Danh mục đang phục vụ ({menuItems.length} món)
                                </h2>
                                <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700">
                                    <CheckCircle2 className="h-3.5 w-3.5" /> {store.name}
                                </span>
                            </div>

                            {menuItems.length === 0 ? (
                                <Card className="border-dashed p-10 text-center">
                                    <p className="text-sm font-medium text-gray-700">
                                        Quán chưa có món ăn nào trong thực đơn gốc.
                                    </p>
                                    <p className="mt-1 text-xs text-gray-500">
                                        Hãy tạo ít nhất 1 món ở biểu mẫu bên trái để bắt đầu đăng bán món dư cuối ca.
                                    </p>
                                </Card>
                            ) : (
                                <div className="space-y-3">
                                    {menuItems.map((item) => (
                                        <Card key={item.id} className="p-4">
                                            <div className="flex items-start justify-between gap-4">
                                                <div className="flex gap-3.5">
                                                    {/* eslint-disable-next-line @next/next/no-img-element */}
                                                    <img
                                                        src={item.image_url || DEFAULT_FOOD_IMAGE}
                                                        alt={item.name}
                                                        className="h-16 w-16 shrink-0 rounded-lg object-cover"
                                                    />
                                                    <div>
                                                        <div className="flex flex-wrap items-center gap-2">
                                                            <h3 className="font-semibold text-gray-900">
                                                                {item.name}
                                                            </h3>
                                                            <Badge variant="neutral">{item.category}</Badge>
                                                        </div>
                                                        <p className="mt-1 text-sm font-bold text-emerald-700">
                                                            Giá gốc: {formatVND(item.original_price)}
                                                        </p>
                                                        {item.base_allergens?.length > 0 && (
                                                            <p className="mt-1 text-xs text-amber-700">
                                                                Dị ứng: {item.base_allergens.join(', ')}
                                                            </p>
                                                        )}
                                                    </div>
                                                </div>

                                                <div className="flex shrink-0 items-center gap-1.5">
                                                    <button
                                                        type="button"
                                                        onClick={() => handleEditClick(item)}
                                                        title="Chỉnh sửa"
                                                        className="rounded-lg border border-gray-200 p-2 text-gray-600 hover:bg-gray-50 hover:text-emerald-700"
                                                    >
                                                        <Edit3 className="h-4 w-4" />
                                                    </button>
                                                    <button
                                                        type="button"
                                                        onClick={() => void handleDelete(item)}
                                                        title="Xóa món"
                                                        className="rounded-lg border border-gray-200 p-2 text-gray-600 hover:bg-red-50 hover:text-red-600"
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </button>
                                                </div>
                                            </div>
                                        </Card>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {toast && (
                    <Toast
                        message={toast.message}
                        type={toast.type}
                        onClose={() => setToast(null)}
                    />
                )}
            </div>
        </AuthGuard>
    );
}