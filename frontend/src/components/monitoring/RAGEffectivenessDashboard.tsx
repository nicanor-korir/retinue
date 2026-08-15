/**
 * RAG Effectiveness Dashboard Component
 *
 * Displays RAG system effectiveness metrics including:
 * - Overall effectiveness score
 * - Retrieval quality metrics
 * - Pattern accuracy
 * - Query trends
 */

import React, { useState, useEffect } from 'react';
import './RAGEffectivenessDashboard.css';

interface RetrievalQuality {
  timestamp: string;
  accuracy: number;
  relevance: number;
  diversity: number;
  latency_ms: number;
  success_rate: number;
}

interface RAGEffectivenessMetrics {
  timestamp: string;
  effectiveness_score: number;
  retrieval_quality: RetrievalQuality;
  pattern_accuracy: number;
  recommendation_acceptance_rate: number;
  total_queries: number;
  successful_queries: number;
  failed_queries: number;
  avg_query_latency_ms: number;
}

export const RAGEffectivenessDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<RAGEffectivenessMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds

  useEffect(() => {
    loadMetrics();
    const interval = setInterval(loadMetrics, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const loadMetrics = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/monitoring/rag-effectiveness');
      if (!response.ok) {
        throw new Error('Failed to load RAG effectiveness metrics');
      }

      const data = await response.json();
      setMetrics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getEffectivenessColor = (score: number): string => {
    if (score >= 0.8) return '#22c55e'; // green
    if (score >= 0.7) return '#f59e0b'; // amber
    return '#ef4444'; // red
  };

  const getHealthStatus = (score: number): string => {
    if (score >= 0.8) return 'Excellent';
    if (score >= 0.7) return 'Good';
    if (score >= 0.6) return 'Fair';
    return 'Poor';
  };

  return (
    <div className="rag-effectiveness-dashboard">
      <div className="dashboard-header">
        <h2>RAG Effectiveness Monitor</h2>
        <p>Real-time monitoring of retrieval-augmented generation system performance</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {loading && !metrics ? (
        <div className="loading">Loading RAG effectiveness metrics...</div>
      ) : metrics ? (
        <>
          {/* Effectiveness Score Card */}
          <div className="effectiveness-score-card">
            <div className="score-circle">
              <svg viewBox="0 0 100 100" className="gauge">
                <circle cx="50" cy="50" r="45" className="gauge-background" />
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  className="gauge-fill"
                  style={{
                    strokeDasharray: `${metrics.effectiveness_score * 282.7} 282.7`,
                    stroke: getEffectivenessColor(metrics.effectiveness_score)
                  }}
                />
              </svg>
              <div className="score-value">
                <span className="score">{(metrics.effectiveness_score * 100).toFixed(0)}%</span>
                <span className="status">{getHealthStatus(metrics.effectiveness_score)}</span>
              </div>
            </div>
            <div className="score-info">
              <h3>Overall Effectiveness</h3>
              <p>System RAG quality and pattern accuracy combined</p>
              <div className="target-indicator">
                <span>Target: 75%</span>
                <span className={metrics.effectiveness_score >= 0.75 ? 'met' : 'unmet'}>
                  {metrics.effectiveness_score >= 0.75 ? '✓ Met' : '✗ Below Target'}
                </span>
              </div>
            </div>
          </div>

          {/* Key Metrics Cards */}
          <div className="metrics-grid">
            {/* Accuracy */}
            <div className="metric-card">
              <div className="metric-header">
                <h4>Retrieval Accuracy</h4>
                <span className="metric-value">{(metrics.retrieval_quality.accuracy * 100).toFixed(0)}%</span>
              </div>
              <div className="metric-bar">
                <div
                  className="metric-fill"
                  style={{
                    width: `${metrics.retrieval_quality.accuracy * 100}%`,
                    backgroundColor: getEffectivenessColor(metrics.retrieval_quality.accuracy)
                  }}
                />
              </div>
              <p className="metric-description">Accuracy of retrieved results</p>
            </div>

            {/* Relevance */}
            <div className="metric-card">
              <div className="metric-header">
                <h4>Relevance Score</h4>
                <span className="metric-value">{(metrics.retrieval_quality.relevance * 100).toFixed(0)}%</span>
              </div>
              <div className="metric-bar">
                <div
                  className="metric-fill"
                  style={{
                    width: `${metrics.retrieval_quality.relevance * 100}%`,
                    backgroundColor: getEffectivenessColor(metrics.retrieval_quality.relevance)
                  }}
                />
              </div>
              <p className="metric-description">Relevance to user queries</p>
            </div>

            {/* Success Rate */}
            <div className="metric-card">
              <div className="metric-header">
                <h4>Query Success Rate</h4>
                <span className="metric-value">{(metrics.retrieval_quality.success_rate * 100).toFixed(0)}%</span>
              </div>
              <div className="metric-bar">
                <div
                  className="metric-fill"
                  style={{
                    width: `${metrics.retrieval_quality.success_rate * 100}%`,
                    backgroundColor: getEffectivenessColor(metrics.retrieval_quality.success_rate)
                  }}
                />
              </div>
              <p className="metric-description">Percentage of successful retrievals</p>
            </div>

            {/* Pattern Accuracy */}
            <div className="metric-card">
              <div className="metric-header">
                <h4>Pattern Accuracy</h4>
                <span className="metric-value">{(metrics.pattern_accuracy * 100).toFixed(0)}%</span>
              </div>
              <div className="metric-bar">
                <div
                  className="metric-fill"
                  style={{
                    width: `${metrics.pattern_accuracy * 100}%`,
                    backgroundColor: getEffectivenessColor(metrics.pattern_accuracy)
                  }}
                />
              </div>
              <p className="metric-description">Accuracy of discovered patterns</p>
            </div>

            {/* Latency */}
            <div className="metric-card">
              <div className="metric-header">
                <h4>Query Latency</h4>
                <span className="metric-value">{metrics.retrieval_quality.latency_ms.toFixed(0)}ms</span>
              </div>
              <div className="metric-bar">
                <div
                  className="metric-fill"
                  style={{
                    width: `${Math.min((metrics.retrieval_quality.latency_ms / 1000) * 100, 100)}%`,
                    backgroundColor: metrics.retrieval_quality.latency_ms < 200 ? '#22c55e' : '#f59e0b'
                  }}
                />
              </div>
              <p className="metric-description">Average query response time (target: &lt;200ms)</p>
            </div>

            {/* Acceptance Rate */}
            <div className="metric-card">
              <div className="metric-header">
                <h4>Acceptance Rate</h4>
                <span className="metric-value">{(metrics.recommendation_acceptance_rate * 100).toFixed(0)}%</span>
              </div>
              <div className="metric-bar">
                <div
                  className="metric-fill"
                  style={{
                    width: `${metrics.recommendation_acceptance_rate * 100}%`,
                    backgroundColor: getEffectivenessColor(metrics.recommendation_acceptance_rate)
                  }}
                />
              </div>
              <p className="metric-description">Users accepting recommendations</p>
            </div>
          </div>

          {/* Query Statistics */}
          <div className="statistics-section">
            <h3>Query Statistics</h3>
            <div className="stats-cards">
              <div className="stat-card">
                <div className="stat-label">Total Queries</div>
                <div className="stat-value">{metrics.total_queries}</div>
                <div className="stat-sub">all-time</div>
              </div>

              <div className="stat-card">
                <div className="stat-label">Successful</div>
                <div className="stat-value success">{metrics.successful_queries}</div>
                <div className="stat-sub">
                  {((metrics.successful_queries / Math.max(metrics.total_queries, 1)) * 100).toFixed(1)}%
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-label">Failed</div>
                <div className="stat-value error">{metrics.failed_queries}</div>
                <div className="stat-sub">
                  {((metrics.failed_queries / Math.max(metrics.total_queries, 1)) * 100).toFixed(1)}%
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-label">Avg Latency</div>
                <div className="stat-value">{metrics.avg_query_latency_ms.toFixed(0)}ms</div>
                <div className="stat-sub">
                  {metrics.avg_query_latency_ms < 200 ? 'Within target' : 'Above target'}
                </div>
              </div>
            </div>
          </div>

          {/* Diversity Score */}
          <div className="diversity-section">
            <h3>Result Diversity</h3>
            <div className="diversity-gauge">
              <div className="gauge-container">
                <div
                  className="gauge-circle"
                  style={{
                    background: `conic-gradient(
                      ${getEffectivenessColor(metrics.retrieval_quality.diversity)} 0deg ${
                        metrics.retrieval_quality.diversity * 360
                      }deg,
                      #e5e7eb ${metrics.retrieval_quality.diversity * 360}deg 360deg
                    )`
                  }}
                >
                  <div className="gauge-inner">
                    <span className="diversity-percent">
                      {(metrics.retrieval_quality.diversity * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
              <p>Diversity of retrieved results across categories</p>
            </div>
          </div>

          {/* Last Updated */}
          <div className="dashboard-footer">
            <span className="last-updated">
              Last updated: {new Date(metrics.timestamp).toLocaleTimeString()}
            </span>
            <button className="refresh-button" onClick={loadMetrics}>
              Refresh Now
            </button>
          </div>
        </>
      ) : null}
    </div>
  );
};

export default RAGEffectivenessDashboard;
