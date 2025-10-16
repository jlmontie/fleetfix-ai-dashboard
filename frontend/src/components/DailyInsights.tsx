import { RefreshCw, AlertCircle, AlertTriangle, Info, Zap } from 'lucide-react'
import { formatRelativeTime } from '../lib/utils'
import Chart from './Chart'
import type { DailyInsightsProps } from '../types'

export default function DailyInsights({ insights, isLoading, onRefresh, lastUpdated }: DailyInsightsProps) {
  const priorityConfig = {
    high: {
      icon: AlertCircle,
      color: 'red',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      textColor: 'text-red-700',
      badgeColor: 'bg-red-100 text-red-700',
    },
    medium: {
      icon: AlertTriangle,
      color: 'yellow',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      textColor: 'text-yellow-700',
      badgeColor: 'bg-yellow-100 text-yellow-700',
    },
    low: {
      icon: Info,
      color: 'blue',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      textColor: 'text-blue-700',
      badgeColor: 'bg-blue-100 text-blue-700',
    },
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <Zap className="text-primary-600" size={24} />
            <h2 className="text-xl font-bold text-gray-900">Today's Highlights</h2>
          </div>
          <div className="h-8 w-8 skeleton rounded"></div>
        </div>
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div key={i} className="p-4 border border-gray-200 rounded-lg">
              <div className="h-6 w-3/4 skeleton rounded mb-2"></div>
              <div className="h-4 w-full skeleton rounded mb-2"></div>
              <div className="h-4 w-5/6 skeleton rounded"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl shadow-xl border border-gray-200/50 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Zap className="text-primary-600" size={24} />
          <h2 className="text-xl font-bold text-gray-900">Today's Highlights</h2>
          {lastUpdated && (
            <span className="text-sm text-gray-500">
              • Updated {formatRelativeTime(lastUpdated)}
            </span>
          )}
        </div>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
          aria-label="Refresh insights"
        >
          <RefreshCw size={20} className={isLoading ? 'animate-spin' : ''} />
        </button>
      </div>

      {insights.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Info size={48} className="mx-auto mb-3 text-gray-400" />
          <p className="text-lg font-medium">No insights available</p>
          <p className="text-sm">Everything is running smoothly!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {insights.map((insight, index) => {
            const config = priorityConfig[insight.priority]
            const Icon = config.icon

            return (
              <div
                key={index}
                className={`p-4 border rounded-lg ${config.borderColor} ${config.bgColor}`}
              >
                <div className="flex items-start gap-3 mb-3">
                  <Icon size={20} className={config.textColor} />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-2 py-0.5 text-xs font-semibold rounded ${config.badgeColor}`}>
                        {insight.priority.toUpperCase()}
                      </span>
                      <h3 className="text-base font-semibold text-gray-900">
                        {insight.title}
                      </h3>
                    </div>
                    <p className="text-sm text-gray-700 mb-2">{insight.description}</p>
                    
                    <div className="bg-white p-3 rounded border border-gray-200 mb-3">
                      <p className="text-sm font-medium text-gray-900 mb-1">
                        Recommended Action:
                      </p>
                      <p className="text-sm text-gray-700">{insight.recommendation}</p>
                      {insight.estimated_cost && (
                        <p className="text-sm text-gray-600 mt-1">
                          Est. Cost: <span className="font-medium">{insight.estimated_cost}</span>
                        </p>
                      )}
                    </div>

                    {insight.chart && (
                      <div className="mt-3">
                        <Chart plotlyConfig={insight.chart} />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

