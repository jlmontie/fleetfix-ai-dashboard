import { useState, useEffect } from 'react'
import { 
  Truck, Gauge, Wrench, Users, Activity, AlertTriangle, Clock, TrendingUp 
} from 'lucide-react'
import MetricCard from './MetricCard'
import Chat from './Chat'
import DailyInsights from './DailyInsights'
import { apiClient } from '../api/client'
import type { ChatMessage, Insight } from '../types'

export default function Dashboard() {
  // State
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoadingQuery, setIsLoadingQuery] = useState(false)
  const [insights, setInsights] = useState<Insight[]>([])
  const [isLoadingInsights, setIsLoadingInsights] = useState(false)
  const [lastInsightsUpdate, setLastInsightsUpdate] = useState<string>('')
  const [exampleQueries, setExampleQueries] = useState<string[]>([])

  // Key metrics state (simplified for now - will be populated by API)
  const [keyMetrics] = useState([
    { title: 'Fleet Utilization', value: '247', unit: 'mi/day', change: 3.2, icon: Truck, color: 'blue' as const },
    { title: 'Fuel Efficiency', value: '18.2', unit: 'MPG', change: -0.8, icon: Gauge, color: 'green' as const },
    { title: 'Maintenance Compliance', value: '94', unit: '%', change: -2.0, icon: Wrench, color: 'yellow' as const },
    { title: 'Avg Driver Score', value: '87', unit: '/100', change: 1.5, icon: Users, color: 'blue' as const },
    { title: 'Vehicle Health', value: '24/30', unit: 'healthy', change: undefined, icon: Activity, color: 'green' as const },
    { title: 'Active Fault Codes', value: '7', unit: 'codes', change: undefined, icon: AlertTriangle, color: 'red' as const },
    { title: 'Downtime Today', value: '3.2', unit: 'hrs', change: -12.0, icon: Clock, color: 'green' as const },
    { title: 'Route Efficiency', value: '96.3', unit: '%', change: 0.5, icon: TrendingUp, color: 'blue' as const },
  ])

  // Load daily digest on mount
  useEffect(() => {
    loadDailyDigest()
    loadExampleQueries()
  }, [])

  const loadDailyDigest = async (forceRefresh: boolean = false) => {
    setIsLoadingInsights(true)
    try {
      const digest = await apiClient.getDailyDigest(forceRefresh)
      setInsights(digest.insights)
      setLastInsightsUpdate(digest.generated_at)
    } catch (error) {
      console.error('Failed to load daily digest:', error)
      // Set empty insights on error
      setInsights([])
    } finally {
      setIsLoadingInsights(false)
    }
  }

  const loadExampleQueries = async () => {
    try {
      const examples = await apiClient.getExamples()
      // Flatten and take first few queries from each category
      const allQueries = examples.flatMap(cat => cat.queries).slice(0, 10)
      setExampleQueries(allQueries)
    } catch (error) {
      console.error('Failed to load example queries:', error)
      // Set default examples
      setExampleQueries([
        'Show me vehicles overdue for maintenance',
        'Which drivers had harsh braking events this week?',
        'What is fault code P0420?',
        'Show vehicles with high mileage',
      ])
    }
  }

  const handleSendMessage = async (query: string) => {
    // Add user message
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMessage])
    setIsLoadingQuery(true)

    try {
      // Get conversation history (last 5 messages)
      const history = messages
        .slice(-5)
        .map(m => `${m.role}: ${m.content}`)

      const response = await apiClient.executeQuery(query, history)

      // Generate assistant message content
      let assistantContent = ''
      
      if (response.query_classification === 'document') {
        // Document query - show RAG answer
        assistantContent = response.rag_answer || 'Here is what I found in the documentation.'
      } else if (response.query_classification === 'hybrid') {
        // Hybrid query - combine database results with RAG
        assistantContent = response.rag_answer || `Found ${response.row_count || 0} results.`
      } else {
        // Database query - show insight or explanation
        assistantContent = response.insight || response.explanation || `Found ${response.row_count || 0} results.`
      }

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: assistantContent,
        timestamp: new Date(),
        queryResponse: response,
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error: any) {
      // Add error message
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error.message || 'Unknown error'}`,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoadingQuery(false)
    }
  }

  const handleRefreshInsights = () => {
    loadDailyDigest(true)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-[1920px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                FleetFix AI Dashboard
              </h1>
              <p className="text-sm text-gray-600 mt-0.5">
                Adaptive intelligence for your fleet
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-sm text-gray-600">
                {new Date().toLocaleDateString('en-US', { 
                  weekday: 'long', 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-[1920px] mx-auto px-6 py-6 space-y-6">
        {/* Today's Highlights Section */}
        <section>
          <DailyInsights
            insights={insights}
            isLoading={isLoadingInsights}
            onRefresh={handleRefreshInsights}
            lastUpdated={lastInsightsUpdate}
          />
        </section>

        {/* Key Metrics Grid */}
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Key Metrics</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {keyMetrics.map((metric, index) => (
              <MetricCard
                key={index}
                title={metric.title}
                value={metric.value}
                unit={metric.unit}
                change={metric.change}
                icon={metric.icon}
                color={metric.color}
              />
            ))}
          </div>
        </section>

        {/* Chat Interface */}
        <section>
          <Chat
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={isLoadingQuery}
            exampleQueries={exampleQueries}
          />
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-[1920px] mx-auto px-6 py-4 text-center text-sm text-gray-600">
          FleetFix AI Dashboard • Built with React, TypeScript, and Claude AI
        </div>
      </footer>
    </div>
  )
}

