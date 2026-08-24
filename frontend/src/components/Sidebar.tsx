import { NavLink } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { 
  LayoutDashboard, 
  Layers, 
  Briefcase, 
  Key, 
  Mail, 
  MessageSquare,
  FileText,
  LogOut,
  UserCircle
} from 'lucide-react'

export default function Sidebar() {
  const { user, logout } = useAuthStore()

  const candidateLinks = [
    { to: '/candidate/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/candidate/profile', icon: UserCircle, label: 'Profile' },
    { to: '/candidate/swipe', icon: Layers, label: 'Job Swipe' },
    { to: '/candidate/applications', icon: Briefcase, label: 'Applications' },
    { to: '/candidate/credentials', icon: Key, label: 'Credentials' },
    { to: '/candidate/resume', icon: FileText, label: 'AI Resume Generator' },
    { to: '/candidate/inbox', icon: Mail, label: 'Inbox' },
    { to: '/candidate/messages', icon: MessageSquare, label: 'Messages' },
  ]

  const recruiterLinks = [
    { to: '/recruiter/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    // more recruiter links could go here
  ]

  const links = user?.role === 'CANDIDATE' ? candidateLinks : recruiterLinks

  return (
    <aside className="w-64 h-screen fixed left-0 top-0 glass border-r border-white/40 flex flex-col z-50">
      <div className="p-8">
        <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-pink-500 tracking-tight">
          Swiply
        </h1>
        <p className="text-sm text-gray-500 font-medium mt-1">
          {user?.role === 'CANDIDATE' ? 'Candidate Portal' : 'Recruiter Portal'}
        </p>
      </div>

      <nav className="flex-1 px-4 space-y-2 overflow-y-auto">
        {links.map((link) => {
          const Icon = link.icon
          return (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? 'active' : ''}`
              }
            >
              <Icon size={20} />
              <span>{link.label}</span>
            </NavLink>
          )
        })}
      </nav>

      <div className="p-4 mt-auto">
        <button
          onClick={() => {
            logout()
            window.location.href = '/login'
          }}
          className="w-full sidebar-link text-red-500 hover:text-red-600 hover:bg-red-50"
        >
          <LogOut size={20} />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  )
}
