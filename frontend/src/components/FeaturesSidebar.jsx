import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import MeditationSelector from "./MeditationSelector";
import YogaSelector from "./YogaSelector";
import { useHolidays } from "../hooks/useHolidays";

function FeaturesSidebar({ darkMode, isOpen, onToggle }) {
  const [isMobile, setIsMobile] = useState(false);
  const [activeFeature, setActiveFeature] = useState(null);
  const [showMeditationModal, setShowMeditationModal] = useState(false);
  const [showYogaModal, setShowYogaModal] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024);
    };
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  const features = [
    {
      id: "meditation",
      name: "Meditation",
      icon: "🧘",
      description: "Guided meditation courses for spiritual journeys",
      color: "from-purple-500 to-indigo-600",
    },
    {
      id: "yoga",
      name: "Yoga Practice",
      icon: "🤸",
      description: "AI-powered yoga pose detection and correction",
      color: "from-emerald-500 to-teal-600",
    },
    {
      id: "weather",
      name: "Weather",
      icon: "🌤️",
      description: "Real-time weather updates for your location",
      color: "from-blue-500 to-cyan-600",
    },
    {
      id: "holidays",
      name: "Holidays",
      icon: "🎉",
      description: "Upcoming Indian holidays and festivals",
      color: "from-orange-500 to-red-600",
    },
    {
      id: "tips",
      name: "Travel Tips",
      icon: "💡",
      description: "Essential tips for your journey",
      color: "from-emerald-500 to-teal-600",
    },
  ];

  const handleFeatureClick = (feature) => {
    if (feature.id === "meditation") {
      setShowMeditationModal(true);
      setActiveFeature(null); // Close any expanded feature
      onToggle?.(false);
    } else if (feature.id === "yoga") {
      setShowYogaModal(true);
      setActiveFeature(null); // Close any expanded feature
      onToggle?.(false);
    } else {
      setActiveFeature(activeFeature?.id === feature.id ? null : feature);
    }
  };

  const SidebarContent = () => (
    <div
      className={`h-full flex flex-col ${
        darkMode
          ? "bg-dark-surface border-l border-dark-border"
          : "bg-white/40 backdrop-blur-xl border-white/20"
      }`}
    >
      {/* Header */}
      <div
        className={`p-5 flex items-center justify-between border-b ${
          darkMode ? "border-dark-border" : "border-white/20"
        }`}
      >
        <h2
          className={`font-semibold tracking-tight ${
            darkMode ? "text-slate-100" : "text-gray-800"
          }`}
        >
          Features
        </h2>
        {isMobile && (
          <button
            onClick={() => onToggle?.(false)}
            className={`w-8 h-8 rounded-full flex items-center justify-center ${
              darkMode
                ? "bg-dark-elev hover:bg-dark-elev/80 text-white"
                : "bg-gray-100 hover:bg-gray-200 text-gray-700"
            }`}
          >
            ✕
          </button>
        )}
      </div>

      {/* Features List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {features.map((feature) => (
          <motion.div
            key={feature.id}
            whileHover={{ scale: 1.02 }}
            className="overflow-hidden"
          >
            <button
              onClick={() => handleFeatureClick(feature)}
              className={`w-full text-left p-4 rounded-xl transition-all ${
                activeFeature?.id === feature.id ||
                (feature.id === "meditation" && showMeditationModal) ||
                (feature.id === "yoga" && showYogaModal)
                  ? `bg-gradient-to-r ${feature.color} text-white shadow-lg`
                  : darkMode
                  ? "bg-dark-elev hover:bg-dark-elev/80 text-slate-200"
                  : "bg-white/60 hover:bg-white text-gray-800"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{feature.icon}</span>
                  <div>
                    <h3 className="font-semibold text-sm">{feature.name}</h3>
                    <p
                      className={`text-xs mt-0.5 ${
                        activeFeature?.id === feature.id ||
                        (feature.id === "meditation" && showMeditationModal) ||
                        (feature.id === "yoga" && showYogaModal)
                          ? "text-white/80"
                          : darkMode
                          ? "text-slate-400"
                          : "text-gray-600"
                      }`}
                    >
                      {feature.description}
                    </p>
                  </div>
                </div>
                {feature.id !== "meditation" && feature.id !== "yoga" && (
                  <svg
                    className={`w-5 h-5 transition-transform ${
                      activeFeature?.id === feature.id ? "rotate-180" : ""
                    } ${darkMode ? "text-slate-400" : "text-gray-500"}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                )}
              </div>
            </button>

            {/* Expanded Content */}
            <AnimatePresence>
              {activeFeature?.id === feature.id && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div
                    className={`mt-2 p-4 rounded-xl ${
                      darkMode
                        ? "bg-dark-elev/50 border border-dark-border"
                        : "bg-white/60 border border-white/60"
                    }`}
                  >
                    {feature.id === "weather" && (
                      <WeatherContent darkMode={darkMode} />
                    )}
                    {feature.id === "holidays" && (
                      <HolidaysContent darkMode={darkMode} />
                    )}
                    {feature.id === "tips" && (
                      <TipsContent darkMode={darkMode} />
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
    </div>
  );

  // Desktop view
  if (!isMobile) {
    return (
      <>
        <aside className="w-80 h-full flex-shrink-0 relative z-10">
          <SidebarContent />
        </aside>

        {showMeditationModal && (
          <MeditationSelector
            darkMode={darkMode}
            onClose={() => setShowMeditationModal(false)}
          />
        )}
        {showYogaModal && (
          <YogaSelector
            darkMode={darkMode}
            onClose={() => setShowYogaModal(false)}
          />
        )}
      </>
    );
  }

  // Mobile view
  return (
    <>
      {isOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            onClick={() => onToggle?.(false)}
          />
          <aside className="fixed right-0 top-0 bottom-0 w-80 z-50">
            <SidebarContent />
          </aside>
        </>
      )}

      {showMeditationModal && (
        <MeditationSelector
          darkMode={darkMode}
          onClose={() => setShowMeditationModal(false)}
        />
      )}
      {showYogaModal && (
        <YogaSelector
          darkMode={darkMode}
          onClose={() => setShowYogaModal(false)}
        />
      )}
    </>
  );
}

// ==================== WEATHER CONTENT COMPONENT ====================
function WeatherContent({ darkMode }) {
  const [weatherData, setWeatherData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [locationPermission, setLocationPermission] = useState("prompt"); // "prompt" | "granted" | "denied"

  useEffect(() => {
    checkLocationPermission();
  }, []);

  const checkLocationPermission = async () => {
    if (!navigator.permissions) {
      // Fallback for browsers that don't support permissions API
      requestLocation();
      return;
    }

    try {
      const result = await navigator.permissions.query({ name: "geolocation" });
      setLocationPermission(result.state);

      if (result.state === "granted") {
        fetchWeatherData();
      }

      // Listen for permission changes
      result.onchange = () => {
        setLocationPermission(result.state);
        if (result.state === "granted") {
          fetchWeatherData();
        }
      };
    } catch (err) {
      console.error("Permission API error:", err);
      requestLocation();
    }
  };

  const requestLocation = () => {
    setLoading(true);
    setError(null);

    if (!navigator.geolocation) {
      setError("Geolocation is not supported by your browser");
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocationPermission("granted"); // ✅ Update permission state
        fetchWeatherData(position.coords.latitude, position.coords.longitude);
      },
      (err) => {
        console.error("Geolocation error:", err);
        setLocationPermission("denied"); // ✅ Update permission state
        if (err.code === 1) {
          setError(
            "Location access denied. Please enable location in your browser settings."
          );
        } else if (err.code === 2) {
          setError("Location unavailable. Please check your device settings.");
        } else {
          setError("Unable to retrieve your location. Please try again.");
        }
        setLoading(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000, // Cache for 5 minutes
      }
    );
  };

  const fetchWeatherData = async (lat, lon) => {
    if (!lat || !lon) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          fetchWeatherData(position.coords.latitude, position.coords.longitude);
        },
        (err) => {
          setError("Could not get your location");
          setLoading(false);
        }
      );
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&hourly=temperature_2m,precipitation_probability,precipitation,rain,showers,snowfall,relative_humidity_2m,visibility,wind_speed_80m,wind_direction_80m,uv_index,is_day&current=temperature_2m,relative_humidity_2m,snowfall,showers,rain,precipitation,cloud_cover,pressure_msl,surface_pressure,weather_code,wind_speed_10m,wind_gusts_10m,wind_direction_10m&timeformat=unixtime&timezone=auto`;

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Weather API error: ${response.status}`);
      }

      const data = await response.json();
      setWeatherData(data);
      console.log("✅ Weather data fetched:", data);
    } catch (err) {
      console.error("❌ Weather fetch error:", err);
      setError("Unable to fetch weather data. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  const getWeatherDescription = (code) => {
    const weatherCodes = {
      0: "Clear sky ☀️",
      1: "Mainly clear 🌤️",
      2: "Partly cloudy ⛅",
      3: "Overcast ☁️",
      45: "Foggy 🌫️",
      48: "Foggy 🌫️",
      51: "Light drizzle 🌦️",
      53: "Drizzle 🌦️",
      55: "Heavy drizzle 🌧️",
      61: "Light rain 🌧️",
      63: "Rain 🌧️",
      65: "Heavy rain ⛈️",
      71: "Light snow 🌨️",
      73: "Snow ❄️",
      75: "Heavy snow ❄️",
      77: "Snow grains ❄️",
      80: "Rain showers 🌧️",
      81: "Rain showers 🌧️",
      82: "Heavy rain showers ⛈️",
      85: "Snow showers 🌨️",
      86: "Heavy snow showers 🌨️",
      95: "Thunderstorm ⛈️",
      96: "Thunderstorm with hail ⛈️",
      99: "Thunderstorm with hail ⛈️",
    };
    return weatherCodes[code] || "Unknown";
  };

  const getWindDirection = (degrees) => {
    const directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
    const index = Math.round(degrees / 45) % 8;
    return directions[index];
  };

  // Permission prompt UI
  if (locationPermission === "prompt" || locationPermission === "denied") {
    return (
      <div className="text-center py-6">
        <div className="text-5xl mb-3">📍</div>
        <h3
          className={`text-sm font-semibold mb-2 ${
            darkMode ? "text-slate-100" : "text-gray-800"
          }`}
        >
          Location Access Required
        </h3>
        <p
          className={`text-xs mb-4 ${
            darkMode ? "text-dark-muted" : "text-gray-600"
          }`}
        >
          We need your location to show accurate weather data
        </p>
        <button
          onClick={requestLocation}
          disabled={loading}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            darkMode
              ? "bg-emerald-600 hover:bg-emerald-700 text-white"
              : "bg-emerald-500 hover:bg-emerald-600 text-white"
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {loading ? "Getting location..." : "Enable Location"}
        </button>
        {error && <p className="text-xs text-red-500 mt-3">{error}</p>}
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="text-center py-6">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500 mx-auto mb-3" />
        <p
          className={`text-sm ${
            darkMode ? "text-dark-muted" : "text-gray-600"
          }`}
        >
          Fetching weather data...
        </p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="text-center py-6">
        <div className="text-4xl mb-3">⚠️</div>
        <p className="text-sm text-red-500 mb-3">{error}</p>
        <button
          onClick={requestLocation}
          className={`px-4 py-2 rounded-lg text-sm font-medium ${
            darkMode
              ? "bg-dark-elev hover:bg-dark-elev/80 text-white"
              : "bg-gray-100 hover:bg-gray-200 text-gray-700"
          }`}
        >
          Try Again
        </button>
      </div>
    );
  }

  // Weather data display
  if (!weatherData) {
    return null;
  }

  const current = weatherData.current;

  return (
    <div className="space-y-4">
      {/* Current Weather Card */}
      <div
        className={`p-4 rounded-xl ${
          darkMode
            ? "bg-gradient-to-br from-blue-900/30 to-purple-900/30 border border-blue-800/30"
            : "bg-gradient-to-br from-blue-50 to-purple-50 border border-blue-200/50"
        }`}
      >
        <div className="flex items-center justify-between mb-3">
          <div>
            <p
              className={`text-xs uppercase tracking-wide mb-1 ${
                darkMode ? "text-blue-400" : "text-blue-600"
              }`}
            >
              Current Weather
            </p>
            <p
              className={`text-3xl font-bold ${
                darkMode ? "text-white" : "text-gray-900"
              }`}
            >
              {Math.round(current.temperature_2m)}°C
            </p>
          </div>
          <div className="text-5xl">
            {getWeatherDescription(current.weather_code).split(" ")[1]}
          </div>
        </div>
        <p
          className={`text-sm font-medium mb-3 ${
            darkMode ? "text-slate-200" : "text-gray-700"
          }`}
        >
          {getWeatherDescription(current.weather_code)
            .split(" ")
            .slice(0, -1)
            .join(" ")}
        </p>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-2 gap-2">
          <div
            className={`p-2 rounded-lg ${
              darkMode ? "bg-dark-surface/50" : "bg-white/60"
            }`}
          >
            <p
              className={`text-xs ${
                darkMode ? "text-dark-muted" : "text-gray-600"
              }`}
            >
              Humidity
            </p>
            <p
              className={`text-sm font-semibold ${
                darkMode ? "text-white" : "text-gray-900"
              }`}
            >
              {current.relative_humidity_2m}%
            </p>
          </div>
          <div
            className={`p-2 rounded-lg ${
              darkMode ? "bg-dark-surface/50" : "bg-white/60"
            }`}
          >
            <p
              className={`text-xs ${
                darkMode ? "text-dark-muted" : "text-gray-600"
              }`}
            >
              Wind
            </p>
            <p
              className={`text-sm font-semibold ${
                darkMode ? "text-white" : "text-gray-900"
              }`}
            >
              {Math.round(current.wind_speed_10m)} km/h{" "}
              {getWindDirection(current.wind_direction_10m)}
            </p>
          </div>
          <div
            className={`p-2 rounded-lg ${
              darkMode ? "bg-dark-surface/50" : "bg-white/60"
            }`}
          >
            <p
              className={`text-xs ${
                darkMode ? "text-dark-muted" : "text-gray-600"
              }`}
            >
              Pressure
            </p>
            <p
              className={`text-sm font-semibold ${
                darkMode ? "text-white" : "text-gray-900"
              }`}
            >
              {Math.round(current.pressure_msl)} hPa
            </p>
          </div>
          <div
            className={`p-2 rounded-lg ${
              darkMode ? "bg-dark-surface/50" : "bg-white/60"
            }`}
          >
            <p
              className={`text-xs ${
                darkMode ? "text-dark-muted" : "text-gray-600"
              }`}
            >
              Cloud Cover
            </p>
            <p
              className={`text-sm font-semibold ${
                darkMode ? "text-white" : "text-gray-900"
              }`}
            >
              {current.cloud_cover}%
            </p>
          </div>
        </div>
      </div>

      {/* Refresh Button */}
      <button
        onClick={requestLocation}
        disabled={loading}
        className={`w-full px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
          darkMode
            ? "bg-dark-elev hover:bg-dark-elev/80 text-slate-200"
            : "bg-white/80 hover:bg-white text-gray-700"
        } disabled:opacity-50 disabled:cursor-not-allowed`}
      >
        🔄 Refresh Weather
      </button>
    </div>
  );
}

// Festivals Content Component
function FestivalsContent({ darkMode }) {
  const festivals = [
    { name: "Kumbh Mela", date: "April 2025" },
    { name: "Char Dham Yatra", date: "May-Nov 2025" },
    { name: "Ganga Dussehra", date: "June 2025" },
  ];

  return (
    <div className="space-y-2">
      {festivals.map((fest) => (
        <div
          key={fest.name}
          className={`p-3 rounded-lg ${
            darkMode ? "bg-dark-surface" : "bg-white/60"
          }`}
        >
          <p
            className={`text-sm font-medium ${
              darkMode ? "text-slate-100" : "text-gray-800"
            }`}
          >
            {fest.name}
          </p>
          <p
            className={`text-xs ${
              darkMode ? "text-dark-muted" : "text-gray-500"
            }`}
          >
            {fest.date}
          </p>
        </div>
      ))}
    </div>
  );
}

// Tips Content Component
function TipsContent({ darkMode }) {
  const tips = [
    "Dress modestly at religious sites",
    "Remove shoes before entering temples",
    "Carry enough water and snacks",
    "Book accommodations in advance",
  ];

  return (
    <ul className="space-y-2">
      {tips.map((tip, idx) => (
        <li
          key={idx}
          className={`text-sm ${darkMode ? "text-slate-200" : "text-gray-700"}`}
        >
          • {tip}
        </li>
      ))}
    </ul>
  );
}

function HolidaysContent({ darkMode }) {
  const { holidays, isLoading, error, fetchUpcomingHolidays } = useHolidays();

  useEffect(() => {
    fetchUpcomingHolidays(3);
  }, [fetchUpcomingHolidays]);

  if (isLoading) {
    return (
      <div className="text-center py-6">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto mb-3" />
        <p
          className={`text-sm ${
            darkMode ? "text-dark-muted" : "text-gray-600"
          }`}
        >
          Loading holidays...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-6">
        <div className="text-4xl mb-3">⚠️</div>
        <p className="text-sm text-red-500 mb-3">{error}</p>
        <button
          onClick={() => fetchUpcomingHolidays(3)}
          className={`px-4 py-2 rounded-lg text-sm font-medium ${
            darkMode
              ? "bg-dark-elev hover:bg-dark-elev/80 text-white"
              : "bg-gray-100 hover:bg-gray-200 text-gray-700"
          }`}
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!holidays || holidays.length === 0) {
    return (
      <div className="text-center py-6">
        <div className="text-4xl mb-3">📅</div>
        <p
          className={`text-sm ${
            darkMode ? "text-dark-muted" : "text-gray-600"
          }`}
        >
          No upcoming holidays found
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {holidays.map((holiday, idx) => (
        <div
          key={idx}
          className={`p-3 rounded-lg ${
            darkMode
              ? "bg-gradient-to-br from-orange-900/20 to-red-900/20 border border-orange-800/30"
              : "bg-gradient-to-br from-orange-50 to-red-50 border border-orange-200/50"
          }`}
        >
          <div className="flex items-start justify-between mb-2">
            <h4
              className={`text-sm font-semibold ${
                darkMode ? "text-orange-300" : "text-orange-700"
              }`}
            >
              {holiday.name}
            </h4>
            {holiday.days_until !== undefined && (
              <span
                className={`text-xs px-2 py-1 rounded-full ${
                  darkMode
                    ? "bg-orange-800/50 text-orange-200"
                    : "bg-orange-200 text-orange-800"
                }`}
              >
                {holiday.days_until === 0
                  ? "Today"
                  : holiday.days_until === 1
                  ? "Tomorrow"
                  : `${holiday.days_until} days`}
              </span>
            )}
          </div>

          <div className="space-y-1">
            <p
              className={`text-xs ${
                darkMode ? "text-slate-300" : "text-gray-700"
              }`}
            >
              📅 {holiday.day_of_week},{" "}
              {new Date(holiday.date).toLocaleDateString("en-IN", {
                day: "numeric",
                month: "long",
                year: "numeric",
              })}
            </p>

            <p
              className={`text-xs ${
                darkMode ? "text-dark-muted" : "text-gray-600"
              }`}
            >
              {holiday.type}
            </p>

            {holiday.description && (
              <p
                className={`text-xs mt-2 ${
                  darkMode ? "text-slate-400" : "text-gray-600"
                }`}
              >
                {holiday.description}
              </p>
            )}
          </div>
        </div>
      ))}

      <button
        onClick={() => fetchUpcomingHolidays(3)}
        className={`w-full px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
          darkMode
            ? "bg-dark-elev hover:bg-dark-elev/80 text-slate-200"
            : "bg-white/80 hover:bg-white text-gray-700"
        }`}
      >
        🔄 Refresh Holidays
      </button>
    </div>
  );
}


export default FeaturesSidebar;
