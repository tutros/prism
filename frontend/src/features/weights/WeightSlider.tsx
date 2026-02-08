interface WeightSliderProps {
  criterionId: string
  label: string
  value: number
  onChange: (criterionId: string, value: number) => void
}

export function WeightSlider({
  criterionId,
  label,
  value,
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
            document.getElementById(`criterion-${criterionId}`)?.scrollIntoView({ behavior: 'smooth' })
          }}
          className="text-sm font-medium text-gray-700 hover:text-blue-600 hover:underline text-left"
        >
          {label}
        </button>
        <span className="text-sm font-semibold text-blue-600 min-w-[3rem] text-right">
          {value}%
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
