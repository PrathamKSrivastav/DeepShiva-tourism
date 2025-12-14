function PersonaSelector({ personas, selectedPersona, onSelectPersona }) {
  return (
    <div className="space-y-3">
      {personas.map((persona) => (
        <button
          key={persona.id}
          onClick={() => onSelectPersona(persona.id)}
          className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
            selectedPersona === persona.id
              ? 'border-indigo-600 bg-indigo-50 shadow-md'
              : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
          }`}
        >
          <div className="flex items-start space-x-3">
            <div className="text-2xl">{persona.icon}</div>
            <div className="flex-1">
              <div className="font-semibold text-gray-900">{persona.name}</div>
              <div className="text-xs text-gray-600 mt-1">
                {persona.description}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Tone: {persona.tone}
              </div>
            </div>
            {selectedPersona === persona.id && (
              <div className="text-indigo-600">✓</div>
            )}
          </div>
        </button>
      ))}
    </div>
  )
}

export default PersonaSelector
