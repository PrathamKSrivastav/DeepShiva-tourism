function PersonaSelector({ personas, selectedPersona, onPersonaChange }) {
  return (
    <div className="space-y-3">
      {personas.map((persona) => (
        <button
          key={persona.id}
          onClick={() => onPersonaChange(persona.id)}
          className={`w-full text-left p-4 rounded-xl transition-all border-2 ${
            selectedPersona === persona.id
              ? 'bg-gradient-to-r from-indigo-100 to-purple-100 border-indigo-400 shadow-lg transform scale-105'
              : 'bg-white border-gray-200 hover:border-indigo-300 hover:shadow-md'
          }`}
        >
          <div className="flex items-start gap-3">
            <span className="text-3xl">{persona.avatar}</span>
            <div className="flex-1">
              <h3 className={`font-semibold text-base ${
                selectedPersona === persona.id ? 'text-indigo-700' : 'text-gray-800'
              }`}>
                {persona.name}
              </h3>
              <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                {persona.description}
              </p>
              <p className="text-[10px] text-gray-500 mt-2 italic">
                Tone: {persona.tone}
              </p>
            </div>
          </div>
          
          {selectedPersona === persona.id && (
            <div className="mt-3 flex items-center justify-center gap-2 text-indigo-600 text-sm font-medium">
              <span>✓ Active</span>
            </div>
          )}
        </button>
      ))}
    </div>
  )
}

export default PersonaSelector
