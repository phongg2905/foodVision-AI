import React, { useEffect, useState } from 'react';

export interface DesiredTimeSelectorProps {
  desiredMinutes: number | null;
  onDesiredMinutesChange: (minutes: number | null) => void;
  testIdPrefix?: string;
  activeTone?: 'saffron' | 'espresso';
  compact?: boolean;
}

const TIME_PRESETS: Array<{ value: number | null; label: string }> = [
  { value: null, label: 'Linh hoạt' },
  { value: 15, label: '15 phút' },
  { value: 30, label: '30 phút' },
  { value: 45, label: '45 phút' },
  { value: 60, label: '60 phút' },
];

export const DesiredTimeSelector: React.FC<DesiredTimeSelectorProps> = ({
  desiredMinutes,
  onDesiredMinutesChange,
  testIdPrefix = 'desired-time-preset',
  activeTone = 'saffron',
  compact = false,
}) => {
  const isPresetValue =
    desiredMinutes === null ||
    TIME_PRESETS.some((p) => p.value === desiredMinutes);
  const [customInput, setCustomInput] = useState(
    !isPresetValue && desiredMinutes !== null ? String(desiredMinutes) : ''
  );

  useEffect(() => {
    if (
      desiredMinutes === null ||
      TIME_PRESETS.some((p) => p.value === desiredMinutes)
    ) {
      setCustomInput('');
    } else {
      setCustomInput(String(desiredMinutes));
    }
  }, [desiredMinutes]);

  const handlePresetClick = (value: number | null) => {
    setCustomInput('');
    onDesiredMinutesChange(value);
  };

  const handleCustomChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    setCustomInput(raw);
    if (raw.trim() === '') {
      onDesiredMinutesChange(null);
      return;
    }
    const parsed = Number(raw);
    if (Number.isFinite(parsed) && parsed >= 1 && parsed <= 720) {
      onDesiredMinutesChange(Math.round(parsed));
    }
  };

  const activeClass =
    activeTone === 'saffron'
      ? 'bg-[#B4490E] text-white'
      : 'bg-[#181512] text-[#FFF8F0]';

  return (
    <div
      role="group"
      aria-label="Chọn thời gian nấu mong muốn"
      className="flex flex-wrap items-center gap-1.5"
    >
      {TIME_PRESETS.map((preset) => {
        const isActive = desiredMinutes === preset.value;
        return (
          <button
            key={preset.label}
            type="button"
            data-testid={`${testIdPrefix}-${preset.value ?? 'flexible'}`}
            aria-pressed={isActive}
            onClick={() => handlePresetClick(preset.value)}
            className={`inline-flex min-h-[34px] items-center justify-center rounded-full px-3.5 py-1 text-[12.5px] font-medium tabular-nums transition ${
              isActive
                ? activeClass
                : 'bg-[#EFE2D2] text-[#3B3027] hover:bg-[#E5D4BF]'
            }`}
          >
            {preset.label}
          </button>
        );
      })}

      <label
        className={`inline-flex min-h-[34px] items-center gap-1 rounded-full border border-[#D5C2AC] bg-[#FFFDF9] px-3 py-1 text-[12.5px] text-[#3B3027] focus-within:border-[#B4490E] ${
          compact ? 'mt-0.5' : ''
        }`}
      >
        <input
          type="number"
          min={1}
          max={720}
          inputMode="numeric"
          value={customInput}
          onChange={handleCustomChange}
          placeholder="Khác"
          aria-label="Nhập thời gian nấu mong muốn (phút)"
          data-testid={`${testIdPrefix}-custom-input`}
          className="w-11 bg-transparent text-[12.5px] font-semibold text-[#181512] tabular-nums placeholder:font-normal placeholder:text-[#6B5E52] focus:outline-none"
        />
        <span className="text-[11.5px] text-[#595047]">phút</span>
      </label>
    </div>
  );
};
