import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { User, Mail, Lock, Phone, MapPin, Briefcase, Code, Upload, CheckCircle } from 'lucide-react'
import { authAPI } from '../services/api'
import { syncWTTJRegistration, WTTJSyncWebSocket } from '../services/wttjSync'

export default function RegisterPage() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    first_name: '',
    last_name: '',
    phone: '',
    location: '',
    experience_years: '',
    skills: '',
    bio: '',
    linkedin_url: '',
    work_preference: '',
    career_interests: '',
    salary_expectations: '',
    availability: ''
  })
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [automationStatus, setAutomationStatus] = useState<any>(null)
  const [wttjSyncStatus, setWttjSyncStatus] = useState<string>('')
  const [wttjSyncProgress, setWttjSyncProgress] = useState<number>(0)

  // WebSocket for real-time WTTJ sync updates
  useEffect(() => {
    const wsSync = new WTTJSyncWebSocket()
    wsSync.connect()
    
    wsSync.onUpdate((status) => {
      setWttjSyncStatus(status.status)
      setWttjSyncProgress(status.progress || 0)
      
      if (status.status === 'ready') {
        console.log('✅ WTTJ form is ready to submit!')
      }
    })
    
    return () => {
      wsSync.disconnect()
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const formPayload = new FormData()
      formPayload.append('email', formData.email)
      formPayload.append('password', formData.password)
      formPayload.append('name', formData.name)
      formPayload.append('first_name', formData.first_name)
      formPayload.append('last_name', formData.last_name)
      formPayload.append('phone', formData.phone)
      formPayload.append('location', formData.location)
      formPayload.append('experience_years', formData.experience_years)
      formPayload.append('skills', formData.skills)
      formPayload.append('bio', formData.bio)
      formPayload.append('linkedin_url', formData.linkedin_url)
      formPayload.append('work_preference', formData.work_preference)
      formPayload.append('career_interests', formData.career_interests)
      formPayload.append('salary_expectations', formData.salary_expectations)
      formPayload.append('availability', formData.availability)
      
      if (resumeFile) {
        formPayload.append('resume', resumeFile)
      }

      console.log('Submitting registration...', formData.email)
      const response = await authAPI.register(formPayload)
      console.log('Registration response:', response)
      
      // ✨ NEW: Start WTTJ form filling in background
      console.log('🔄 Starting WTTJ form sync in background...')
      syncWTTJRegistration({
        email: formData.email,
        password: formData.password,
        firstName: formData.first_name || formData.name.split(' ')[0],
        lastName: formData.last_name || formData.name.split(' ')[1] || '',
        role: 'candidate'
      }).then((syncResult) => {
        if (syncResult.success) {
          console.log('✅ WTTJ form filling started successfully')
        } else {
          console.warn('⚠️ WTTJ sync failed:', syncResult.error)
        }
      })
      
      if (response.data.success) {
        setAutomationStatus({
          success: true,
          aiProfile: response.data.ai_enhanced_profile,
          automationSites: response.data.automation_sites
        })
        
        // Redirect after showing automation status
        setTimeout(() => {
          navigate('/login')
        }, 5000)
      }
    } catch (error: any) {
      console.error('Registration failed:', error)
      console.error('Error response:', error.response?.data)
      console.error('Error status:', error.response?.status)
      console.error('Error message:', error.message)
      setAutomationStatus({
        success: false,
        error: error.response?.data?.detail || error.message || 'Registration failed'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }
  
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setResumeFile(e.target.files[0])
    }
  }

  if (automationStatus) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-400 via-purple-500 to-indigo-600 flex items-center justify-center p-6">
        <div className="glass-panel max-w-2xl w-full p-8 text-center">
          {automationStatus.success ? (
            <div className="animate-fade-in">
              <div className="text-6xl mb-4">🚀</div>
              <h2 className="text-3xl font-bold mb-4 text-gray-900">Account Created Successfully!</h2>
              <p className="text-gray-600 mb-6">
                Your account has been created and automatic career site automation has been initiated.
              </p>
              
              {automationStatus.aiProfile && (
                <div className="bg-white/50 rounded-xl p-6 mb-6 text-left">
                  <h3 className="text-xl font-bold mb-4 text-gray-900">🤖 AI-Enhanced Profile</h3>
                  <div className="space-y-3">
                    <div>
                      <strong className="text-indigo-600">Headline:</strong>
                      <p className="text-gray-700">{automationStatus.aiProfile.headline}</p>
                    </div>
                    <div>
                      <strong className="text-indigo-600">Bio:</strong>
                      <p className="text-gray-700">{automationStatus.aiProfile.bio}</p>
                    </div>
                    {automationStatus.aiProfile.suggested_skills?.length > 0 && (
                      <div>
                        <strong className="text-indigo-600">Suggested Skills:</strong>
                        <p className="text-gray-700">{automationStatus.aiProfile.suggested_skills.join(', ')}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              <div className="bg-green-50 rounded-xl p-4 mb-6">
                <h3 className="text-lg font-bold text-green-800 mb-2">🎯 Automation Started</h3>
                <p className="text-green-700 text-sm">
                  Accounts are being automatically created on: {automationStatus.automationSites?.join(', ')}
                </p>
                <p className="text-green-600 text-xs mt-2">
                  Check your credentials manager in a few minutes to see the generated accounts.
                </p>
              </div>
              
              {/* WTTJ Sync Status */}
              {wttjSyncStatus && (
                <div className={`rounded-xl p-4 mb-6 ${
                  wttjSyncStatus === 'ready' ? 'bg-blue-50' : 
                  wttjSyncStatus === 'error' ? 'bg-red-50' : 
                  'bg-yellow-50'
                }`}>
                  <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                    {wttjSyncStatus === 'ready' && <CheckCircle className="text-blue-600" />}
                    🌐 WTTJ Form Status
                  </h3>
                  
                  {wttjSyncStatus === 'started' && (
                    <div>
                      <p className="text-yellow-700 text-sm mb-2">
                        Filling WTTJ form in background...
                      </p>
                      <div className="w-full bg-yellow-200 rounded-full h-2">
                        <div 
                          className="bg-yellow-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${wttjSyncProgress}%` }}
                        />
                      </div>
                      <p className="text-yellow-600 text-xs mt-1">{wttjSyncProgress}%</p>
                    </div>
                  )}
                  
                  {wttjSyncStatus === 'ready' && (
                    <div>
                      <p className="text-blue-700 text-sm">
                        ✅ WTTJ form is ready to submit!
                      </p>
                      <p className="text-blue-600 text-xs mt-1">
                        A browser window has the form filled. You can submit it when ready.
                      </p>
                    </div>
                  )}
                  
                  {wttjSyncStatus === 'error' && (
                    <p className="text-red-700 text-sm">
                      ⚠️ WTTJ form filling encountered an issue. You can create an account manually.
                    </p>
                  )}
                </div>
              )}
              
              <p className="text-gray-500 text-sm">Redirecting to login in 5 seconds...</p>
            </div>
          ) : (
            <div className="animate-fade-in">
              <div className="text-6xl mb-4">❌</div>
              <h2 className="text-3xl font-bold mb-4 text-red-600">Registration Failed</h2>
              <p className="text-gray-600 mb-6">{automationStatus.error}</p>
              <button 
                onClick={() => setAutomationStatus(null)}
                className="btn-primary"
              >
                Try Again
              </button>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-400 via-purple-500 to-indigo-600 flex items-center justify-center p-6">
      <div className="glass-panel max-w-2xl w-full p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-extrabold text-gray-900 mb-2">Join Swiply</h1>
          <p className="text-gray-600">Create your account and we'll automatically set up your career site profiles</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="bg-white/30 rounded-xl p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <User size={20} />
              Basic Information
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                  <input
                    type="email"
                    name="email"
                    required
                    value={formData.email}
                    onChange={handleInputChange}
                    className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="your@email.com"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                  <input
                    type="password"
                    name="password"
                    required
                    value={formData.password}
                    onChange={handleInputChange}
                    className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                <input
                  type="text"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="John"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                <input
                  type="text"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="Doe"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name (Display)</label>
                <input
                  type="text"
                  name="name"
                  required
                  value={formData.name}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="John Doe"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleInputChange}
                    className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="+33 6 12 34 56 78"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Professional Information */}
          <div className="bg-white/30 rounded-xl p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Briefcase size={20} />
              Professional Information
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                  <input
                    type="text"
                    name="location"
                    value={formData.location}
                    onChange={handleInputChange}
                    className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="Paris, France"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Years of Experience</label>
                <input
                  type="number"
                  name="experience_years"
                  value={formData.experience_years}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="3"
                  min="0"
                  max="50"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Skills</label>
                <div className="relative">
                  <Code className="absolute left-3 top-3 text-gray-400" size={20} />
                  <input
                    type="text"
                    name="skills"
                    value={formData.skills}
                    onChange={handleInputChange}
                    className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="React, TypeScript, Node.js, Python (comma separated)"
                  />
                </div>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">LinkedIn URL</label>
                <input
                  type="url"
                  name="linkedin_url"
                  value={formData.linkedin_url}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="https://linkedin.com/in/johndoe"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Professional Bio</label>
                <textarea
                  name="bio"
                  value={formData.bio}
                  onChange={handleInputChange}
                  rows={3}
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="Brief description of your professional experience and goals..."
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Work Preferences</label>
                <textarea
                  name="work_preference"
                  value={formData.work_preference}
                  onChange={handleInputChange}
                  rows={2}
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="e.g. Remote, Hybrid, 4 days a week..."
                />
              </div>
              
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Career Interests</label>
                <textarea
                  name="career_interests"
                  value={formData.career_interests}
                  onChange={handleInputChange}
                  rows={2}
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="e.g. Fullstack Development, AI integration..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Salary Expectations</label>
                <input
                  type="text"
                  name="salary_expectations"
                  value={formData.salary_expectations}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="e.g. 60k-80k EUR"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Availability</label>
                <select
                  name="availability"
                  value={formData.availability}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                >
                  <option value="">Select availability</option>
                  <option value="Available immediately">Available immediately</option>
                  <option value="1 month notice">1 month notice</option>
                  <option value="2 months notice">2 months notice</option>
                  <option value="3 months notice">3 months notice</option>
                  <option value="Not looking">Not looking</option>
                </select>
              </div>

              <div className="md:col-span-2 mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Resume Upload</label>
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-xl hover:border-indigo-500 transition-colors bg-white/50">
                  <div className="space-y-1 text-center">
                    <Upload className="mx-auto h-12 w-12 text-gray-400" />
                    <div className="flex text-sm text-gray-600 justify-center">
                      <label htmlFor="file-upload" className="relative cursor-pointer rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500">
                        <span>Upload a file</span>
                        <input id="file-upload" name="resume" type="file" className="sr-only" onChange={handleFileChange} accept=".pdf,.doc,.docx" />
                      </label>
                    </div>
                    <p className="text-xs text-gray-500">
                      {resumeFile ? resumeFile.name : 'PDF, DOC, DOCX up to 10MB'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 rounded-xl p-4">
            <h3 className="text-lg font-bold text-blue-800 mb-2">🚀 Automatic Career Site Setup</h3>
            <p className="text-blue-700 text-sm">
              After registration, we'll automatically create optimized profiles for you on:
            </p>
            <ul className="text-blue-600 text-sm mt-2 list-disc list-inside">
              <li>Welcome to the Jungle (WTTJ)</li>
              <li>SNCF Careers</li>
              <li>TotalEnergies Careers</li>
            </ul>
            <p className="text-blue-500 text-xs mt-2">
              Your profile will be enhanced using AI to maximize your job matching potential.
            </p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full btn-primary py-4 text-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="flex items-center justify-center gap-2">
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Creating Account & Setting Up Profiles...
              </div>
            ) : (
              'Create Account & Start Automation'
            )}
          </button>

          <div className="text-center">
            <p className="text-gray-600">
              Already have an account?{' '}
              <Link to="/login" className="text-indigo-600 hover:text-indigo-500 font-semibold">
                Sign in
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  )
}
