export default function RecruiterDashboard() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Recruiter Dashboard</h1>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="font-semibold mb-2">Active Jobs</h3>
            <p className="text-3xl font-bold text-blue-600">8</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="font-semibold mb-2">Candidates</h3>
            <p className="text-3xl font-bold text-green-600">24</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="font-semibold mb-2">Matches</h3>
            <p className="text-3xl font-bold text-purple-600">7</p>
          </div>
        </div>
      </div>
    </div>
  )
}