import React, { useEffect, useRef, useState } from 'react';
import { Search, Check, Plus, X } from 'lucide-react';
import { Ingredient } from '../../../shared/api/types';
import { searchMainIngredients } from '../../../shared/api/ingredientsApi';
import { getMatchedAliasHint } from '../../../shared/utils/vietnamese';

export interface IngredientSearchBoxProps {
  selectedIngredients: Ingredient[];
  onAddIngredient: (ingredient: Ingredient) => void;
  onSearchingChange?: (isSearching: boolean) => void;
  onQueryChange?: (query: string) => void;
  onDropdownOpenChange?: (isOpen: boolean) => void;
}

export const IngredientSearchBox: React.FC<IngredientSearchBoxProps> = ({
  selectedIngredients,
  onAddIngredient,
  onSearchingChange,
  onQueryChange,
  onDropdownOpenChange,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<Ingredient[]>([]);
  const [duplicateNotice, setDuplicateNotice] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  const selectedIdSet = new Set(selectedIngredients.map((item) => item.id));
  const isSearching = query.trim().length > 0;
  const showDropdown = isSearching && isOpen;

  useEffect(() => {
    onSearchingChange?.(isSearching);
    onQueryChange?.(query);
  }, [isSearching, query, onSearchingChange, onQueryChange]);

  useEffect(() => {
    onDropdownOpenChange?.(showDropdown);
  }, [showDropdown, onDropdownOpenChange]);

  // Đóng khung gợi ý khi bấm chuột ra ngoài ô tìm kiếm
  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setActiveIndex(-1);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, []);

  useEffect(() => {
    let isCancelled = false;

    const timer = window.setTimeout(() => {
      searchMainIngredients(query, 20, 0).then((res) => {
        if (!isCancelled) {
          setSuggestions(res.items);
          setActiveIndex(-1);
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
    setQuery('');
    setIsOpen(false);
    setActiveIndex(-1);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape') {
      if (showDropdown) {
        e.preventDefault();
        setIsOpen(false);
        setActiveIndex(-1);
      }
      return;
    }

    if (!showDropdown || suggestions.length === 0) {
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((prev) => (prev + 1) % suggestions.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((prev) =>
        prev <= 0 ? suggestions.length - 1 : prev - 1
      );
    } else if (e.key === 'Enter' && activeIndex >= 0) {
      e.preventDefault();
      const target = suggestions[activeIndex];
      if (target) {
        handleSelectSuggestion(target);
      }
    }
  };

  const activeDescendantId =
    showDropdown && activeIndex >= 0 && suggestions[activeIndex]
      ? `ingredient-option-${suggestions[activeIndex].slug}`
      : undefined;

  return (
    <div
      ref={containerRef}
      aria-label="Tìm kiếm và chọn nguyên liệu chính"
      className="relative w-full"
    >
      {/* Thanh Search Box tích hợp ngay trong đầu Bàn Chọn Nguyên Liệu */}
      <div className="flex min-h-[46px] items-center gap-3 rounded-tl-[16px] rounded-br-[16px] rounded-tr-[6px] rounded-bl-[6px] border border-[#D8C6B2] bg-[#F7EFE5] px-4 py-2 transition focus-within:border-[#181512] focus-within:bg-[#FFF8F0] focus-within:shadow-sm">
        <Search
          className="h-4 w-4 shrink-0 text-[#595047]"
          aria-hidden="true"
        />
        <input
          type="search"
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={showDropdown}
          aria-controls="ingredient-autocomplete-list"
          aria-activedescendant={activeDescendantId}
          value={query}
          onFocus={() => {
            if (isSearching) setIsOpen(true);
          }}
          onChange={(e) => {
            const nextVal = e.target.value;
            setQuery(nextVal);
            setIsOpen(nextVal.trim().length > 0);
            setDuplicateNotice(null);
            setActiveIndex(-1);
          }}
          onKeyDown={handleKeyDown}
          placeholder="Tìm nguyên liệu: đậu phụ, cà chua, ngô..."
          aria-label="Nhập tên nguyên liệu chính"
          className="w-full border-0 bg-transparent p-0 text-[14px] font-medium text-[#181512] placeholder:font-normal placeholder:text-[#7D7064] focus:outline-none focus:ring-0"
        />
        {query.length > 0 && (
          <button
            type="button"
            onClick={() => {
              setQuery('');
              setIsOpen(false);
              setDuplicateNotice(null);
              setActiveIndex(-1);
            }}
            aria-label="Xóa từ khóa tìm kiếm"
            className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#EFE4D6] text-[#4A4037] transition hover:bg-[#E2D3C1]"
          >
            <X className="h-3.5 w-3.5 stroke-[2.5]" aria-hidden="true" />
          </button>
        )}
      </div>

      {duplicateNotice && (
        <p
          role="status"
          data-testid="duplicate-ingredient-notice"
          className="mt-2 rounded-xl border border-[#E5C98E] bg-[#FDF2D6] px-3.5 py-2 text-xs font-medium text-[#7C4706]"
        >
          {duplicateNotice}
        </p>
      )}

      {/* Chỉ xổ danh sách gợi ý khi người dùng đang gõ từ khóa tìm kiếm */}
      {showDropdown && (
        <div
          data-testid="ingredient-search-dropdown"
          className="mt-2 rounded-tl-[18px] rounded-br-[18px] rounded-tr-[6px] rounded-bl-[6px] border border-[#D8C6B2] bg-[#FFF8F0] p-2 shadow-[0_14px_35px_rgba(24,21,18,0.12)]"
        >
          {suggestions.length === 0 ? (
            <p
              data-testid="ingredient-search-empty"
              className="py-3 text-center text-xs text-[#595047]"
            >
              Không tìm thấy nguyên liệu khớp với &ldquo;{query}&rdquo;.
            </p>
          ) : (
            <ul
              id="ingredient-autocomplete-list"
              role="listbox"
              aria-label="Danh sách gợi ý nguyên liệu chính"
              className="max-h-[240px] space-y-1 overflow-y-auto"
            >
              {suggestions.map((item, idx) => {
                const isSelected = selectedIdSet.has(item.id);
                const isKeyboardActive = idx === activeIndex;
                const aliasHint = getMatchedAliasHint(item.slug, query);

                return (
                  <li key={item.id} role="presentation">
                    <button
                      id={`ingredient-option-${item.slug}`}
                      type="button"
                      role="option"
                      aria-selected={isKeyboardActive}
                      data-testid={`suggestion-item-${item.slug}`}
                      onClick={() => handleSelectSuggestion(item)}
                      className={`group flex min-h-[40px] w-full items-center justify-between rounded-xl px-3.5 py-2 text-left transition ${
                        isKeyboardActive
                          ? 'bg-[#EFE2D2] text-[#181512] ring-1 ring-[#C65112]/40'
                          : isSelected
                            ? 'bg-[#FAF3EB] text-[#181512]'
                            : 'bg-transparent text-[#181512] hover:bg-[#F7EFE5]'
                      }`}
                    >
                      <div className="flex min-w-0 items-center gap-2 truncate">
                        <span className="truncate text-[14px] font-medium text-[#181512]">
                          {item.name_vi}
                        </span>
                        {aliasHint && (
                          <span className="truncate text-xs font-semibold text-[#9E3D08]">
                            ({aliasHint})
                          </span>
                        )}
                      </div>

                      {isSelected ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-[#6E6256] px-2.5 py-0.5 text-[11px] font-medium text-white">
                          <Check className="h-3 w-3 stroke-[2.5]" />
                          <span>Đã chọn</span>
                        </span>
                      ) : (
                        <span className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#EFE4D6] text-[#4A4037] transition group-hover:bg-[#C65112] group-hover:text-white">
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
