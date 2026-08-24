import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { useAuthStore } from './store/authStore'
import Layout from './components/Layout'

// Pages
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import CandidateDashboard from './pages/candidate/Dashboard'
import JobSwipe from './pages/candidate/JobSwipe'
import Applications from './pages/candidate/Applications'
import Credentials from './pages/candidate/Credentials'
import EmailInbox from './pages/candidate/EmailInbox'
import Messages from './pages/candidate/Messages'
import Profile from './pages/candidate/Profile'
import ResumeGenerator from './pages/candidate/ResumeGenerator'
import RecruiterDashboard from './pages/recruiter/Dashboard'

function App() {
  const { isAuthenticated, user } = useAuthStore()
  const [isInitialized, setIsInitialized] = useState(false)

  useEffect(() => {
    // App is initialized when auth store has loaded from localStorage
    setIsInitialized(true)
  }, [])

  if (!isInitialized) {
    return null // Don't render routes until auth state is loaded
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        
        {/* Candidate Routes */}
        <Route
          path="/candidate/dashboard"
          element={
            isAuthenticated && user?.role === 'CANDIDATE' ? (
              <Layout><CandidateDashboard /></Layout>
            ) : (
              <Navigate to="/login" />
            )
          }
        />
        <Route
          path="/candidate/swipe"
          element={
            isAuthenticated && user?.role === 'CANDIDATE' ? (
              <Layout><JobSwipe /></Layout>
            ) : (
              <Navigate to="/login" />
            )
          }
        />
        <Route
          path="/candidate/applications"
          element={
            isAuthenticated && user?.role === 'CANDIDATE' ? (
              <Layout><Applications /></Layout>
            ) : (
              <Navigate to="/login" />
            )
          }
        />
        <Route
          path="/candidate/credentials"
          element={
            isAuthenticated && user?.role === 'CANDIDATE' ? (
              <Layout><Credentials /></Layout>
            ) : (
              <Navigate to="/login" />
            )
          }
        />
        <Route
          path="/candidate/inbox"
          element={
            isAuthenticated && user?.role === 'CANDIDATE' ? (
              <Layout><EmailInbox /></Layout>
            ) : (
              <Navigate to="/login" />
            )
          }
        />
        <Route
          path="/candidate/messages"
          element={
            isAuthenticated && user?.role === 'CANDIDATE' ? (
              <Layout><Messages /></Layout>
            ) : (
              <Navigate to="/login" />
            )
          }
        />
        <Route
          path="/candidate/profile"
          element={
            isAuthenticated && user?.role === 'CANDIDATE' ? (
              <Layout><Profile /></Layout>
            ) : (
              <Navigate to="/login" />
            )
          }
        />
        <Route
          path="/candidate/resume"
          element={
            isAuthenticated && user?.role === 'CANDIDATE' ? (
              <Layout><ResumeGenerator /></Layout>
            ) : (
              <Navigate to="/login" />
            )
          }
        />
        
        {/* Recruiter Routes */}
        <Route
          path="/recruiter/dashboard"
          element={
            isAuthenticated && user?.role === 'RECRUITER' ? (
              <Layout><RecruiterDashboard /></Layout>
            ) : (
              <Navigate to="/login" />
            )
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
