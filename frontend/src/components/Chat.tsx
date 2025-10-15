import { useState, useRef, useEffect } from 'react'
import { Send, ChevronDown, ChevronUp, Database, FileText, Loader2, BookOpen } from 'lucide-react'
import { formatDate, cn } from '../lib/utils'
import Chart from './Chart'
import type { ChatProps, ChatMessage } from '../types'

export default function Chat({ messages, onSendMessage, isLoading, exampleQueries = [] }: ChatProps) {
  const [input, setInput] = useState('')
  const [expandedSQL, setExpandedSQL] = useState<Record<string, boolean>>({})
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Auto-focus input
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    onSendMessage(input.trim())
    setInput('')
  }

  const handleExampleClick = (query: string) => {
    if (isLoading) return
    onSendMessage(query)
  }

  const toggleSQL = (messageId: string) => {
    setExpandedSQL(prev => ({ ...prev, [messageId]: !prev[messageId] }))
  }

  const renderQueryClassificationBadge = (classification?: string) => {
    if (!classification) return null

    const badges = {
      database: { color: 'bg-blue-100 text-blue-700', icon: Database, label: 'Database Query' },
      document: { color: 'bg-purple-100 text-purple-700', icon: FileText, label: 'Document Query' },
      hybrid: { color: 'bg-indigo-100 text-indigo-700', icon: BookOpen, label: 'Hybrid Query' },
    }

    const badge = badges[classification as keyof typeof badges]
    if (!badge) return null

    const Icon = badge.icon

    return (
      <div className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${badge.color}`}>
        <Icon size={12} />
        {badge.label}
      </div>
    )
  }

  const renderCitations = (citations?: string[]) => {
    if (!citations || citations.length === 0) return null

    return (
      <div className="mt-3 pt-3 border-t border-gray-200">
        <p className="text-xs font-semibold text-gray-700 mb-1">Sources:</p>
        <ul className="text-xs text-gray-600 space-y-0.5">
          {citations.map((citation, idx) => (
            <li key={idx}>{citation}</li>
          ))}
        </ul>
      </div>
    )
  }

  const renderMessage = (message: ChatMessage) => {
    const isUser = message.role === 'user'

    return (
      <div
        key={message.id}
        className={cn(
          'flex gap-3',
          isUser ? 'justify-end' : 'justify-start'
        )}
      >
        {!isUser && (
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center text-white font-semibold text-sm">
            AI
          </div>
        )}

        <div className={cn('max-w-3xl', isUser ? 'order-first' : '')}>
          <div
            className={cn(
              'rounded-lg p-4',
              isUser
                ? 'bg-primary-600 text-white'
                : 'bg-white border border-gray-200'
            )}
          >
            {!isUser && message.queryResponse && (
              <div className="mb-2">
                {renderQueryClassificationBadge(message.queryResponse.query_classification)}
              </div>
            )}

            <p className={cn(
              'text-sm whitespace-pre-wrap',
              isUser ? 'text-white' : 'text-gray-900'
            )}>
              {message.content}
            </p>

            {/* RAG Answer */}
            {message.queryResponse?.rag_answer && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <p className="text-sm text-gray-900 whitespace-pre-wrap">
                  {message.queryResponse.rag_answer}
                </p>
                {renderCitations(message.queryResponse.citations)}
              </div>
            )}

            {/* SQL Query */}
            {message.queryResponse?.sql && (
              <div className="mt-3">
                <button
                  onClick={() => toggleSQL(message.id)}
                  className="flex items-center gap-2 text-xs font-medium text-primary-600 hover:text-primary-700"
                >
                  {expandedSQL[message.id] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  {expandedSQL[message.id] ? 'Hide' : 'Show'} SQL Query
                </button>
                {expandedSQL[message.id] && (
                  <pre className="mt-2 p-3 bg-gray-50 rounded text-xs font-mono overflow-x-auto">
                    <code>{message.queryResponse.sql}</code>
                  </pre>
                )}
              </div>
            )}

            {/* Chart */}
            {message.queryResponse?.plotly_chart && (
              <div className="mt-3">
                <Chart plotlyConfig={message.queryResponse.plotly_chart} />
              </div>
            )}

            {/* Results Summary */}
            {message.queryResponse?.row_count !== undefined && (
              <div className="mt-2 text-xs text-gray-500">
                {message.queryResponse.row_count} {message.queryResponse.row_count === 1 ? 'result' : 'results'}
                {message.queryResponse.execution_time_ms && (
                  <> • {message.queryResponse.execution_time_ms.toFixed(0)}ms</>
                )}
              </div>
            )}

            {/* Error */}
            {message.queryResponse?.error && (
              <div className="mt-2 text-sm text-red-600">
                Error: {message.queryResponse.error}
              </div>
            )}
          </div>

          <div className={cn(
            'mt-1 text-xs text-gray-500',
            isUser ? 'text-right' : 'text-left'
          )}>
            {formatDate(message.timestamp)}
          </div>
        </div>

        {isUser && (
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center text-gray-700 font-semibold text-sm">
            You
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col h-[600px]">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <span>💬</span> Ask FleetFix AI
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          Ask questions in plain English about your fleet
        </p>
      </div>

      {/* Example Queries */}
      {messages.length === 0 && exampleQueries.length > 0 && (
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <p className="text-xs font-medium text-gray-700 mb-2">Try these examples:</p>
          <div className="flex flex-wrap gap-2">
            {exampleQueries.slice(0, 4).map((query, idx) => (
              <button
                key={idx}
                onClick={() => handleExampleClick(query)}
                disabled={isLoading}
                className="px-3 py-1.5 bg-white text-sm text-gray-700 rounded-full border border-gray-300 hover:border-primary-500 hover:text-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {query}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
        {messages.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <p className="text-lg font-medium">No messages yet</p>
            <p className="text-sm">Start by asking a question about your fleet</p>
          </div>
        )}

        {messages.map(renderMessage)}

        {isLoading && (
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center text-white font-semibold text-sm">
              AI
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-2 text-gray-600">
                <Loader2 size={16} className="animate-spin" />
                <span className="text-sm">Thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSubmit(e)
              }
            }}
            placeholder="Ask a question... (Shift+Enter for new line)"
            disabled={isLoading}
            rows={1}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <Send size={18} />
            <span className="hidden sm:inline">Send</span>
          </button>
        </div>
      </form>
    </div>
  )
}

