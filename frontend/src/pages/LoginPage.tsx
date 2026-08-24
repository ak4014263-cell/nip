import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { authAPI } from '../services/api'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const login = useAuthStore(state => state.login)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      console.log('Attempting login with:', email)
      const response = await authAPI.login(email, password)
      console.log('Login response:', response.data)
      
      const { user, token } = response.data
      
      if (!user) {
        throw new Error('No user in response')
      }
      
      if (!token) {
        throw new Error('No token in response')
      }
      
      console.log('User data received:', user)
      console.log('User role:', user.role)
      
      // Update store first
      login(user, token)
      console.log('Store updated with user and token')
      
      // Small delay to ensure state is persisted to localStorage
      await new Promise(resolve => setTimeout(resolve, 200))
      
      toast.success('Login successful!')
      
      // Redirect based on role
      const redirectPath = user.role === 'CANDIDATE' ? '/candidate/dashboard' : '/recruiter/dashboard'
      console.log('Redirecting to:', redirectPath)
      
      // Use window.location for more reliable redirect
      window.location.href = redirectPath
      
    } catch (error: any) {
      console.error('Login error:', error)
      const errorMsg = error.response?.data?.message || error.response?.data?.detail || error.message || 'Login failed'
      console.error('Error message:', errorMsg)
      toast.error(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
        <h1 className="text-3xl font-bold text-gray-900 mb-2 text-center">
          Welcome Back
        </h1>
        <p className="text-gray-600 mb-8 text-center">
          Sign in to continue to Swiply
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="mt-6 text-center text-gray-600">
          Don't have an account?{' '}
          <Link to="/register" className="text-blue-600 hover:text-blue-700 font-semibold">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  )
}
