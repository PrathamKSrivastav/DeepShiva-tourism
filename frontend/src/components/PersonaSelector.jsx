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
        darkMode ? "text-white" : "text-gray-800"
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
                    ? "bg-gray-700 shadow-lg shadow-indigo-500/20 ring-1 ring-indigo-400/50"
                    : "bg-white/80 shadow-lg shadow-fuchsia-500/10 ring-1 ring-fuchsia-500/30 scale-[1.02]"
                  : darkMode
                  ? "bg-gray-800 hover:bg-gray-700 hover:shadow-sm border border-gray-600"
                  : "bg-white/30 hover:bg-white/50 hover:shadow-sm border border-white/20"
              } backdrop-blur-md`}
          >
            {/* Active Indicator Strip */}
            {isSelected && (
              <div
                className={`absolute left-0 top-3 bottom-3 w-1 ${
                  darkMode
                    ? "bg-gradient-to-b from-indigo-400 to-indigo-600"
                    : "bg-gradient-to-b from-fuchsia-400 to-purple-500"
                } rounded-r-full`}
              />
            )}

            <div className="flex items-start gap-3">
              <div
                className={`flex-shrink-0 text-2xl p-2 rounded-xl transition-colors ${
                  isSelected
                    ? darkMode
                      ? "bg-indigo-900/50"
                      : "bg-fuchsia-50"
                    : darkMode
                    ? "bg-transparent group-hover:bg-gray-700"
                    : "bg-transparent group-hover:bg-white/40"
                }`}
              >
                {persona.icon}
              </div>

              <div className="flex-1 min-w-0 pt-1">
                <div
                  className={`font-semibold text-sm truncate transition-colors ${
                    isSelected
                      ? darkMode
                        ? "text-white"
                        : "text-fuchsia-900"
                      : darkMode
                      ? "text-gray-200"
                      : "text-gray-800"
                  }`}
                >
                  {persona.name}
                </div>
                <div
                  className={`text-xs mt-0.5 line-clamp-2 leading-relaxed ${
                    darkMode ? "text-gray-400" : "text-gray-500"
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
                          ? "bg-indigo-900/50 text-indigo-200 border-indigo-500"
                          : "bg-fuchsia-100/50 text-fuchsia-700 border-fuchsia-200"
                        : darkMode
                        ? "bg-gray-700 text-gray-400 border-gray-600"
                        : "bg-gray-100/50 text-gray-500 border-gray-200"
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
