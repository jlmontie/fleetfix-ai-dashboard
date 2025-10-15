import axios, { AxiosInstance, AxiosError } from 'axios'
import type { QueryResponse, DailyDigest, ExampleQuery } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000, // 30 seconds
    })

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        console.error('API Error:', error)
        
        if (error.response) {
          // Server responded with error status
          throw new Error(
            error.response.data?.error || 
            error.response.data?.detail ||
            `Server error: ${error.response.status}`
          )
        } else if (error.request) {
          // Request made but no response
          throw new Error('No response from server. Please check your connection.')
        } else {
          // Error setting up request
          throw new Error('Failed to send request to server.')
        }
      }
    )
  }

  /**
   * Execute a natural language query
   */
  async executeQuery(query: string, conversationHistory?: string[]): Promise<QueryResponse> {
    try {
      const response = await this.client.post<QueryResponse>('/api/query', {
        query,
        conversation_history: conversationHistory,
      })
      return response.data
    } catch (error) {
      console.error('Query execution error:', error)
      throw error
    }
  }

  /**
   * Get daily digest with adaptive insights
   */
  async getDailyDigest(forceRefresh: boolean = false): Promise<DailyDigest> {
    try {
      const response = await this.client.get<DailyDigest>('/api/daily-digest', {
        params: { force_refresh: forceRefresh },
      })
      return response.data
    } catch (error) {
      console.error('Daily digest error:', error)
      throw error
    }
  }

  /**
   * Get example queries grouped by category
   */
  async getExamples(): Promise<ExampleQuery[]> {
    try {
      const response = await this.client.get<{ examples: ExampleQuery[] }>('/api/examples')
      return response.data.examples
    } catch (error) {
      console.error('Examples fetch error:', error)
      throw error
    }
  }

  /**
   * Get database schema information
   */
  async getSchema(): Promise<any> {
    try {
      const response = await this.client.get('/api/schema')
      return response.data
    } catch (error) {
      console.error('Schema fetch error:', error)
      throw error
    }
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string }> {
    try {
      const response = await this.client.get('/health')
      return response.data
    } catch (error) {
      console.error('Health check error:', error)
      throw error
    }
  }

  /**
   * Get key metrics for dashboard
   */
  async getKeyMetrics(): Promise<any> {
    try {
      // Execute predefined queries for key metrics
      const queries = [
        'SELECT COUNT(*) as total_vehicles FROM vehicles',
        'SELECT AVG(score) as avg_driver_score FROM driver_performance WHERE date >= CURRENT_DATE - INTERVAL \'7 days\'',
        'SELECT COUNT(*) as active_fault_codes FROM fault_codes WHERE resolved = false',
      ]

      const results = await Promise.allSettled(
        queries.map(query => this.client.post('/api/query', { query }))
      )

      return results.map(result => 
        result.status === 'fulfilled' ? result.value.data : null
      )
    } catch (error) {
      console.error('Key metrics error:', error)
      throw error
    }
  }
}

// Export singleton instance
export const apiClient = new APIClient()

// Export types for convenience
export type { QueryResponse, DailyDigest, ExampleQuery }

