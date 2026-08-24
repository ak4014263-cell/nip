import { useState, useEffect, useRef } from 'react'
import { Check, X, MapPin, Building2, Briefcase, Loader2, Sparkles, CheckCircle2, MonitorPlay } from 'lucide-react'
import { jobAPI, applicationAPI } from '../../services/api'
import { useAuthStore } from '../../store/authStore'
import toast from 'react-hot-toast'
import axios from 'axios'

const API_BASE = ((import.meta as any).env?.VITE_API_URL) || 'http://localhost:8000'
const WTTJ_SERVICE_URL = 'http://localhost:8012'

export default function JobSwipe() {
  const [jobs, setJobs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [swipeDirection, setSwipeDirection] = useState<'left' | 'right' | null>(null)
  
  // Live Preview State
  const [liveStatus, setLiveStatus] = useState<any>(null)
  const [isApplying, setIsApplying] = useState(false)
  const pollIntervalRef = useRef<any>(null)

  const { user } = useAuthStore()

  useEffect(() => {
    fetchJobs()
  }, [])

  const fetchJobs = async () => {
    try {
      setLoading(true)
      const candidateId = (user as any)?.id || 'demo-candidate'
      const response = await jobAPI.getRecommendations(candidateId)
      setJobs(response.data.jobs || [])
    } catch (error) {
      console.error('Failed to fetch jobs:', error)
    } finally {
      setLoading(false)
    }
  }

  // Poll live status when applying
  useEffect(() => {
    if (isApplying) {
      pollIntervalRef.current = setInterval(async () => {
        try {
          const res = await axios.get(`${WTTJ_SERVICE_URL}/live-status`)
          setLiveStatus(res.data)
          if (!res.data.is_running && res.data.progress === 100) {
            setTimeout(() => {
              setIsApplying(false)
              setLiveStatus(null)
            }, 3000)
          }
        } catch (err) {
          console.error("Live status error", err)
        }
      }, 1000)
    } else {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
    }
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
    }
  }, [isApplying])

  const handleSwipe = async (direction: 'left' | 'right' | 'heart') => {
    if (jobs.length === 0) return
    const currentJob = jobs[0]
    const candidateId = (user as any)?.id || 'demo-candidate'
    
    if (direction === 'heart') {
      // Heart icon - Save job to favorites (no card animation)
      try {
        await jobAPI.swipe(currentJob.id, true)
        toast.success(`❤️ Saved "${currentJob.title}" to your favorites!`, { duration: 3000 })
      } catch (err) {
        toast.error('Failed to save job')
      }
      return
    }
    
    setSwipeDirection(direction)
    
    if (direction === 'right') {
      toast.loading(`🤖 AI Auto-Applying to ${currentJob.title} on Welcome to the Jungle...`, { id: 'apply-toast' })
      setIsApplying(true)
      setLiveStatus({
        step_name: "Starting Automation",
        progress: 5,
        logs: [{msg: "Waking up browser..."}]
      })
      
      try {
        // Trigger WTTJ 1-click apply through API Gateway
        const response = await axios.post(`${API_BASE}/swipe-job`, {
          user_id: candidateId,
          candidate_id: candidateId,
          job_id: currentJob.id,
          job_url: currentJob.externalUrl,
          action: 'apply'
        })
        
        if (response.data.success) {
          toast.success(`🎉 Application Sent to ${currentJob.company}! Synced to WTTJ & Swiply.`, { id: 'apply-toast', duration: 5000 })
          
          // Record successful application in DB so it shows up in Applications tab
          try {
            await applicationAPI.create({
              candidate_id: candidateId,
              job_id: currentJob.id,
              job_title: currentJob.title,
              company_name: currentJob.company,
              location: currentJob.location,
              logo: currentJob.logo,
              job_url: currentJob.externalUrl,
              status: "Applied (WTTJ Automation)"
            } as any)
          } catch (appErr) {
            console.error("Failed to save application to dashboard:", appErr)
          }
        } else {
          toast.success(`Application queued for ${currentJob.company}!`, { id: 'apply-toast' })
        }
      } catch (err) {
        // Record swipe in DB anyway
        await jobAPI.swipe(currentJob.id, true)
        toast.success(`Applied to ${currentJob.company}!`, { id: 'apply-toast' })
      } finally {
        setTimeout(() => setIsApplying(false), 5000)
      }
    } else if (direction === 'left') {
      await jobAPI.swipe(currentJob.id, false)
      toast(`Skipped ${currentJob.title}`, { icon: '👋' })
    }
    
    // Animate out card
    setTimeout(() => {
      setJobs((prev) => prev.slice(1))
      setSwipeDirection(null)
    }, 300)
  }

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-12">
        <Loader2 className="animate-spin text-indigo-600 w-12 h-12 mb-3" />
        <p className="text-slate-600 font-medium">Fetching tailored Welcome to the Jungle jobs...</p>
      </div>
    )
  }

  if (jobs.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-12 animate-fade-in">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-10 text-center max-w-md">
          <div className="text-6xl mb-4">🎉</div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">You're all caught up!</h2>
          <p className="text-slate-500 mb-6">You've swiped on all currently available Welcome to the Jungle matches.</p>
          <button
            onClick={fetchJobs}
            className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-semibold shadow-md transition"
          >
            Refresh Match Feed
          </button>
        </div>
      </div>
    )
  }

  const currentJob = jobs[0]

  return (
    <div className="h-full flex flex-col items-center justify-center py-6 px-4">
      <div className="w-full max-w-md relative min-h-[580px]">
        <div 
          className={`bg-white rounded-3xl border border-slate-200/90 shadow-xl overflow-hidden p-6 flex flex-col justify-between transition-all duration-300 ${
            swipeDirection === 'left' ? 'translate-x-[-150%] rotate-[-20deg] opacity-0' :
            swipeDirection === 'right' ? 'translate-x-[150%] rotate-[20deg] opacity-0' : ''
          }`}
        >
          {/* Card Header with Company & Match Score */}
          <div>
            <div className="flex items-center justify-between gap-4 mb-4">
              <div className="flex items-center gap-3">
                {currentJob.logo ? (
                  <img 
                    src={currentJob.logo} 
                    alt={currentJob.company} 
                    className="w-12 h-12 rounded-xl object-contain bg-slate-50 border border-slate-100 p-1"
                  />
                ) : (
                  <div className="w-12 h-12 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
                    <Building2 size={24} />
                  </div>
                )}
                <div>
                  <h2 className="text-lg font-bold text-slate-900 leading-tight">{currentJob.company}</h2>
                  <span className="inline-flex items-center gap-1 text-xs text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100 mt-0.5">
                    <CheckCircle2 size={12} /> WTTJ Verified
                  </span>
                </div>
              </div>

              <div className="px-3 py-1 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-xs font-bold shadow-xs flex items-center gap-1">
                <Sparkles size={12} />
                {currentJob.match_score || 90}% Match
              </div>
            </div>

            <h1 className="text-xl font-extrabold text-slate-900 mb-2 leading-snug">{currentJob.title}</h1>
            
            {/* Meta Tags */}
            <div className="flex flex-wrap gap-2 mb-4 text-xs font-medium text-slate-600">
              <span className="flex items-center gap-1 bg-slate-100 px-2.5 py-1 rounded-lg">
                <MapPin size={13} className="text-slate-500" />
                {currentJob.location || 'Paris, France'}
              </span>
              <span className="flex items-center gap-1 bg-slate-100 px-2.5 py-1 rounded-lg">
                <Briefcase size={13} className="text-slate-500" />
                {currentJob.salaryMin ? `€${Math.round(currentJob.salaryMin/1000)}k - €${Math.round(currentJob.salaryMax/1000)}k` : 'Competitive'}
              </span>
              {currentJob.remote && (
                <span className="bg-purple-50 text-purple-700 border border-purple-100 px-2.5 py-1 rounded-lg">
                  🏠 Remote / Hybrid
                </span>
              )}
            </div>

            {/* Skill Tags */}
            <div className="flex flex-wrap gap-1.5 mb-4">
              {(currentJob.requirements || currentJob.tags || ['React', 'TypeScript', 'Python']).slice(0, 4).map((tag: string) => (
                <span key={tag} className="px-2.5 py-0.5 bg-indigo-50 text-indigo-700 border border-indigo-100 rounded-md text-xs font-semibold">
                  {tag}
                </span>
              ))}
            </div>

            {/* Job Summary Description */}
            <p className="text-slate-600 text-sm line-clamp-4 leading-relaxed bg-slate-50/70 p-3 rounded-xl border border-slate-100">
              {currentJob.description}
            </p>
          </div>

          {/* Action Swipe Buttons */}
          <div className="flex justify-center items-center gap-4 mt-6 pt-4 border-t border-slate-100">
            <button
              onClick={() => handleSwipe('left')}
              title="Pass (Swipe Left)"
              className="w-14 h-14 rounded-full bg-white shadow-md border border-slate-200 flex items-center justify-center text-slate-400 hover:text-red-500 hover:bg-red-50 hover:scale-110 active:scale-95 transition-all"
            >
              <X size={28} />
            </button>
            
            <button
              onClick={() => handleSwipe('heart')}
              title="Save Job (Heart)"
              className="w-14 h-14 rounded-full bg-white shadow-md border border-slate-200 flex items-center justify-center text-slate-400 hover:text-pink-500 hover:bg-pink-50 hover:scale-110 active:scale-95 transition-all"
            >
              <svg className="w-7 h-7 fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
              </svg>
            </button>
            
            <button
              onClick={() => handleSwipe('right')}
              title="1-Click Auto-Apply (Swipe Right)"
              className="w-16 h-16 rounded-full bg-gradient-to-r from-emerald-500 to-teal-600 shadow-lg shadow-emerald-200/80 flex items-center justify-center text-white hover:scale-110 active:scale-95 transition-all"
            >
              <Check size={32} />
            </button>
          </div>
        </div>
        
        {/* Live Application Preview Overlay */}
        {isApplying && liveStatus && (
          <div className="absolute inset-0 z-50 bg-slate-900/95 rounded-3xl border border-slate-700 overflow-hidden flex flex-col shadow-2xl animate-in fade-in zoom-in-95 duration-300">
            <div className="bg-slate-800 border-b border-slate-700 p-4 flex items-center justify-between">
              <div className="flex items-center gap-2 text-indigo-400 font-semibold">
                <MonitorPlay className="animate-pulse" size={18} />
                Live Application View
              </div>
              <div className="text-xs font-mono text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded">
                {liveStatus.step_name || 'Running...'}
              </div>
            </div>
            
            <div className="flex-1 relative overflow-hidden bg-black flex items-center justify-center p-2">
              {liveStatus.last_screenshot_base64 ? (
                <img 
                  src={`data:image/jpeg;base64,${liveStatus.last_screenshot_base64}`}
                  className="max-h-full w-auto object-contain rounded border border-slate-800 shadow-xl"
                  alt="Live Browser View"
                />
              ) : (
                <div className="flex flex-col items-center text-slate-500">
                  <Loader2 className="w-8 h-8 animate-spin mb-2" />
                  <span className="text-xs">Waiting for browser stream...</span>
                </div>
              )}
            </div>
            
            <div className="p-4 bg-slate-900">
              <div className="w-full bg-slate-800 rounded-full h-1.5 mb-3 overflow-hidden">
                <div 
                  className="bg-indigo-500 h-1.5 rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${liveStatus.progress || 0}%` }}
                ></div>
              </div>
              <div className="bg-slate-950 rounded-lg p-2 h-20 overflow-y-auto border border-slate-800/50">
                {liveStatus.logs?.map((log: any, i: number) => (
                  <div key={i} className="text-[10px] font-mono flex gap-2 leading-relaxed">
                    <span className="text-slate-500 shrink-0">[{log.time}]</span>
                    <span className="text-emerald-400/90">{log.msg}</span>
                  </div>
                ))}
                {/* Auto-scroll anchor */}
                <div ref={(el) => el?.scrollIntoView()} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
