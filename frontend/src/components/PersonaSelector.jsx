import React from "react";

function PersonaSelector({
  personas,
  selectedPersona,
  onSelectPersona,
  darkMode,
}) {
  return (
    <div
      className={`flex flex-col space-y-3 h-full overflow-y-auto no-scrollbar p-1 ${
        darkMode ? "text-slate-100" : "text-gray-800"
      }`}
    >
      {personas.map((persona) => {
        const isSelected = selectedPersona === persona.id;

        return (
          <button
            key={persona.id}
            onClick={() => onSelectPersona(persona.id)}
            className={`group relative w-full text-left p-4 rounded-2xl transition-all duration-300 ease-[cubic-bezier(0.25,0.1,0.25,1)]
              ${
                isSelected
                  ? darkMode
                    ? "bg-dark-elev shadow-[0_8px_24px_rgba(99,102,241,0.06)] ring-1 ring-accent-indigo/30 scale-[1.02]"
                    : "bg-white/90 shadow-lg ring-1 ring-fuchsia-200 scale-[1.02]"
                  : darkMode
                  ? "bg-dark-surface hover:bg-dark-elev/70 border border-dark-border"
                  : "bg-white/30 hover:bg-white/50 border border-white/20"
              } backdrop-blur-md`}
          >
            {/* Active Indicator Strip */}
            {isSelected && (
              <div
                className={`absolute left-0 top-3 bottom-3 w-1 rounded-r-full bg-gradient-to-b from-accent-indigo to-accent-fuchsia`}
              />
            )}

            <div className="flex items-start gap-3">
              <div
                className={`flex-shrink-0 text-2xl p-2 rounded-xl transition-colors ${
                  isSelected
                    ? "bg-gradient-to-tr from-accent-indigo/20 to-accent-fuchsia/10"
                    : "bg-transparent group-hover:bg-dark-elev/60"
                }`}
              >
                {persona.icon}
              </div>

              <div className="flex-1 min-w-0 pt-1">
                <div
                  className={`font-semibold text-sm truncate ${
                    isSelected
                      ? darkMode
                        ? "text-white"
                        : "text-fuchsia-900"
                      : darkMode
                      ? "text-slate-100"
                      : "text-gray-800"
                  }`}
                >
                  {persona.name}
                </div>
                <div
                  className={`text-xs mt-0.5 line-clamp-2 leading-relaxed ${
                    darkMode ? "text-dark-muted" : "text-gray-500"
                  }`}
                >
                  {persona.description}
                </div>

                {/* Tone Tag */}
                <div className="mt-2 flex">
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full border ${
                      isSelected
                        ? darkMode
                          ? "bg-dark-elev text-accent-indigo border-accent-indigo/30"
                          : "bg-fuchsia-100/60 text-fuchsia-700 border-fuchsia-200"
                        : darkMode
                        ? "bg-dark-surface text-dark-muted border-dark-border"
                        : "bg-gray-100 text-gray-600 border-gray-200"
                    }`}
                  >
                    {persona.tone}
                  </span>
                </div>
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}

export default PersonaSelector;
