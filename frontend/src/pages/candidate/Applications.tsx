import { useState, useEffect } from 'react'
import { Building2, Calendar, ExternalLink, Loader2, CheckCircle2, Clock, XCircle, RefreshCw, Layers } from 'lucide-react'
import axios from 'axios'
import { useAuthStore } from '../../store/authStore'

const API_BASE = 'http://localhost:8000'

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: any }> = {
  applied:    { label: 'Applied',     color: 'bg-indigo-50 text-indigo-700 border-indigo-200',  icon: CheckCircle2 },
  pending:    { label: 'Pending',     color: 'bg-amber-50 text-amber-700 border-amber-200',     icon: Clock },
  interview:  { label: 'Interview',   color: 'bg-emerald-50 text-emerald-700 border-emerald-200', icon: CheckCircle2 },
  rejected:   { label: 'Rejected',   color: 'bg-red-50 text-red-600 border-red-200',            icon: XCircle },
  swiped:     { label: 'Auto-Applied', color: 'bg-purple-50 text-purple-700 border-purple-200', icon: CheckCircle2 },
}

export default function Applications() {
  const { user } = useAuthStore()
  const [apps, setApps] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (user?.id) fetchApps()
  }, [user?.id])

  const fetchApps = async () => {
    try {
      setLoading(true)
      setError(null)
      // Filter by current user's candidate_id
      const response = await axios.get(`${API_BASE}/applications`, {
        params: { candidate_id: user?.id },
        timeout: 8000
      })
      const data = Array.isArray(response.data) ? response.data : (response.data?.applications || [])
      // Extra client-side safety: only show apps belonging to this user
      const mine = data.filter((a: any) =>
        !a.candidate_id || a.candidate_id === user?.id ||
        a.candidateId === user?.id || a.userId === user?.id
      )
      setApps(mine)
    } catch (err: any) {
      console.error('Failed to fetch applications:', err)
      setError('Could not load applications — make sure you are connected.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-4 p-12">
        <Loader2 className="animate-spin text-indigo-500 w-10 h-10" />
        <p className="text-slate-500 text-sm">Loading your applications…</p>
      </div>
    )
  }

  return (
    <div className="animate-fade-in max-w-5xl mx-auto py-6 px-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">My Applications</h1>
          <p className="text-slate-500 mt-1 text-sm">
            Applications auto-submitted when you swiped right on Welcome to the Jungle.
          </p>
        </div>
        <button
          onClick={fetchApps}
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-600 rounded-xl font-semibold text-sm transition"
        >
          <RefreshCw size={15} />
          Refresh
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Stats bar */}
      {apps.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {[
            { label: 'Total', value: apps.length, color: 'text-slate-700' },
            { label: 'Auto-Applied', value: apps.filter(a => ['applied', 'swiped'].includes(a.status)).length, color: 'text-indigo-600' },
            { label: 'Interview', value: apps.filter(a => a.status === 'interview').length, color: 'text-emerald-600' },
            { label: 'Pending', value: apps.filter(a => a.status === 'pending').length, color: 'text-amber-600' },
          ].map(s => (
            <div key={s.label} className="bg-white rounded-xl border border-slate-200 px-4 py-3 text-center shadow-xs">
              <p className={`text-2xl font-extrabold ${s.color}`}>{s.value}</p>
              <p className="text-xs text-slate-500 font-medium mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {apps.length === 0 && !error ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-14 text-center shadow-xs">
          <div className="w-16 h-16 rounded-2xl bg-indigo-50 flex items-center justify-center text-3xl mx-auto mb-4">
            <Layers className="text-indigo-400" size={32} />
          </div>
          <h3 className="text-xl font-bold text-slate-900 mb-1">No applications yet</h3>
          <p className="text-slate-500 mb-6 text-sm max-w-sm mx-auto">
            Swipe right on any job in the <strong>Job Swipe</strong> tab — Swiply AI will auto-apply on Welcome to the Jungle in 1 click!
          </p>
          <a
            href="/candidate/swipe"
            className="inline-flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-xl font-semibold shadow-md shadow-indigo-200 transition"
          >
            <Layers size={16} />
            Start Swiping Jobs
          </a>
        </div>
      ) : (
        /* Applications list */
        <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
          <ul className="divide-y divide-slate-100">
            {apps.map((app, i) => {
              const jobTitle = app.job?.title || app.title || 'Software Engineer'
              const companyName = app.job?.company || app.company || 'Welcome to the Jungle Employer'
              const logo = app.job?.logo || app.logo
              const date = app.appliedAt || app.applied_at || app.createdAt || app.created_at
              const dateStr = date ? new Date(date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : 'Recently'
              const externalUrl = app.job?.externalUrl || app.externalUrl || app.job_url
              const status = app.status || 'applied'
              const statusCfg = STATUS_CONFIG[status] || STATUS_CONFIG['applied']
              const StatusIcon = statusCfg.icon

              return (
                <li key={app.id || i} className="p-5 hover:bg-slate-50/60 transition-colors group">
                  <div className="flex items-center justify-between gap-4">
                    {/* Left: logo + info */}
                    <div className="flex items-center gap-4 min-w-0">
                      <div className="w-11 h-11 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-center flex-shrink-0 overflow-hidden">
                        {logo ? (
                          <img src={logo} alt={companyName} className="w-full h-full object-contain p-1" />
                        ) : (
                          <Building2 size={20} className="text-slate-400" />
                        )}
                      </div>
                      <div className="min-w-0">
                        <p className="font-bold text-slate-900 text-sm truncate">{jobTitle}</p>
                        <p className="text-xs text-slate-500 truncate">{companyName}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Calendar size={11} className="text-slate-400 flex-shrink-0" />
                          <span className="text-xs text-slate-400">{dateStr}</span>
                        </div>
                      </div>
                    </div>

                    {/* Right: status + link */}
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-semibold ${statusCfg.color}`}>
                        <StatusIcon size={11} />
                        {statusCfg.label}
                      </span>
                      {externalUrl && (
                        <a
                          href={externalUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="w-8 h-8 rounded-lg bg-slate-100 hover:bg-indigo-50 border border-slate-200 hover:border-indigo-300 flex items-center justify-center text-slate-400 hover:text-indigo-600 transition"
                        >
                          <ExternalLink size={13} />
                        </a>
                      )}
                    </div>
                  </div>
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </div>
  )
}
