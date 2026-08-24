import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const API_BASE_URL = ((import.meta as any).env?.VITE_API_URL) || 'http://localhost:8000'

// Service endpoints
export const SERVICES = {
  AUTH: `http://localhost:8001`,
  AI: `http://localhost:8010`,
  USER: `${API_BASE_URL}/user`,
  JOB: `http://localhost:8003`,
  PROFILE: `http://localhost:8004`,
  MATCH: `${API_BASE_URL}/match`,
  APPLICATION: `http://localhost:8003`,
  CREDENTIAL: `http://localhost:8009`,
  EMAIL: `http://localhost:8007`,
  CHAT: `${API_BASE_URL}/chat`,
}

// Create axios instance
export const api = axios.create({
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API methods
export const authAPI = {
  register: (data: FormData) =>
    api.post(`${SERVICES.AUTH}/register`, data, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 30000, // 30 seconds for registration
    }),
  
  login: (email: string, password: string) => {
    console.log('Calling login API:', `${SERVICES.AUTH}/login`)
    return api.post(`${SERVICES.AUTH}/login`, { email, password })
  },
  
  logout: () => api.post(`${SERVICES.AUTH}/logout`),
  
  me: () => api.get(`${SERVICES.AUTH}/me`),
  
  getAutomationStatus: (userId: string) => 
    api.get(`${SERVICES.AUTH}/automation-status/${userId}`),
}

export const aiAPI = {
  enhanceProfile: (profileData: any) => 
    api.post(`${SERVICES.AI}/enhance-profile`, profileData),
  
  generateResume: (profileData: any) => 
    api.post(`${SERVICES.AI}/generate-resume`, profileData),
  
  generateCoverLetter: (profileData: any, jobData: any) => 
    api.post(`${SERVICES.AI}/generate-cover-letter`, { profile: profileData, job: jobData }),
  
  generateProfileSections: (profileData: any) => 
    api.post(`${SERVICES.AI}/generate-profile-sections`, profileData),
  
  optimizeForATS: (profileData: any, jobData: any) => 
    api.post(`${SERVICES.AI}/optimize-for-ats`, { profile: profileData, job: jobData }),
}

export const credentialAPI = {
  getAll: () => api.get(`${SERVICES.CREDENTIAL}/credentials`),
  
  getStats: () => api.get(`${SERVICES.CREDENTIAL}/credentials/stats`),
  
  getForSite: (site: string) =>
    api.get(`${SERVICES.CREDENTIAL}/credentials/${site}`),
  
  create: (site: string) =>
    api.post(`${SERVICES.CREDENTIAL}/credentials/${site}`),
  
  delete: (id: string) =>
    api.delete(`${SERVICES.CREDENTIAL}/credentials/${id}`),
}

export const emailAPI = {
  getAll: (params?: { isRead?: boolean; category?: string; limit?: number; offset?: number }) =>
    api.get(`${SERVICES.EMAIL}/emails`, { params }),
  
  getStats: () => api.get(`${SERVICES.EMAIL}/emails/stats`),
  
  getById: (id: string) => api.get(`${SERVICES.EMAIL}/emails/${id}`),
  
  markAsRead: (id: string) => api.patch(`${SERVICES.EMAIL}/emails/${id}/read`),
  
  markAsUnread: (id: string) => api.patch(`${SERVICES.EMAIL}/emails/${id}/unread`),
  
  toggleStar: (id: string) => api.patch(`${SERVICES.EMAIL}/emails/${id}/star`),
  
  delete: (id: string) => api.delete(`${SERVICES.EMAIL}/emails/${id}`),
}

export const jobAPI = {
  getAll: (params?: { limit?: number; offset?: number }) =>
    api.get(`${SERVICES.JOB}/`, { params }),
  
  getById: (id: string) => api.get(`${SERVICES.JOB}/jobs/${id}`),
  
  swipe: (jobId: string, liked: boolean) =>
    api.post(`${SERVICES.JOB}/jobs/${jobId}/swipe`, { liked }),
  
  getRecommendations: (candidateId?: string) => api.get(`${SERVICES.JOB}/recommendations`, { params: { candidate_id: candidateId } }),
}

export const applicationAPI = {
  getAll: () => api.get(`${SERVICES.APPLICATION}/applications`),
  
  getById: (id: string) => api.get(`${SERVICES.APPLICATION}/applications/${id}`),
  
  create: (data: any) =>
    api.post(`${SERVICES.APPLICATION}/applications`, data),
  
  getStats: () => api.get(`${SERVICES.APPLICATION}/applications/stats`),
}

export const profileAPI = {
  analyzeCV: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`${SERVICES.PROFILE}/analyze-cv`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
  
  getProfile: (candidateId: string) => 
    api.get(`${SERVICES.PROFILE}/candidate-profile/${candidateId}`),
  
  calculateMatch: (data: { candidate: any; job: any }) =>
    api.post(`${SERVICES.PROFILE}/calculate-match`, data),
}
