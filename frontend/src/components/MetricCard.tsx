import { ArrowUp, ArrowDown, Minus, LucideIcon } from 'lucide-react'
import { cn, formatNumber, formatPercent } from '../lib/utils'
import type { MetricCardProps } from '../types'

export default function MetricCard({
  title,
  value,
  change,
  icon: Icon,
  color = 'blue',
  unit = '',
  loading = false,
}: MetricCardProps & { icon?: LucideIcon }) {
  const colorClasses = {
    green: 'bg-green-50 border-green-200 text-green-700',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-700',
    red: 'bg-red-50 border-red-200 text-red-700',
    blue: 'bg-blue-50 border-blue-200 text-blue-700',
  }

  const iconColorClasses = {
    green: 'text-green-600',
    yellow: 'text-yellow-600',
    red: 'text-red-600',
    blue: 'text-blue-600',
  }

  const getTrendColor = (value: number) => {
    if (value > 0) return 'text-green-600'
    if (value < 0) return 'text-red-600'
    return 'text-gray-600'
  }

  const getTrendIcon = (value: number) => {
    if (value > 0) return <ArrowUp size={16} />
    if (value < 0) return <ArrowDown size={16} />
    return <Minus size={16} />
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="h-5 w-32 skeleton rounded"></div>
          <div className="h-10 w-10 skeleton rounded-lg"></div>
        </div>
        <div className="h-8 w-24 skeleton rounded mb-2"></div>
        <div className="h-4 w-16 skeleton rounded"></div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        {Icon && (
          <div className={cn('p-2 rounded-lg', colorClasses[color])}>
            <Icon size={20} className={iconColorClasses[color]} />
          </div>
        )}
      </div>
      
      <div className="flex items-baseline gap-2 mb-2">
        <div className="text-3xl font-bold text-gray-900 metric-value">
          {typeof value === 'number' ? formatNumber(value, 1) : value}
          {unit && <span className="text-lg font-normal text-gray-500 ml-1">{unit}</span>}
        </div>
      </div>

      {change !== undefined && (
        <div className={cn('flex items-center gap-1 text-sm font-medium', getTrendColor(change))}>
          {getTrendIcon(change)}
          <span>{formatPercent(Math.abs(change))}</span>
          <span className="text-gray-500 font-normal">vs last week</span>
        </div>
      )}
    </div>
  )
}

