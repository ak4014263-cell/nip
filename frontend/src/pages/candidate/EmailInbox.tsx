import { useState, useEffect } from 'react'
import { Mail, Star, ExternalLink, Loader2, RefreshCw, CheckCircle } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import axios from 'axios'
import toast from 'react-hot-toast'

const API_BASE = ((import.meta as any).env?.VITE_API_URL) || 'http://localhost:8000'

export default function EmailInbox() {
  const { user } = useAuthStore()
  const [emails, setEmails] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedEmail, setSelectedEmail] = useState<any>(null)
  const [gmailAddress, setGmailAddress] = useState<string | null>(null)
  const [stats, setStats] = useState({ total: 0, unread: 0, verification: 0 })

  useEffect(() => {
    fetchEmails()
  }, [])

  const fetchEmails = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`${API_BASE}/gmail/inbox/${user?.id}`)
      
      if (response.data) {
        setGmailAddress(response.data.gmail_address)
        setEmails(response.data.emails || [])
        setStats({
          total: response.data.total || 0,
          unread: response.data.unread || 0,
          verification: (response.data.emails || []).filter((e: any) => e.category === 'verification').length
        })
        
        if (response.data.emails?.length > 0) {
          setSelectedEmail(response.data.emails[0])
        }
      }
    } catch (error) {
      console.error('Failed to fetch emails:', error)
      toast.error('Failed to load emails')
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    toast.loading('Refreshing emails...', { id: 'refresh' })
    try {
      await axios.post(`${API_BASE}/gmail/fetch-wttj-emails/${user?.id}`)
      await fetchEmails()
      toast.success('Emails refreshed!', { id: 'refresh' })
    } catch (error) {
      toast.error('Failed to refresh', { id: 'refresh' })
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'verification': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'job_alert': return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'application': return 'bg-green-100 text-green-800 border-green-200'
      case 'welcome': return 'bg-purple-100 text-purple-800 border-purple-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'verification': return '🔐'
      case 'job_alert': return '💼'
      case 'application': return '📨'
      case 'welcome': return '👋'
      default: return '📧'
    }
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="animate-spin text-indigo-500 w-12 h-12" />
      </div>
    )
  }

  if (!gmailAddress) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-8">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md text-center">
          <Mail className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Gmail Not Connected</h2>
          <p className="text-gray-600 mb-6">
            Please complete your profile setup to connect Gmail and view your WTTJ emails
          </p>
          <a
            href="/candidate/dashboard"
            className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            Go to Dashboard
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">📬 Email Inbox</h1>
              <p className="text-gray-600">WTTJ emails from {gmailAddress}</p>
            </div>
            <button
              onClick={handleRefresh}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              <RefreshCw size={20} />
              Refresh
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-xl shadow-sm p-4">
            <p className="text-gray-600 text-sm mb-1">Total Emails</p>
            <p className="text-3xl font-bold text-blue-600">{stats.total}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4">
            <p className="text-gray-600 text-sm mb-1">Unread</p>
            <p className="text-3xl font-bold text-green-600">{stats.unread}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4">
            <p className="text-gray-600 text-sm mb-1">Verification</p>
            <p className="text-3xl font-bold text-yellow-600">{stats.verification}</p>
          </div>
        </div>

        {/* Email List */}
        {emails.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <Mail className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-xl font-bold text-gray-900 mb-2">No WTTJ Emails Yet</h3>
            <p className="text-gray-600 mb-4">
              Your WTTJ emails will appear here once you receive them
            </p>
            <button
              onClick={handleRefresh}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              <RefreshCw size={16} />
              Check for Emails
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <div className="grid grid-cols-3 divide-x">
              {/* Email List */}
              <div className="col-span-1 overflow-y-auto max-h-[600px]">
                {emails.map((email) => (
                  <div
                    key={email.id}
                    onClick={() => setSelectedEmail(email)}
                    className={`p-4 border-b cursor-pointer transition ${
                      selectedEmail?.id === email.id
                        ? 'bg-blue-50 border-l-4 border-l-blue-600'
                        : 'hover:bg-gray-50 border-l-4 border-l-transparent'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{getCategoryIcon(email.category)}</span>
                        {!email.read && (
                          <span className="w-2 h-2 bg-blue-600 rounded-full"></span>
                        )}
                      </div>
                      <span className="text-xs text-gray-500">
                        {new Date(email.received_at * 1000).toLocaleDateString()}
                      </span>
                    </div>
                    
                    <h4 className="font-semibold text-gray-900 text-sm mb-1 line-clamp-2">
                      {email.subject}
                    </h4>
                    
                    <p className="text-xs text-gray-600 mb-2 line-clamp-1">
                      {email.sender}
                    </p>
                    
                    <span className={`inline-block text-xs px-2 py-1 rounded-full border ${getCategoryColor(email.category)}`}>
                      {email.category}
                    </span>
                  </div>
                ))}
              </div>

              {/* Email Content */}
              <div className="col-span-2 p-6 overflow-y-auto max-h-[600px]">
                {selectedEmail ? (
                  <div>
                    <div className="mb-6 pb-6 border-b">
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <h2 className="text-2xl font-bold text-gray-900 mb-2">
                            {selectedEmail.subject}
                          </h2>
                          <div className="flex items-center gap-4 text-sm text-gray-600">
                            <span>From: <strong>{selectedEmail.sender}</strong></span>
                            <span>To: <strong>{selectedEmail.recipient}</strong></span>
                          </div>
                        </div>
                        <button className="text-gray-400 hover:text-yellow-500">
                          <Star size={24} />
                        </button>
                      </div>
                      
                      <div className="flex items-center gap-2 mb-4">
                        <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border ${getCategoryColor(selectedEmail.category)}`}>
                          <span>{getCategoryIcon(selectedEmail.category)}</span>
                          <span className="text-sm font-semibold">{selectedEmail.category}</span>
                        </span>
                        
                        <span className="text-sm text-gray-500">
                          {new Date(selectedEmail.received_at * 1000).toLocaleString()}
                        </span>
                      </div>

                      {selectedEmail.verification_link && (
                        <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
                          <div className="flex items-center gap-3">
                            <CheckCircle className="text-green-600" size={24} />
                            <div className="flex-1">
                              <h4 className="font-bold text-green-900 mb-1">Verification Link Found!</h4>
                              <p className="text-sm text-green-700 mb-2">Click to verify your WTTJ account</p>
                            </div>
                            <a
                              href={selectedEmail.verification_link}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
                            >
                              <ExternalLink size={16} />
                              Verify Now
                            </a>
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="prose max-w-none">
                      <div className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                        {selectedEmail.content ? (
                          selectedEmail.content.split(/(https?:\/\/[^\s]+)/g).map((part: string, i: number) => 
                            part.match(/https?:\/\/[^\s]+/) ? (
                              <a key={i} href={part} target="_blank" rel="noopener noreferrer" className="text-blue-600 font-semibold hover:underline bg-blue-50 px-1 rounded">
                                {part}
                              </a>
                            ) : (
                              part
                            )
                          )
                        ) : 'No content available'}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center text-gray-400">
                    <div className="text-center">
                      <Mail className="w-16 h-16 mx-auto mb-4" />
                      <p>Select an email to read</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
