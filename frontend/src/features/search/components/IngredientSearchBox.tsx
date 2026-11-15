import React, { useEffect, useState } from 'react';
import { Search, Check, Plus, X } from 'lucide-react';
import { Ingredient } from '../../../shared/api/types';
import { searchMainIngredients } from '../../../shared/api/ingredientsApi';
import { getMatchedAliasHint } from '../../../shared/utils/vietnamese';

export interface IngredientSearchBoxProps {
  selectedIngredients: Ingredient[];
  onAddIngredient: (ingredient: Ingredient) => void;
  onSearchingChange?: (isSearching: boolean) => void;
  onQueryChange?: (query: string) => void;
}

export const IngredientSearchBox: React.FC<IngredientSearchBoxProps> = ({
  selectedIngredients,
  onAddIngredient,
  onSearchingChange,
  onQueryChange,
}) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<Ingredient[]>([]);
  const [duplicateNotice, setDuplicateNotice] = useState<string | null>(null);

  const selectedIdSet = new Set(selectedIngredients.map((item) => item.id));
  const isSearching = query.trim().length > 0;

  useEffect(() => {
    onSearchingChange?.(isSearching);
    onQueryChange?.(query);
  }, [isSearching, query, onSearchingChange, onQueryChange]);

  useEffect(() => {
    let isCancelled = false;

    const timer = window.setTimeout(() => {
      searchMainIngredients(query, 20, 0).then((res) => {
        if (!isCancelled) {
          setSuggestions(res.items);
        }
      });
    }, 120);

    return () => {
      isCancelled = true;
      window.clearTimeout(timer);
    };
  }, [query]);

  const handleSelectSuggestion = (ingredient: Ingredient) => {
    if (selectedIdSet.has(ingredient.id)) {
      setDuplicateNotice(
        `Nguyên liệu "${ingredient.name_vi}" đã có trong danh sách đã chọn.`
      );
      return;
    }
    setDuplicateNotice(null);
    onAddIngredient(ingredient);
  };

  return (
    <div
      aria-label="Tìm kiếm và chọn nguyên liệu chính"
      className="relative w-full"
    >
      {/* Thanh Search Box tích hợp ngay trong đầu Bàn Chọn Nguyên Liệu */}
      <div className="flex items-center gap-3 rounded-2xl border border-[#DFD3C3] bg-[#FAF7F2] px-4 py-3 transition focus-within:border-[#181512] focus-within:bg-white focus-within:shadow-sm">
        <Search
          className="h-4 w-4 shrink-0 text-[#6E655C]"
          aria-hidden="true"
        />
        <input
          type="search"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setDuplicateNotice(null);
          }}
          placeholder="Tìm nhanh nguyên liệu (VD: đậu phụ, ngô, cà chua, tôm tươi...)"
          aria-label="Nhập tên nguyên liệu chính"
          className="w-full border-0 bg-transparent p-0 text-[14px] font-medium text-[#181512] placeholder:font-normal placeholder:text-[#8C8277] focus:outline-none focus:ring-0"
        />
        {query.length > 0 && (
          <button
            type="button"
            onClick={() => {
              setQuery('');
              setDuplicateNotice(null);
            }}
            aria-label="Xóa từ khóa tìm kiếm"
            className="inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#EAECEE] text-[#374151] transition hover:bg-[#D5D9DD]"
          >
            <X className="h-3 w-3 stroke-[2.5]" aria-hidden="true" />
          </button>
        )}
      </div>

      {duplicateNotice && (
        <p
          role="status"
          data-testid="duplicate-ingredient-notice"
          className="mt-2 rounded-xl bg-[#FEF3C7] px-3.5 py-2 text-xs font-medium text-[#92400E]"
        >
          {duplicateNotice}
        </p>
      )}

      {/* Chỉ xổ danh sách gợi ý khi người dùng đang gõ từ khóa tìm kiếm */}
      {isSearching && (
        <div className="mt-2 rounded-2xl border border-[#DFD3C3] bg-white p-2 shadow-[0_14px_35px_rgba(24,21,18,0.12)]">
          {suggestions.length === 0 ? (
            <p
              data-testid="ingredient-search-empty"
              className="py-3 text-center text-xs text-[#6E655C]"
            >
              Không tìm thấy nguyên liệu khớp với &ldquo;{query}&rdquo;.
            </p>
          ) : (
            <ul
              aria-label="Danh sách gợi ý nguyên liệu chính"
              className="max-h-[240px] space-y-1 overflow-y-auto"
            >
              {suggestions.map((item) => {
                const isSelected = selectedIdSet.has(item.id);
                const aliasHint = getMatchedAliasHint(item.slug, query);

                return (
                  <li key={item.id}>
                    <button
                      type="button"
                      data-testid={`suggestion-item-${item.slug}`}
                      onClick={() => handleSelectSuggestion(item)}
                      className={`group flex w-full items-center justify-between rounded-xl px-3.5 py-2.5 text-left transition ${
                        isSelected
                          ? 'bg-[#F4F6F8] text-[#181512]'
                          : 'bg-transparent text-[#181512] hover:bg-[#FAF7F2]'
                      }`}
                    >
                      <div className="flex min-w-0 items-center gap-2 truncate">
                        <span className="truncate text-[14px] font-medium text-[#181512]">
                          {item.name_vi}
                        </span>
                        {aliasHint && (
                          <span className="truncate text-xs font-semibold text-[#E87838]">
                            ({aliasHint})
                          </span>
                        )}
                      </div>

                      {isSelected ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-[#6E7781] px-2.5 py-0.5 text-[11px] font-medium text-white">
                          <Check className="h-3 w-3 stroke-[2.5]" />
                          <span>Đã chọn</span>
                        </span>
                      ) : (
                        <span className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#EAECEE] text-[#374151] transition group-hover:bg-[#E87838] group-hover:text-white">
                          <Plus className="h-3.5 w-3.5 stroke-[2.5]" />
                        </span>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};
