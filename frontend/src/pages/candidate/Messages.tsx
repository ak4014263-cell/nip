import { MessageCircle } from 'lucide-react'

export default function Messages() {
  return (
    <div className="animate-fade-in max-w-5xl mx-auto h-full flex flex-col items-center justify-center py-20">
      <div className="glass-panel p-12 text-center max-w-md">
        <div className="w-20 h-20 bg-indigo-50 rounded-full flex items-center justify-center mx-auto mb-6">
          <MessageCircle size={40} className="text-indigo-500" />
        </div>
        <h2 className="text-2xl font-bold mb-3 text-gray-900">No Messages Yet</h2>
        <p className="text-gray-500 leading-relaxed mb-8">
          When recruiters match with your profile and want to connect, their messages will appear here. Keep swiping to increase your chances!
        </p>
      </div>
    </div>
  )
}