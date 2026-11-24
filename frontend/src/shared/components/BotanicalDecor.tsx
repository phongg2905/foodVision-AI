import React from 'react';

export interface BotanicalDecorProps {
  variant: 'header-arcs' | 'rosemary' | 'basil';
  className?: string;
}

/**
 * Họa tiết đường cong và nhánh thảo mộc nét mảnh đặc trưng từ NEWTASTE Case Study.
 */
export const BotanicalDecor: React.FC<BotanicalDecorProps> = ({
  variant,
  className = '',
}) => {
  if (variant === 'header-arcs') {
    return (
      <svg
        viewBox="0 0 360 220"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
        className={`pointer-events-none select-none ${className}`}
      >
        <path
          d="M-20 185C95 170 198 110 245 -10"
          stroke="currentColor"
          strokeWidth="1.25"
          strokeLinecap="round"
        />
        <path
          d="M-20 212C118 192 232 124 282 -10"
          stroke="currentColor"
          strokeWidth="1.25"
          strokeLinecap="round"
        />
      </svg>
    );
  }

  if (variant === 'rosemary') {
    return (
      <svg
        viewBox="0 0 180 180"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
        className={`pointer-events-none select-none ${className}`}
      >
        <path
          d="M28 156C64 118 104 78 148 26"
          stroke="currentColor"
          strokeWidth="1.35"
          strokeLinecap="round"
        />
        <path
          d="M54 128C40 104 38 82 48 64C64 78 68 102 54 128Z"
          stroke="currentColor"
          strokeWidth="1.15"
          strokeLinejoin="round"
        />
        <path
          d="M66 116C92 126 114 124 132 110C114 96 90 98 66 116Z"
          stroke="currentColor"
          strokeWidth="1.15"
          strokeLinejoin="round"
        />
        <path
          d="M84 96C72 72 72 52 82 34C96 50 98 72 84 96Z"
          stroke="currentColor"
          strokeWidth="1.15"
          strokeLinejoin="round"
        />
        <path
          d="M96 84C120 92 142 88 158 74C140 62 118 66 96 84Z"
          stroke="currentColor"
          strokeWidth="1.15"
          strokeLinejoin="round"
        />
        <path
          d="M116 62C108 42 110 26 122 14C132 28 130 46 116 62Z"
          stroke="currentColor"
          strokeWidth="1.15"
          strokeLinejoin="round"
        />
        <path
          d="M126 52C146 56 162 48 172 34C156 26 138 34 126 52Z"
          stroke="currentColor"
          strokeWidth="1.15"
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  return (
    <svg
      viewBox="0 0 180 180"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className={`pointer-events-none select-none ${className}`}
    >
      <path
        d="M90 162V72"
        stroke="currentColor"
        strokeWidth="1.35"
        strokeLinecap="round"
      />
      <path
        d="M90 124C56 122 30 100 24 68C56 66 80 86 90 124Z"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinejoin="round"
      />
      <path
        d="M90 124C124 122 150 100 156 68C124 66 100 86 90 124Z"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinejoin="round"
      />
      <path
        d="M90 96C66 64 66 36 90 14C114 36 114 64 90 96Z"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinejoin="round"
      />
      <path
        d="M84 114L44 82M96 114L136 82M90 88V30"
        stroke="currentColor"
        strokeWidth="1"
        strokeLinecap="round"
      />
    </svg>
  );
};
