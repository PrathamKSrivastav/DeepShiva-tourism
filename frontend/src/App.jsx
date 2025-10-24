import { useState, useEffect } from 'react'
import ChatWindow from './components/ChatWindow'
import PersonaSelector from './components/PersonaSelector'
import { fetchPersonas } from './api'

function App() {
  const [personas, setPersonas] = useState([])
  const [selectedPersona, setSelectedPersona] = useState('local_guide')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadPersonas()
  }, [])

  const loadPersonas = async () => {
    try {
      const data = await fetchPersonas()
      setPersonas(data.personas)
      setLoading(false)
    } catch (error) {
      console.error('Error loading personas:', error)
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <header className="text-center mb-8">
          <h1 className="text-5xl font-heading font-bold text-white mb-3 drop-shadow-lg">
            🏔️ Deep Shiva
          </h1>
          <p className="text-xl text-white/90 font-medium">
            Your AI Companion for Exploring Uttarakhand - Dev Bhoomi
          </p>
          <p className="text-sm text-white/75 mt-2">
            Choose your guide and embark on a journey through the Land of Gods
          </p>
        </header>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Persona Selector - Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white/95 backdrop-blur-sm rounded-2xl shadow-2xl p-6 sticky top-8">
              <h2 className="text-2xl font-heading font-semibold text-gray-800 mb-4">
                Choose Your Guide
              </h2>
              {loading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                  <p className="text-gray-600 mt-3">Loading personas...</p>
                </div>
              ) : (
                <PersonaSelector
                  personas={personas}
                  selectedPersona={selectedPersona}
                  onPersonaChange={setSelectedPersona}
                />
              )}
              
              {/* Info Box */}
              <div className="mt-6 p-4 bg-gradient-to-r from-saffron/20 to-mountain-green/20 rounded-xl border border-saffron/30">
                <p className="text-xs text-gray-700 leading-relaxed">
                  <strong>💡 Tip:</strong> Each guide offers a unique perspective. 
                  Switch personas to get different insights about the same topic!
                </p>
              </div>
            </div>
          </div>

          {/* Chat Window - Main Area */}
          <div className="lg:col-span-3">
            <ChatWindow
              selectedPersona={selectedPersona}
              personaInfo={personas.find(p => p.id === selectedPersona)}
            />
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-8 text-center text-white/70 text-sm">
          <p>
            Built with ❤️ for travelers & pilgrims exploring Uttarakhand
          </p>
          <p className="mt-1">
            🙏 Har Har Gange | Om Namah Shivaya 🕉️
          </p>
        </footer>
      </div>
    </div>
  )
}

export default App
