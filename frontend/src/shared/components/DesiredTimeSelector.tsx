import React, { useEffect, useState } from 'react';
import { Clock } from 'lucide-react';

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
      ? 'bg-[#E87838] text-white shadow-sm'
      : 'bg-[#181512] text-white shadow-sm';

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
            className={`rounded-full px-3 py-1.5 text-[12px] font-semibold tabular-nums transition ${
              isActive
                ? activeClass
                : 'border border-[#DFD3C3] bg-[#FAF7F2] text-[#4A4139] hover:border-[#E87838] hover:text-[#C2591B]'
            }`}
          >
            {preset.label}
          </button>
        );
      })}

      <label
        className={`inline-flex items-center gap-1.5 rounded-full border border-[#DFD3C3] bg-[#FAF7F2] px-3 py-1 text-[12px] text-[#4A4139] focus-within:border-[#E87838] ${
          compact ? 'mt-0.5' : ''
        }`}
      >
        <Clock className="h-3 w-3 shrink-0 text-[#E87838]" aria-hidden="true" />
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
          className="w-12 bg-transparent text-[12px] font-semibold text-[#181512] tabular-nums placeholder:font-normal placeholder:text-[#8C8277] focus:outline-none"
        />
        <span className="text-[11px] text-[#6E655C]">phút</span>
      </label>
    </div>
  );
};
