import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

function UserDropdown({ darkMode }) {
  const { user, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = async () => {
    await logout();
    setIsOpen(false);
  };

  if (!user) return null;

  return (
    <div className="relative" ref={dropdownRef}>
      {/* User Avatar Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center space-x-2 p-2 rounded-lg transition-colors ${
          darkMode ? "hover:bg-gray-700" : "hover:bg-gray-100"
        }`}
      >
        {user.picture ? (
          <img
            src={user.picture}
            alt={user.name?.charAt(0).toUpperCase()}
            className="w-8 h-8 rounded-full"
          />
        ) : (
          <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold">
            {user.name?.charAt(0).toUpperCase()}
          </div>
        )}
        <span className="text-sm font-medium hidden md:block">{user.name}</span>
        <svg
          className={`w-4 h-4 transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
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
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          className={`absolute right-0 mt-2 w-64 rounded-lg shadow-lg py-2 z-50 border ${
            darkMode
              ? "bg-gray-800 border-gray-700"
              : "bg-white border-gray-200"
          }`}
        >
          {/* User Info */}
          <div className={`px-4 py-3 border-b ${
            darkMode ? "border-dark-border" : "border-gray-200"
          }`}>
            <div className="flex items-center space-x-3">
              {user.picture ? (
                <img
                  src={user.picture}
                  alt={user.name?.charAt(0).toUpperCase()}
                  className="w-10 h-10 rounded-full"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold">
                  {user.name?.charAt(0).toUpperCase()}
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-semibold truncate ${
                  darkMode ? "text-white" : "text-gray-900"
                }`}>
                  {user.name}
                </p>
                <p className={`text-xs truncate ${
                  darkMode ? "text-dark-muted" : "text-gray-500"
                }`}>{user.email}</p>
              </div>
            </div>
            {user.role === "admin" && (
              <div className="mt-2">
                <span className={`inline-flex items-center px-2 py-1 rounded-lg text-xs font-medium ${
                  darkMode
                    ? "bg-gradient-to-r from-accent-indigo/20 to-accent-fuchsia/20 text-accent-indigo border border-accent-indigo/30"
                    : "bg-purple-100 text-purple-800"
                }`}>
                  👑 Admin
                </span>
              </div>
            )}
          </div>

  

            <button
              onClick={handleLogout}
              className={`w-full text-left px-4 py-2 text-sm flex items-center space-x-2 border-t mt-1 transition-colors ${
                darkMode
                  ? "text-red-400 hover:bg-red-900/20 border-dark-border"
                  : "text-red-600 hover:bg-red-50 border-gray-200"
              }`}
            >
              <span>🚪</span>
              <span>Logout</span>
            </button>
          </div>  
      )}
    </div>
  );
}

export default UserDropdown
