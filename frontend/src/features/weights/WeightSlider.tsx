interface WeightSliderProps {
  criterionId: string
  label: string
  value: number
  effectivePercent: number
  onChange: (criterionId: string, value: number) => void
}

export function WeightSlider({
  criterionId,
  label,
  value,
  effectivePercent,
  onChange,
}: WeightSliderProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(criterionId, parseInt(e.target.value, 10))
  }

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <button
          type="button"
          onClick={() => {
            const el = document.getElementById(`criterion-${criterionId}`)
            if (el) {
              el.scrollIntoView({ behavior: 'smooth' })
              el.classList.add('highlight-flash')
              setTimeout(() => el.classList.remove('highlight-flash'), 1500)
            }
          }}
          className="text-sm font-medium text-gray-700 hover:text-blue-600 hover:underline text-left"
        >
          {label}
        </button>
        <span className="text-sm min-w-[5rem] text-right">
          <span className="font-semibold text-blue-600">{effectivePercent}%</span>
          <span className="text-gray-400 text-xs ml-1">({value})</span>
        </span>
      </div>
      <input
        id={`weight-${criterionId}`}
        type="range"
        min="0"
        max="100"
        step="1"
        value={value}
        onChange={handleChange}
        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
      />
    </div>
  )
}
