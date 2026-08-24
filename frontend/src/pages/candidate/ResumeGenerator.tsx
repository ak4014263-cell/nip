import { useState } from 'react'
import { FileText, Download, Sparkles, User, Briefcase, GraduationCap, Award, Loader2, Upload, FileCheck } from 'lucide-react'
import { aiAPI } from '../../services/api'

export default function ResumeGenerator() {
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    location: '',
    linkedin_url: '',
    experience_years: '',
    skills: '',
    bio: '',
    education: '',
    current_role: '',
    career_goals: ''
  })
  const [generatedResume, setGeneratedResume] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [uploadedResume, setUploadedResume] = useState<any>(null)
  const [uploading, setUploading] = useState(false)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.name.match(/\.(pdf|docx|txt)$/)) {
      alert('Please upload a PDF, DOCX, or TXT file')
      return
    }

    setUploading(true)
    try {
      const formDataUpload = new FormData()
      formDataUpload.append('file', file)

      const response = await fetch('http://localhost:8010/analyze-resume', {
        method: 'POST',
        body: formDataUpload
      })

      const result = await response.json()
      
      if (result.success) {
        setUploadedResume(result)
        
        // Auto-fill form with extracted data
        const analysis = result.analysis
        if (analysis.personal_info) {
          setFormData(prev => ({
            ...prev,
            first_name: analysis.personal_info.first_name || prev.first_name,
            last_name: analysis.personal_info.last_name || prev.last_name,
            email: analysis.personal_info.email || prev.email,
            phone: analysis.personal_info.phone || prev.phone,
            location: analysis.personal_info.location || prev.location,
            linkedin_url: analysis.personal_info.linkedin_url || prev.linkedin_url
          }))
        }
        
        if (analysis.skills) {
          setFormData(prev => ({
            ...prev,
            skills: analysis.skills.join(', ')
          }))
        }
        
        if (analysis.experience_years) {
          setFormData(prev => ({
            ...prev,
            experience_years: analysis.experience_years.toString()
          }))
        }
        
        if (analysis.professional_summary) {
          setFormData(prev => ({
            ...prev,
            bio: analysis.professional_summary
          }))
        }
        
        if (analysis.education) {
          setFormData(prev => ({
            ...prev,
            education: analysis.education
          }))
        }
        
        alert('Resume analyzed successfully! Form has been pre-filled with extracted information.')
      } else {
        alert('Failed to analyze resume: ' + (result.error || 'Unknown error'))
      }
    } catch (error) {
      console.error('Resume upload failed:', error)
      alert('Resume upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const generateResume = async () => {
    if (!formData.first_name || !formData.last_name || !formData.email) {
      alert('Please fill in at least your name and email')
      return
    }

    setLoading(true)
    try {
      const skillsArray = formData.skills.split(',').map(skill => skill.trim()).filter(skill => skill)
      
      const profileData = {
        ...formData,
        skills: skillsArray,
        experience_years: parseInt(formData.experience_years) || 0
      }

      const response = await aiAPI.generateResume(profileData)
      
      if (response.data.success) {
        setGeneratedResume(response.data.resume)
      } else {
        alert('Resume generation failed. Please try again.')
      }
    } catch (error) {
      console.error('Resume generation failed:', error)
      alert('Resume generation failed. Please check your connection and try again.')
    } finally {
      setLoading(false)
    }
  }

  const downloadResume = () => {
    if (!generatedResume) return
    
    const resumeText = formatResumeForDownload(generatedResume)
    const blob = new Blob([resumeText], { type: 'text/plain' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${formData.first_name}_${formData.last_name}_Resume.txt`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  }

  const formatResumeForDownload = (resume: any) => {
    let formatted = `${resume.contact_info?.name || `${formData.first_name} ${formData.last_name}`}\n`
    formatted += `${resume.contact_info?.email || formData.email}\n`
    formatted += `${resume.contact_info?.phone || formData.phone}\n`
    formatted += `${resume.contact_info?.location || formData.location}\n\n`
    
    formatted += `PROFESSIONAL SUMMARY\n${resume.professional_summary}\n\n`
    
    if (resume.technical_skills) {
      formatted += `TECHNICAL SKILLS\n`
      Object.entries(resume.technical_skills).forEach(([category, skills]: [string, any]) => {
        formatted += `${category}: ${Array.isArray(skills) ? skills.join(', ') : skills}\n`
      })
      formatted += `\n`
    }
    
    if (resume.work_experience && Array.isArray(resume.work_experience)) {
      formatted += `WORK EXPERIENCE\n`
      resume.work_experience.forEach((exp: any) => {
        formatted += `${exp.title} - ${exp.company} (${exp.duration})\n`
        if (exp.achievements && Array.isArray(exp.achievements)) {
          exp.achievements.forEach((achievement: string) => {
            formatted += `• ${achievement}\n`
          })
        }
        formatted += `\n`
      })
    }
    
    if (resume.education) {
      formatted += `EDUCATION\n${resume.education}\n\n`
    }
    
    if (resume.projects && Array.isArray(resume.projects)) {
      formatted += `KEY PROJECTS\n`
      resume.projects.forEach((project: any) => {
        formatted += `• ${project.name || project.title}: ${project.description}\n`
      })
      formatted += `\n`
    }
    
    if (resume.certifications && Array.isArray(resume.certifications)) {
      formatted += `CERTIFICATIONS\n`
      resume.certifications.forEach((cert: string) => {
        formatted += `• ${cert}\n`
      })
    }
    
    return formatted
  }

  return (
    <div className="animate-fade-in max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight flex items-center gap-3">
            <Sparkles className="text-indigo-600" />
            AI Resume Generator
          </h1>
          <p className="text-gray-500 mt-1">Create a professional, ATS-optimized resume using OpenAI</p>
        </div>
        {generatedResume && (
          <button
            onClick={downloadResume}
            className="btn-primary flex items-center gap-2"
          >
            <Download size={20} />
            Download Resume
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Form */}
        <div className="glass-panel p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            <User size={24} />
            Your Information
          </h2>
          
          {/* Resume Upload Section */}
          <div className="mb-8 bg-blue-50 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-blue-800 mb-4 flex items-center gap-2">
              <Upload size={20} />
              Quick Start: Upload Your Resume
            </h3>
            <p className="text-blue-700 text-sm mb-4">
              Upload your existing resume and our AI will extract information to pre-fill the form below.
            </p>
            
            <div className="flex items-center gap-4">
              <input
                type="file"
                id="resume-upload"
                accept=".pdf,.docx,.txt"
                onChange={handleResumeUpload}
                disabled={uploading}
                className="hidden"
              />
              <label
                htmlFor="resume-upload"
                className={`
                  inline-flex items-center gap-2 px-4 py-2 rounded-lg border-2 border-dashed 
                  ${uploading 
                    ? 'border-gray-300 bg-gray-100 cursor-not-allowed' 
                    : 'border-blue-300 bg-blue-50 hover:bg-blue-100 cursor-pointer'
                  } transition-colors
                `}
              >
                {uploading ? (
                  <>
                    <Loader2 className="animate-spin" size={20} />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Upload size={20} />
                    Upload Resume (PDF, DOCX, TXT)
                  </>
                )}
              </label>
              
              {uploadedResume && (
                <div className="flex items-center gap-2 text-green-600">
                  <FileCheck size={20} />
                  <span className="text-sm font-medium">
                    {uploadedResume.filename} analyzed successfully!
                  </span>
                </div>
              )}
            </div>
            
            {uploadedResume && (
              <div className="mt-4 text-xs text-blue-600">
                ✨ Extracted: {uploadedResume.analysis?.skills?.length || 0} skills, 
                {uploadedResume.analysis?.experience_years || 0} years experience, 
                {uploadedResume.analysis?.work_experience?.length || 0} work entries
              </div>
            )}
          </div>
          
          <div className="space-y-6">
            {/* Personal Info */}
            <div className="bg-white/50 rounded-xl p-4">
              <h3 className="font-semibold text-gray-800 mb-3">Personal Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <input
                  type="text"
                  name="first_name"
                  placeholder="First Name *"
                  value={formData.first_name}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500"
                  required
                />
                <input
                  type="text"
                  name="last_name"
                  placeholder="Last Name *"
                  value={formData.last_name}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500"
                  required
                />
                <input
                  type="email"
                  name="email"
                  placeholder="Email *"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500"
                  required
                />
                <input
                  type="tel"
                  name="phone"
                  placeholder="Phone Number"
                  value={formData.phone}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500"
                />
                <input
                  type="text"
                  name="location"
                  placeholder="Location (City, Country)"
                  value={formData.location}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500"
                />
                <input
                  type="url"
                  name="linkedin_url"
                  placeholder="LinkedIn Profile URL"
                  value={formData.linkedin_url}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            {/* Professional Info */}
            <div className="bg-white/50 rounded-xl p-4">
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <Briefcase size={18} />
                Professional Information
              </h3>
              <div className="space-y-4">
                <input
                  type="text"
                  name="current_role"
                  placeholder="Current/Target Job Title"
                  value={formData.current_role}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500"
                />
                <input
                  type="number"
                  name="experience_years"
                  placeholder="Years of Experience"
                  value={formData.experience_years}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500"
                  min="0"
                  max="50"
                />
                <input
                  type="text"
                  name="skills"
                  placeholder="Skills (comma-separated: React, Python, AWS, etc.)"
                  value={formData.skills}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500"
                />
                <textarea
                  name="bio"
                  placeholder="Brief professional summary or bio..."
                  value={formData.bio}
                  onChange={handleInputChange}
                  rows={3}
                  className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            {/* Education & Goals */}
            <div className="bg-white/50 rounded-xl p-4">
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <GraduationCap size={18} />
                Education & Goals
              </h3>
              <div className="space-y-4">
                <input
                  type="text"
                  name="education"
                  placeholder="Education (e.g., Bachelor's in Computer Science, University of Paris)"
                  value={formData.education}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500"
                />
                <textarea
                  name="career_goals"
                  placeholder="Career goals and aspirations..."
                  value={formData.career_goals}
                  onChange={handleInputChange}
                  rows={2}
                  className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <button
              onClick={generateResume}
              disabled={loading || !formData.first_name || !formData.last_name}
              className="w-full btn-primary py-4 text-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
            >
              {loading ? (
                <>
                  <Loader2 className="animate-spin" size={24} />
                  Generating AI Resume...
                </>
              ) : (
                <>
                  <Sparkles size={24} />
                  Generate Resume with AI
                </>
              )}
            </button>
          </div>
        </div>

        {/* Generated Resume Preview */}
        <div className="glass-panel p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            <FileText size={24} />
            Generated Resume Preview
          </h2>
          
          {loading && (
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <Loader2 className="animate-spin text-indigo-500 w-12 h-12 mx-auto mb-4" />
                <p className="text-gray-600">AI is crafting your professional resume...</p>
              </div>
            </div>
          )}

          {!loading && !generatedResume && (
            <div className="flex items-center justify-center py-20">
              <div className="text-center text-gray-500">
                <FileText size={48} className="mx-auto mb-4 opacity-50" />
                <p>Fill in your information and click "Generate Resume with AI" to see your professional resume here.</p>
              </div>
            </div>
          )}

          {generatedResume && (
            <div className="bg-white rounded-lg p-6 shadow-sm border max-h-96 overflow-y-auto">
              <div className="space-y-4">
                {/* Header */}
                <div className="border-b pb-4">
                  <h1 className="text-2xl font-bold text-gray-900">
                    {generatedResume.contact_info?.name || `${formData.first_name} ${formData.last_name}`}
                  </h1>
                  <div className="text-sm text-gray-600 mt-2">
                    <p>{generatedResume.contact_info?.email || formData.email}</p>
                    <p>{generatedResume.contact_info?.phone || formData.phone}</p>
                    <p>{generatedResume.contact_info?.location || formData.location}</p>
                  </div>
                </div>

                {/* Professional Summary */}
                {generatedResume.professional_summary && (
                  <div>
                    <h2 className="text-lg font-semibold text-gray-800 mb-2">Professional Summary</h2>
                    <p className="text-gray-700 text-sm leading-relaxed">{generatedResume.professional_summary}</p>
                  </div>
                )}

                {/* Technical Skills */}
                {generatedResume.technical_skills && (
                  <div>
                    <h2 className="text-lg font-semibold text-gray-800 mb-2">Technical Skills</h2>
                    <div className="text-sm space-y-1">
                      {Object.entries(generatedResume.technical_skills).map(([category, skills]: [string, any]) => (
                        <div key={category}>
                          <span className="font-medium text-gray-800">{category}:</span>{' '}
                          <span className="text-gray-700">{Array.isArray(skills) ? (skills as string[]).join(', ') : String(skills)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Work Experience */}
                {generatedResume.work_experience && Array.isArray(generatedResume.work_experience) && (
                  <div>
                    <h2 className="text-lg font-semibold text-gray-800 mb-2">Work Experience</h2>
                    <div className="space-y-3">
                      {generatedResume.work_experience.map((exp: any, index: number) => (
                        <div key={index} className="border-l-2 border-indigo-200 pl-4">
                          <h3 className="font-medium text-gray-900">{exp.title} - {exp.company}</h3>
                          <p className="text-xs text-gray-500 mb-2">{exp.duration}</p>
                          {exp.achievements && Array.isArray(exp.achievements) && (
                            <ul className="text-sm text-gray-700 space-y-1">
                              {exp.achievements.map((achievement: string, i: number) => (
                                <li key={i} className="flex items-start gap-2">
                                  <span className="text-indigo-500 mt-1">•</span>
                                  <span>{achievement}</span>
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Projects */}
                {generatedResume.projects && Array.isArray(generatedResume.projects) && (
                  <div>
                    <h2 className="text-lg font-semibold text-gray-800 mb-2">Key Projects</h2>
                    <ul className="text-sm text-gray-700 space-y-1">
                      {generatedResume.projects.map((project: any, index: number) => (
                        <li key={index} className="flex items-start gap-2">
                          <span className="text-indigo-500 mt-1">•</span>
                          <span><strong>{project.name || project.title}:</strong> {project.description}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="mt-8 bg-blue-50 rounded-xl p-6">
        <h3 className="text-lg font-bold text-blue-800 mb-2 flex items-center gap-2">
          <Award size={20} />
          AI-Powered Features
        </h3>
        <ul className="text-blue-700 text-sm space-y-1">
          <li>✨ Professional summary optimized for your field</li>
          <li>🎯 ATS-friendly formatting and keywords</li>
          <li>💼 Industry-specific work experience examples</li>
          <li>🚀 Skills organized by category and relevance</li>
          <li>📝 Achievement-focused bullet points with metrics</li>
          <li>🏆 Tailored certifications and project suggestions</li>
        </ul>
      </div>
    </div>
  )
}