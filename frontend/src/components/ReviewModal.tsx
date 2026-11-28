'use client';

import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { AlertCircle, CheckCircle2, MessageSquare, Star } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { extractApiErrorMessage } from '@/lib/api-client';
import { reviewService } from '@/services/review.service';
import type { ReviewResponse } from '@/types/api';

export interface ReviewModalProps {
    isOpen: boolean;
    onClose: () => void;
    orderId: string;
    orderCode?: string;
    dishName?: string;
    onSuccess?: (review: ReviewResponse) => void;
}

const DEFAULT_REVIEW_TAGS = [
    'Món ăn ngon',
    'Đúng giờ',
    'Đóng gói cẩn thận',
    'Hợp vệ sinh',
    'Sẽ ủng hộ tiếp',
    'Giá rất hợp lý',
];

const RATING_DESCRIPTIONS: Record<number, string> = {
    1: 'Rất không hài lòng (1/5)',
    2: 'Chưa hài lòng (2/5)',
    3: 'Bình thường (3/5)',
    4: 'Hài lòng (4/5)',
    5: 'Rất hài lòng, tuyệt vời (5/5)',
};

export function ReviewModal({
    isOpen,
    onClose,
    orderId,
    orderCode,
    dishName,
    onSuccess,
}: ReviewModalProps) {
    const [rating, setRating] = useState<number>(5);
    const [hoverRating, setHoverRating] = useState<number>(0);
    const [comment, setComment] = useState<string>('');
    const [selectedTags, setSelectedTags] = useState<string[]>([]);
    const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [validationError, setValidationError] = useState<string | null>(null);
    const [isSuccess, setIsSuccess] = useState<boolean>(false);

    // Reset form state on open / close
    useEffect(() => {
        if (isOpen) {
            setRating(5);
            setHoverRating(0);
            setComment('');
            setSelectedTags([]);
            setIsSubmitting(false);
            setError(null);
            setValidationError(null);
            setIsSuccess(false);
        }
    }, [isOpen]);

    const handleTagToggle = (tag: string) => {
        setSelectedTags((prev) =>
            prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
        );
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setValidationError(null);

        if (!rating || rating < 1 || rating > 5) {
            setValidationError('Vui lòng chọn số sao đánh giá từ 1 đến 5 sao.');
            return;
        }

        setIsSubmitting(true);
        try {
            const review = await reviewService.createReview(orderId, {
                rating,
                comment: comment.trim() || null,
                tags: selectedTags,
                photo_urls: [],
            });

            setIsSuccess(true);
            if (onSuccess) {
                onSuccess(review);
            }
            // Auto close after brief display
            setTimeout(() => {
                onClose();
            }, 1200);
        } catch (err: unknown) {
            if (axios.isAxiosError(err) && err.response?.status === 409) {
                // 409 Conflict - order already reviewed
                const detail = err.response.data?.detail;
                setError(
                    typeof detail === 'string'
                        ? detail
                        : 'Đơn hàng này đã được đánh giá trước đó. Cảm ơn bạn!'
                );
            } else {
                setError(
                    extractApiErrorMessage(
                        err,
                        'Không thể gửi đánh giá lúc này. Vui lòng thử lại sau.'
                    )
                );
            }
        } finally {
            setIsSubmitting(false);
        }
    };

    const activeRatingDisplay = hoverRating || rating;

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title="Đánh giá món ăn giải cứu"
            className="max-w-md"
        >
            {isSuccess ? (
                <div className="py-6 text-center">
                    <CheckCircle2 className="mx-auto h-12 w-12 text-emerald-600 animate-bounce" />
                    <h4 className="mt-3 text-lg font-bold text-gray-900">
                        Cảm ơn đánh giá của bạn!
                    </h4>
                    <p className="mt-1 text-sm text-gray-500">
                        Phản hồi của bạn giúp quán ăn cải thiện chất lượng và giảm lãng phí thực phẩm.
                    </p>
                </div>
            ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                    {orderCode && (
                        <div className="rounded-lg bg-gray-50 p-2.5 text-xs text-gray-600">
                            Đơn hàng:{' '}
                            <span className="font-semibold text-gray-900">{orderCode}</span>
                            {dishName && (
                                <>
                                    {' '}
                                    • Món:{' '}
                                    <span className="font-semibold text-emerald-800">
                                        {dishName}
                                    </span>
                                </>
                            )}
                        </div>
                    )}

                    {error && (
                        <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700">
                            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                            <span>{error}</span>
                        </div>
                    )}

                    {validationError && (
                        <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-700">
                            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                            <span>{validationError}</span>
                        </div>
                    )}

                    {/* Star Rating Selection */}
                    <div>
                        <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                            Mức độ hài lòng của bạn <span className="text-red-500">*</span>
                        </label>
                        <div className="flex items-center gap-1.5">
                            {[1, 2, 3, 4, 5].map((star) => (
                                <button
                                    key={star}
                                    type="button"
                                    onClick={() => {
                                        setRating(star);
                                        setValidationError(null);
                                    }}
                                    onMouseEnter={() => setHoverRating(star)}
                                    onMouseLeave={() => setHoverRating(0)}
                                    className="rounded p-1 text-gray-300 transition-colors hover:scale-110 focus:outline-hidden"
                                    aria-label={`${star} sao`}
                                >
                                    <Star
                                        className={`h-7 w-7 transition-colors ${
                                            star <= activeRatingDisplay
                                                ? 'fill-amber-400 text-amber-400'
                                                : 'text-gray-300 hover:text-amber-200'
                                        }`}
                                    />
                                </button>
                            ))}
                        </div>
                        <p className="mt-1 text-xs text-gray-500 min-h-[1rem]">
                            {RATING_DESCRIPTIONS[activeRatingDisplay] || ''}
                        </p>
                    </div>

                    {/* Quick Tags */}
                    <div>
                        <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                            Điểm bạn thích ở món ăn này:
                        </label>
                        <div className="flex flex-wrap gap-1.5">
                            {DEFAULT_REVIEW_TAGS.map((tag) => {
                                const isSelected = selectedTags.includes(tag);
                                return (
                                    <button
                                        key={tag}
                                        type="button"
                                        onClick={() => handleTagToggle(tag)}
                                        className={`rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
                                            isSelected
                                                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200 border border-transparent'
                                        }`}
                                    >
                                        {tag}
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Comment text area */}
                    <div>
                        <label
                            htmlFor="review-comment"
                            className="block text-xs font-semibold text-gray-700 mb-1.5"
                        >
                            Nhận xét chi tiết (tùy chọn)
                        </label>
                        <div className="relative">
                            <textarea
                                id="review-comment"
                                rows={3}
                                maxLength={500}
                                value={comment}
                                onChange={(e) => setComment(e.target.value)}
                                placeholder="Hãy chia sẻ cảm nhận của bạn về chất lượng món ăn và dịch vụ của quán..."
                                className="w-full rounded-xl border border-gray-300 p-2.5 text-xs text-gray-900 placeholder-gray-400 focus:border-emerald-500 focus:outline-hidden focus:ring-1 focus:ring-emerald-500"
                            />
                            <div className="mt-1 flex items-center justify-between text-[11px] text-gray-400">
                                <span className="inline-flex items-center gap-1">
                                    <MessageSquare className="h-3 w-3" />
                                    Tối đa 500 ký tự
                                </span>
                                <span>{comment.length}/500</span>
                            </div>
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center justify-end gap-2 pt-2 border-t border-gray-100">
                        <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={onClose}
                            disabled={isSubmitting}
                        >
                            Hủy
                        </Button>
                        <Button
                            type="submit"
                            size="sm"
                            disabled={isSubmitting || rating < 1}
                            isLoading={isSubmitting}
                        >
                            Gửi đánh giá
                        </Button>
                    </div>
                </form>
            )}
        </Modal>
    );
}
