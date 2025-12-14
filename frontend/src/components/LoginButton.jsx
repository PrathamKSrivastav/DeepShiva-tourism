import { GoogleLogin } from '@react-oauth/google'
import { useAuth } from '../context/AuthContext'

function LoginButton({ onSuccess }) {
  const { login } = useAuth()

  const handleSuccess = async (credentialResponse) => {
    console.log('🎫 Google credential received')
    const result = await login(credentialResponse.credential)
    
    if (result.success) {
      console.log('✅ Login complete:', result.user.email)
      
      // Check token with CORRECT key name
      setTimeout(() => {
        const token = localStorage.getItem('app_session_token') // CHANGED KEY NAME
        console.log('🔍 Token check after login:', token ? 'EXISTS ✅' : 'MISSING ❌')
        if (!token) {
          alert('Token save failed! Check browser settings.')
        } else {
          console.log('🎉 Token successfully saved and persisting!')
        }
      }, 500)
      
      if (onSuccess) {
        onSuccess(result.user)
      }
    } else {
      console.error('❌ Login result failed:', result.error)
      alert(`Login failed: ${result.error}`)
    }
  }

  const handleError = () => {
    console.error('❌ Google Login Failed')
    alert('Google Login failed. Please try again.')
  }

  return (
    <div className="flex items-center justify-center">
      <GoogleLogin
        onSuccess={handleSuccess}
        onError={handleError}
        useOneTap={false}
        theme="filled_blue"
        size="large"
        text="signin_with"
        shape="rectangular"
        auto_select={false}
      />
    </div>
  )
}

export default LoginButton
