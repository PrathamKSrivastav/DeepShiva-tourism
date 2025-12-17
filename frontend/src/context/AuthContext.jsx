import { createContext, useState, useEffect, useContext } from 'react'
import { googleLogout } from '@react-oauth/google'
import { verifyToken, loginWithGoogle, getCurrentUser, logout as logoutApi } from '../api'

const AuthContext = createContext(null)

// Use a different key name to avoid blocking
const TOKEN_KEY = 'app_session_token'

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    console.log('🔍 Checking authentication on mount...')
    checkAuth()
  }, [])

  const checkAuth = async () => {
    const token = localStorage.getItem(TOKEN_KEY)
    console.log('🎫 Token found:', !!token)
    
    if (!token) {
      console.log('❌ No token found')
      setLoading(false)
      return
    }

    try {
      console.log('🔐 Verifying token with backend...')
      const response = await verifyToken()
      
      if (response.valid && response.user) {
        console.log('✅ Token valid, user:', response.user.email)
        setUser(response.user)
        setIsAuthenticated(true)
      } else {
        console.warn('⚠️ Token invalid, clearing')
        localStorage.removeItem(TOKEN_KEY)
        setUser(null)
        setIsAuthenticated(false)
      }
    } catch (error) {
      console.error('❌ Auth check error:', error)
      if (error.response?.status === 401) {
        localStorage.removeItem(TOKEN_KEY)
        setUser(null)
        setIsAuthenticated(false)
      }
    } finally {
      setLoading(false)
    }
  }

  const login = async (credential) => {
    try {
      console.log('=== LOGIN START ===')
      const response = await loginWithGoogle(credential)
      console.log('📦 Response received:', response.user.email)
      
      const token = response.access_token
      console.log('🎫 Token length:', token?.length)
      
      if (!token) {
        throw new Error('No token in response')
      }
      
      // Save with new key name
      console.log(`💾 Saving token to localStorage['${TOKEN_KEY}']...`)
      try {
        localStorage.setItem(TOKEN_KEY, token)
        console.log('💾 Save completed')
      } catch (storageError) {
        console.error('❌ Storage error:', storageError)
        throw new Error('localStorage blocked: ' + storageError.message)
      }
      
      // Verify save
      const verify = localStorage.getItem(TOKEN_KEY)
      if (!verify) {
        throw new Error('Token verification failed - not saved')
      }
      if (verify !== token) {
        throw new Error('Token verification failed - mismatch')
      }
      console.log('✅ Token verified in storage')
      
      // Set state
      setUser(response.user)
      setIsAuthenticated(true)
      console.log('✅ User state updated')
      
      // Check persistence
      setTimeout(() => {
        const check = localStorage.getItem(TOKEN_KEY)
        console.log('🔍 Token after 100ms:', check ? 'EXISTS ✅' : 'GONE ❌')
      }, 100)
      
      console.log('=== LOGIN COMPLETE ===')
      return { success: true, user: response.user }
      
    } catch (error) {
      console.error('❌ Login error:', error)
      alert('Login failed: ' + error.message)
      return { 
        success: false, 
        error: error.message || 'Login failed' 
      }
    }
  }

  const logout = async () => {
    try {
      // Clear all auth-related data
      localStorage.removeItem("app_session_token");
      localStorage.removeItem("app_user_data");
      setUser(null);
      setIsAuthenticated(false);

      // Emit custom event for components to listen to
      window.dispatchEvent(new Event("user-logout"));
      await logoutApi();
    } catch (error) {
      console.error('Logout API error:', error)
    } finally {
      localStorage.removeItem(TOKEN_KEY)
      setUser(null)
      setIsAuthenticated(false)
      googleLogout()
      console.log('✅ Logged out')
    }
  }

  const refreshUser = async () => {
    try {
      const userData = await getCurrentUser()
      setUser(userData)
    } catch (error) {
      console.error('Refresh user error:', error)
    }
  }

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    logout,
    refreshUser
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export default AuthContext
