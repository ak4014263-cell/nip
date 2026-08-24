import { useState, useEffect, useRef } from 'react'
import {
  User, Briefcase, GraduationCap, Code2,
  FileText, Upload, Save, X, Plus, Trash2, Loader2,
  CheckCircle, Globe
} from 'lucide-react'
import axios from 'axios'
import { useAuthStore } from '../../store/authStore'
import toast from 'react-hot-toast'

const API_BASE = 'http://localhost:8000'

const defaultProfile = {
  first_name: '', last_name: '', email: '', phone: '', location: '',
  bio: '', current_title: '', linkedin_url: '', github_url: '', portfolio_url: '',
  skills: [] as string[], languages: [] as string[],
  experience: [] as any[], education: [] as any[], resume_url: null as string | null
}

function Avatar({ name }: { name: string }) {
  const initials = name.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2) || '?'
  return (
    <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-3xl font-black shadow-lg shadow-indigo-200">
      {initials}
    </div>
  )
}

function SectionCard({ title, icon: Icon, children }: { title: string; icon: any; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-100 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center">
          <Icon size={16} className="text-indigo-600" />
        </div>
        <h2 className="font-bold text-slate-800 text-base">{title}</h2>
      </div>
      <div className="p-6">{children}</div>
    </div>
  )
}

function Field({ label, value, type = 'text', multiline = false, onChange, placeholder }: any) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{label}</label>
      {multiline ? (
        <textarea value={value} onChange={(e: any) => onChange(e.target.value)} rows={4} placeholder={placeholder}
          className="px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 text-sm resize-none focus:outline-none focus:border-indigo-400 focus:bg-white transition" />
      ) : (
        <input type={type} value={value} onChange={(e: any) => onChange(e.target.value)} placeholder={placeholder}
          className="px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 text-sm focus:outline-none focus:border-indigo-400 focus:bg-white transition" />
      )}
    </div>
  )
}

export default function Profile() {
  const { user } = useAuthStore()
  const [profile, setProfile] = useState({ ...defaultProfile })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [saved, setSaved] = useState(false)
  const [newSkill, setNewSkill] = useState('')
  const [newLang, setNewLang] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => { if (user?.id) fetchProfile() }, [user?.id])

  const fetchProfile = async () => {
    try {
      setLoading(true)
      const res = await axios.get(`${API_BASE}/user/profile/${user?.id}`, { timeout: 6000 })
      const d = res.data
      setProfile({
        first_name: d.first_name || (user?.name?.split(' ')[0]) || '',
        last_name: d.last_name || (user?.name?.split(' ').slice(1).join(' ')) || '',
        email: d.email || user?.email || '',
        phone: d.phone || '',
        location: d.current_location || d.location || '',
        bio: d.bio || '',
        current_title: d.current_title || '',
        linkedin_url: d.linkedin_url || '',
        github_url: d.github_url || '',
        portfolio_url: d.portfolio_url || '',
        skills: Array.isArray(d.skills) ? d.skills : [],
        languages: Array.isArray(d.languages) ? d.languages : [],
        experience: Array.isArray(d.experience) ? d.experience : [],
        education: Array.isArray(d.education) ? d.education : [],
        resume_url: d.resume_url || d.resume_path || null
      })
    } catch {
      setProfile(prev => ({ ...prev, first_name: user?.name?.split(' ')[0] || '', last_name: user?.name?.split(' ').slice(1).join(' ') || '', email: user?.email || '' }))
    } finally { setLoading(false) }
  }

  const saveProfile = async () => {
    setSaving(true)
    try {
      await axios.put(`${API_BASE}/user/profile/${user?.id}`, {
        first_name: profile.first_name, last_name: profile.last_name, phone: profile.phone,
        current_location: profile.location, bio: profile.bio, current_title: profile.current_title,
        linkedin_url: profile.linkedin_url, github_url: profile.github_url, portfolio_url: profile.portfolio_url,
        skills: profile.skills, languages: profile.languages, experience: profile.experience, education: profile.education,
      }, { timeout: 8000 })
      setSaved(true); toast.success('Profile saved!'); setTimeout(() => setSaved(false), 3000)
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Could not save profile') }
    finally { setSaving(false) }
  }

  const uploadCV = async (file: File) => {
    setUploading(true)
    const fd = new FormData(); fd.append('file', file); fd.append('user_id', user?.id || '')
    try {
      const res = await axios.post(`${API_BASE}/user/upload-cv/${user?.id}`, fd, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 30000 })
      setProfile(prev => ({ ...prev, resume_url: res.data.resume_url || res.data.file_url || '' }))
      toast.success('CV uploaded! Profile will be updated.'); await fetchProfile()
    } catch { toast.error('Failed to upload CV') }
    finally { setUploading(false) }
  }

  const up = (f: string) => (v: any) => setProfile(prev => ({ ...prev, [f]: v }))
  const addSkill = () => { const s = newSkill.trim(); if (s && !profile.skills.includes(s)) { setProfile(p => ({ ...p, skills: [...p.skills, s] })); setNewSkill('') } }
  const addLang = () => { const l = newLang.trim(); if (l && !profile.languages.includes(l)) { setProfile(p => ({ ...p, languages: [...p.languages, l] })); setNewLang('') } }
  const addExp = () => setProfile(p => ({ ...p, experience: [...p.experience, { id: Date.now().toString(), company: '', title: '', start_date: '', end_date: '', is_current: false, description: '' }] }))
  const updExp = (id: string, f: string, v: any) => setProfile(p => ({ ...p, experience: p.experience.map((e: any) => e.id === id ? { ...e, [f]: v } : e) }))
  const addEdu = () => setProfile(p => ({ ...p, education: [...p.education, { id: Date.now().toString(), institution: '', degree: '', field: '', start_date: '', end_date: '' }] }))
  const updEdu = (id: string, f: string, v: string) => setProfile(p => ({ ...p, education: p.education.map((e: any) => e.id === id ? { ...e, [f]: v } : e) }))

  if (loading) return <div className="h-full flex flex-col items-center justify-center gap-3"><Loader2 className="animate-spin text-indigo-500 w-10 h-10" /><p className="text-slate-500 text-sm">Loading profile…</p></div>

  return (
    <div className="animate-fade-in max-w-4xl mx-auto py-6 px-4 pb-24">
      <div className="flex items-start justify-between mb-8 gap-4">
        <div className="flex items-center gap-5">
          <Avatar name={`${profile.first_name} ${profile.last_name}`} />
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900">{(`${profile.first_name} ${profile.last_name}`).trim() || user?.name || 'My Profile'}</h1>
            {profile.current_title && <p className="text-slate-500 text-sm mt-0.5">{profile.current_title}</p>}
            <p className="text-xs text-slate-400 mt-1">{profile.email}</p>
          </div>
        </div>
        <button onClick={saveProfile} disabled={saving}
          className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm shadow-md transition ${saved ? 'bg-emerald-500 text-white shadow-emerald-200' : 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white shadow-indigo-200'} disabled:opacity-60`}>
          {saving ? <Loader2 size={15} className="animate-spin" /> : saved ? <CheckCircle size={15} /> : <Save size={15} />}
          {saving ? 'Saving…' : saved ? 'Saved!' : 'Save Profile'}
        </button>
      </div>

      <div className="space-y-6">
        <SectionCard title="CV / Resume" icon={FileText}>
          <div className="flex items-center gap-4">
            <div onClick={() => fileRef.current?.click()} className="flex-1 border-2 border-dashed border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/40 rounded-xl p-6 text-center cursor-pointer transition group">
              <input ref={fileRef} type="file" accept=".pdf,.doc,.docx" className="hidden" onChange={e => e.target.files?.[0] && uploadCV(e.target.files[0])} />
              {uploading ? <div className="flex flex-col items-center gap-2"><Loader2 size={28} className="text-indigo-500 animate-spin" /><p className="text-sm text-indigo-600 font-semibold">Uploading…</p></div>
                : <div className="flex flex-col items-center gap-2"><Upload size={28} className="text-slate-300 group-hover:text-indigo-400 transition" /><p className="text-sm font-semibold text-slate-600 group-hover:text-indigo-700">{profile.resume_url ? 'Replace CV' : 'Upload CV'}</p><p className="text-xs text-slate-400">PDF, DOC, DOCX</p></div>}
            </div>
            {profile.resume_url && <a href={profile.resume_url} target="_blank" rel="noopener noreferrer" className="flex flex-col items-center gap-2 px-5 py-4 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 rounded-xl transition"><FileText size={24} className="text-indigo-500" /><span className="text-xs font-semibold text-indigo-700">View CV</span></a>}
          </div>
        </SectionCard>

        <SectionCard title="Personal Information" icon={User}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label="First Name" value={profile.first_name} onChange={up('first_name')} placeholder="Lucas" />
            <Field label="Last Name" value={profile.last_name} onChange={up('last_name')} placeholder="Dupont" />
            <Field label="Job Title" value={profile.current_title} onChange={up('current_title')} placeholder="Senior Software Engineer" />
            <Field label="Phone" value={profile.phone} onChange={up('phone')} placeholder="+33 6 12 34 56 78" />
            <Field label="Location" value={profile.location} onChange={up('location')} placeholder="Paris, France" />
            <Field label="Email" value={profile.email} onChange={up('email')} type="email" />
          </div>
          <div className="mt-4"><Field label="Bio / Summary" value={profile.bio} onChange={up('bio')} multiline placeholder="Tell employers about yourself…" /></div>
        </SectionCard>

        <SectionCard title="Social & Portfolio" icon={Globe}>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[{ label: 'LinkedIn', field: 'linkedin_url', placeholder: 'https://linkedin.com/in/…' }, { label: 'GitHub', field: 'github_url', placeholder: 'https://github.com/…' }, { label: 'Portfolio', field: 'portfolio_url', placeholder: 'https://yoursite.com' }].map(l => (
              <div key={l.field} className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{l.label}</label>
                <input value={(profile as any)[l.field]} onChange={e => up(l.field)(e.target.value)} placeholder={l.placeholder}
                  className="px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 text-sm focus:outline-none focus:border-indigo-400 focus:bg-white transition" />
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Skills" icon={Code2}>
          <div className="flex flex-wrap gap-2 mb-4">
            {profile.skills.map((s: string) => <span key={s} className="inline-flex items-center gap-1.5 px-3 py-1 bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-full text-xs font-semibold">{s}<button onClick={() => setProfile(p => ({ ...p, skills: p.skills.filter(x => x !== s) }))} className="hover:text-red-500"><X size={11} /></button></span>)}
            {!profile.skills.length && <p className="text-sm text-slate-400 italic">No skills added yet</p>}
          </div>
          <div className="flex gap-2">
            <input value={newSkill} onChange={e => setNewSkill(e.target.value)} onKeyDown={e => e.key === 'Enter' && addSkill()} placeholder="Add a skill (e.g. Python)" className="flex-1 px-3.5 py-2 rounded-xl border border-slate-200 bg-slate-50 text-sm focus:outline-none focus:border-indigo-400 transition" />
            <button onClick={addSkill} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold transition"><Plus size={15} /></button>
          </div>
        </SectionCard>

        <SectionCard title="Languages" icon={Globe}>
          <div className="flex flex-wrap gap-2 mb-4">
            {profile.languages.map((l: string) => <span key={l} className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full text-xs font-semibold">{l}<button onClick={() => setProfile(p => ({ ...p, languages: p.languages.filter(x => x !== l) }))} className="hover:text-red-500"><X size={11} /></button></span>)}
          </div>
          <div className="flex gap-2">
            <input value={newLang} onChange={e => setNewLang(e.target.value)} onKeyDown={e => e.key === 'Enter' && addLang()} placeholder="English – Native" className="flex-1 px-3.5 py-2 rounded-xl border border-slate-200 bg-slate-50 text-sm focus:outline-none focus:border-indigo-400 transition" />
            <button onClick={addLang} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-sm font-semibold transition"><Plus size={15} /></button>
          </div>
        </SectionCard>

        <SectionCard title="Work Experience" icon={Briefcase}>
          <div className="space-y-5">
            {profile.experience.map((exp: any) => (
              <div key={exp.id} className="p-4 bg-slate-50 rounded-xl border border-slate-200 relative group">
                <button onClick={() => setProfile(p => ({ ...p, experience: p.experience.filter((e: any) => e.id !== exp.id) }))} className="absolute top-3 right-3 w-7 h-7 flex items-center justify-center rounded-lg bg-red-50 text-red-400 hover:bg-red-100 transition opacity-0 group-hover:opacity-100"><Trash2 size={13} /></button>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {[['title', 'Job Title', 'Software Engineer'], ['company', 'Company', 'Google']].map(([f, lbl, ph]) => (
                    <div key={f} className="flex flex-col gap-1"><label className="text-xs text-slate-500 font-semibold uppercase tracking-wider">{lbl}</label><input value={exp[f]} onChange={e => updExp(exp.id, f, e.target.value)} placeholder={ph} className="px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm focus:outline-none focus:border-indigo-400" /></div>
                  ))}
                  <div className="flex flex-col gap-1"><label className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Start Date</label><input type="month" value={exp.start_date} onChange={e => updExp(exp.id, 'start_date', e.target.value)} className="px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm focus:outline-none focus:border-indigo-400" /></div>
                  <div className="flex flex-col gap-1"><label className="text-xs text-slate-500 font-semibold uppercase tracking-wider">End Date</label><input type="month" value={exp.end_date} disabled={exp.is_current} onChange={e => updExp(exp.id, 'end_date', e.target.value)} className="px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm focus:outline-none focus:border-indigo-400 disabled:bg-slate-100 disabled:text-slate-400" /><label className="flex items-center gap-1.5 text-xs text-slate-500 mt-1 cursor-pointer"><input type="checkbox" checked={exp.is_current} onChange={e => updExp(exp.id, 'is_current', e.target.checked)} className="rounded" />Currently working here</label></div>
                </div>
                <div className="mt-3 flex flex-col gap-1"><label className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Description</label><textarea value={exp.description} onChange={e => updExp(exp.id, 'description', e.target.value)} rows={3} placeholder="Describe responsibilities…" className="px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm resize-none focus:outline-none focus:border-indigo-400" /></div>
              </div>
            ))}
          </div>
          <button onClick={addExp} className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/30 rounded-xl text-sm font-semibold text-slate-500 hover:text-indigo-600 transition"><Plus size={15} /> Add Experience</button>
        </SectionCard>

        <SectionCard title="Education" icon={GraduationCap}>
          <div className="space-y-5">
            {profile.education.map((edu: any) => (
              <div key={edu.id} className="p-4 bg-slate-50 rounded-xl border border-slate-200 relative group">
                <button onClick={() => setProfile(p => ({ ...p, education: p.education.filter((e: any) => e.id !== edu.id) }))} className="absolute top-3 right-3 w-7 h-7 flex items-center justify-center rounded-lg bg-red-50 text-red-400 hover:bg-red-100 transition opacity-0 group-hover:opacity-100"><Trash2 size={13} /></button>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {[['institution', 'Institution', 'MIT'], ['degree', 'Degree', "Bachelor's / Master's"], ['field', 'Field of Study', 'Computer Science']].map(([f, lbl, ph]) => (
                    <div key={f} className="flex flex-col gap-1"><label className="text-xs text-slate-500 font-semibold uppercase tracking-wider">{lbl}</label><input value={edu[f]} onChange={e => updEdu(edu.id, f, e.target.value)} placeholder={ph} className="px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm focus:outline-none focus:border-indigo-400" /></div>
                  ))}
                  <div className="flex flex-col gap-1"><label className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Years</label><div className="flex gap-2"><input type="month" value={edu.start_date} onChange={e => updEdu(edu.id, 'start_date', e.target.value)} className="flex-1 px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm focus:outline-none focus:border-indigo-400" /><input type="month" value={edu.end_date} onChange={e => updEdu(edu.id, 'end_date', e.target.value)} className="flex-1 px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm focus:outline-none focus:border-indigo-400" /></div></div>
                </div>
              </div>
            ))}
          </div>
          <button onClick={addEdu} className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/30 rounded-xl text-sm font-semibold text-slate-500 hover:text-indigo-600 transition"><Plus size={15} /> Add Education</button>
        </SectionCard>
      </div>

      <div className="fixed bottom-0 left-64 right-0 bg-white/90 backdrop-blur border-t border-slate-200 px-8 py-4 flex items-center justify-between z-40">
        <p className="text-sm text-slate-500">{saved ? <span className="flex items-center gap-1.5 text-emerald-600 font-semibold"><CheckCircle size={15} /> All changes saved</span> : 'Unsaved changes'}</p>
        <button onClick={saveProfile} disabled={saving} className="inline-flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-xl font-semibold text-sm shadow-md shadow-indigo-200 transition disabled:opacity-60">
          {saving ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />} {saving ? 'Saving…' : 'Save Changes'}
        </button>
      </div>
    </div>
  )
}
