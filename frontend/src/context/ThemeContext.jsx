import { createContext, useState, useContext, useEffect } from "react";

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  // ✅ Initialize from localStorage, default to false (light mode)
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem("theme_preference");
    return saved === "dark"; // Only true if explicitly set to "dark"
  });

  // ✅ Save preference and apply class
  useEffect(() => {
    const theme = darkMode ? "dark" : "light";
    localStorage.setItem("theme_preference", theme);

    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [darkMode]);

  return (
    <ThemeContext.Provider value={{ darkMode, setDarkMode }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
