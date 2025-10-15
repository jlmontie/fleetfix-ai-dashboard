// API Response Types

export interface QueryResponse {
  success: boolean
  query: string
  sql?: string
  explanation?: string
  results?: any[]
  columns?: string[]
  row_count?: number
  chart_config?: ChartConfig
  plotly_chart?: PlotlyChart
  insight?: string
  execution_time_ms?: number
  query_classification?: 'database' | 'document' | 'hybrid'
  rag_answer?: string
  citations?: string[]
  retrieved_docs?: RetrievedDocument[]
  error?: string
}

export interface ChartConfig {
  type: 'line' | 'bar' | 'grouped_bar' | 'scatter' | 'map' | 'metric' | 'table'
  reason?: string
  x_column?: string
  y_columns?: string[]
  title?: string
  confidence?: number
}

export interface PlotlyChart {
  data: any[]
  layout: any
  config?: any
}

export interface RetrievedDocument {
  content: string
  section: string
  source: string
  relevance_score: number
  citation_key: string
}

export interface DailyDigest {
  generated_at: string
  insights: Insight[]
}

export interface Insight {
  priority: 'high' | 'medium' | 'low'
  title: string
  description: string
  recommendation: string
  chart?: PlotlyChart
  affected_vehicles?: number[]
  estimated_cost?: string
}

export interface ExampleQuery {
  category: string
  queries: string[]
}

export interface MetricData {
  title: string
  value: string | number
  change?: number
  unit?: string
  icon?: string
  color?: 'green' | 'yellow' | 'red' | 'blue'
}

// Chat Message Types

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  queryResponse?: QueryResponse
}

// Component Props Types

export interface MetricCardProps {
  title: string
  value: string | number
  change?: number
  icon?: React.ReactNode
  color?: 'green' | 'yellow' | 'red' | 'blue'
  unit?: string
  loading?: boolean
}

export interface ChartProps {
  plotlyConfig: PlotlyChart
  isLoading?: boolean
  error?: string
  onRetry?: () => void
}

export interface ChatProps {
  messages: ChatMessage[]
  onSendMessage: (message: string) => void
  isLoading: boolean
  exampleQueries?: string[]
}

export interface DailyInsightsProps {
  insights: Insight[]
  isLoading: boolean
  onRefresh: () => void
  lastUpdated?: string
}

