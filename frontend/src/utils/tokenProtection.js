// Protect localStorage from being cleared
let protectedToken = null

export const saveProtectedToken = (token) => {
  localStorage.setItem('auth_token', token)
  protectedToken = token
  console.log('🛡️ Token protected')
}

export const getProtectedToken = () => {
  let token = localStorage.getItem('auth_token')
  
  // If localStorage was cleared but we have backup
  if (!token && protectedToken) {
    console.log('🔄 Restoring token from memory')
    localStorage.setItem('auth_token', protectedToken)
    token = protectedToken
  }
  
  return token
}

export const clearProtectedToken = () => {
  localStorage.removeItem('auth_token')
  protectedToken = null
  console.log('🗑️ Token cleared')
}

// Watch for storage changes
window.addEventListener('storage', (e) => {
  if (e.key === 'auth_token' && !e.newValue && protectedToken) {
    console.log('⚠️ Token deletion detected, restoring...')
    localStorage.setItem('auth_token', protectedToken)
  }
})
