interface Example {
  optionA: string
  optionB: string
  intent: string
}

const EXAMPLES: Example[] = [
  {
    optionA: 'Glass bottle',
    optionB: 'Plastic bottle',
    intent: 'I want to minimize environmental impact in my local community',
  },
  {
    optionA: 'Electric car',
    optionB: 'Hybrid car',
    intent: 'I want to reduce my carbon footprint over the next 10 years',
  },
  {
    optionA: 'Buying new laptop',
    optionB: 'Refurbished laptop',
    intent: 'I want to minimize e-waste while getting reliable performance',
  },
]

interface ExamplePromptsProps {
  onSelect: (example: Example) => void
}

export function ExamplePrompts({ onSelect }: ExamplePromptsProps) {
  return (
    <div className="mb-6">
      <p className="text-sm text-gray-500 mb-3">Try an example:</p>
      <div className="flex flex-wrap gap-2">
        {EXAMPLES.map((example, i) => (
          <button
            key={i}
            type="button"
            onClick={() => onSelect(example)}
            className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors"
          >
            {example.optionA} vs {example.optionB}
          </button>
        ))}
      </div>
    </div>
  )
}

export type { Example }
