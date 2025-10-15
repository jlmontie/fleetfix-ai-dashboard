import { useState, useEffect } from 'react'
import Plot from 'react-plotly.js'
import { AlertCircle, RefreshCw } from 'lucide-react'
import type { ChartProps } from '../types'

export default function Chart({ plotlyConfig, isLoading, error, onRetry }: ChartProps) {
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="h-64 flex items-center justify-center">
          <div className="text-center">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-600 border-r-transparent"></div>
            <p className="mt-2 text-sm text-gray-500">Loading chart...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-red-200 p-6">
        <div className="flex items-center gap-2 text-red-600 mb-2">
          <AlertCircle size={20} />
          <h3 className="font-semibold">Chart Error</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">{error}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors text-sm"
          >
            <RefreshCw size={16} />
            Retry
          </button>
        )}
      </div>
    )
  }

  if (!plotlyConfig || !plotlyConfig.data) {
    return null
  }

  // Don't render Plotly on server-side
  if (!isClient) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="h-64 skeleton rounded"></div>
      </div>
    )
  }

  // Merge default layout settings
  const defaultLayout = {
    font: {
      family: 'Inter, system-ui, sans-serif',
      size: 12,
    },
    margin: { t: 40, r: 20, b: 40, l: 50 },
    paper_bgcolor: 'white',
    plot_bgcolor: '#f8fafc',
    hoverlabel: {
      bgcolor: 'white',
      bordercolor: '#e2e8f0',
      font: { size: 12 },
    },
    ...plotlyConfig.layout,
  }

  const defaultConfig = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    displaylogo: false,
    ...plotlyConfig.config,
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <Plot
        data={plotlyConfig.data}
        layout={defaultLayout}
        config={defaultConfig}
        className="w-full"
        style={{ width: '100%', height: '100%' }}
        useResizeHandler={true}
      />
    </div>
  )
}

