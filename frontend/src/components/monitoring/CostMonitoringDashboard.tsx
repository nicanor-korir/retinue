/**
 * Cost Monitoring Dashboard Component
 *
 * Displays cost metrics including:
 * - Total costs and monthly projections
 * - Cost breakdown by provider and API type
 * - Cost trends over time
 * - Budget alerts
 */

import React, { useState, useEffect } from 'react';
import './CostMonitoringDashboard.css';

interface CostBreakdown {
  timestamp: string;
  total_cost: number;
  by_provider: Record<string, number>;
  by_type: Record<string, number>;
  monthly_projection: number;
  cost_per_query: number;
  cost_per_pattern_discovery: number;
}

interface CostTrend {
  date: string;
  total_cost: number;
  by_provider: Record<string, number>;
  trend_percent: number;
}

export const CostMonitoringDashboard: React.FC = () => {
  const [costData, setCostData] = useState<CostBreakdown | null>(null);
  const [trends, setTrends] = useState<CostTrend[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState('30d');

  useEffect(() => {
    loadCostData();
  }, [period]);

  const loadCostData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load cost breakdown
      const costResponse = await fetch(`/api/v1/monitoring/costs?period=${period}`);
      if (costResponse.ok) {
        const data = await costResponse.json();
        setCostData(data);
      }

      // Load cost trends
      const days = parseInt(period);
      const trendsResponse = await fetch(`/api/v1/monitoring/costs/trends?days=${days}`);
      if (trendsResponse.ok) {
        const trendsData = await trendsResponse.json();
        setTrends(trendsData.trends || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getTrendColor = (trend: number): string => {
    if (trend < -10) return '#22c55e'; // Decreasing
    if (trend > 10) return '#ef4444'; // Increasing
    return '#6b7280'; // Stable
  };

  const getTrendIcon = (trend: number): string => {
    if (trend < -10) return '↓';
    if (trend > 10) return '↑';
    return '→';
  };

  return (
    <div className="cost-monitoring-dashboard">
      <div className="dashboard-header">
        <h2>Cost Monitoring Dashboard</h2>
        <p>Track API and infrastructure costs</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {loading && !costData ? (
        <div className="loading">Loading cost metrics...</div>
      ) : costData ? (
        <>
          {/* Period Selector */}
          <div className="period-selector">
            <label htmlFor="period">Time Period:</label>
            <select value={period} onChange={(e) => setPeriod(e.target.value)}>
              <option value="1">1 Day</option>
              <option value="7">7 Days</option>
              <option value="30">30 Days</option>
            </select>
          </div>

          {/* Cost Summary Cards */}
          <div className="cost-summary">
            <div className="cost-card total">
              <div className="cost-label">Current Total</div>
              <div className="cost-value">${costData.total_cost.toFixed(2)}</div>
              <div className="cost-period">Last {period.replace('d', '')} days</div>
            </div>

            <div className="cost-card projection">
              <div className="cost-label">Projected Monthly</div>
              <div className="cost-value">${costData.monthly_projection.toFixed(2)}</div>
              <div className="cost-period">30-day estimate</div>
            </div>

            <div className="cost-card per-query">
              <div className="cost-label">Cost Per Query</div>
              <div className="cost-value">${costData.cost_per_query.toFixed(4)}</div>
              <div className="cost-period">average cost</div>
            </div>

            <div className="cost-card per-pattern">
              <div className="cost-label">Cost Per Pattern</div>
              <div className="cost-value">${costData.cost_per_pattern_discovery.toFixed(2)}</div>
              <div className="cost-period">discovery cost</div>
            </div>
          </div>

          {/* Cost Breakdown */}
          <div className="breakdown-section">
            <div className="breakdown-container">
              <div className="breakdown-box">
                <h3>By Provider</h3>
                <div className="breakdown-items">
                  {Object.entries(costData.by_provider).length === 0 ? (
                    <p className="no-data">No provider data available</p>
                  ) : (
                    Object.entries(costData.by_provider).map(([provider, cost]) => (
                      <div key={provider} className="breakdown-item">
                        <div className="item-label">{provider}</div>
                        <div className="item-bar">
                          <div
                            className="item-fill"
                            style={{
                              width: `${(cost / costData.total_cost) * 100}%`
                            }}
                          />
                        </div>
                        <div className="item-value">${cost.toFixed(2)}</div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="breakdown-box">
                <h3>By Type</h3>
                <div className="breakdown-items">
                  {Object.entries(costData.by_type).length === 0 ? (
                    <p className="no-data">No type data available</p>
                  ) : (
                    Object.entries(costData.by_type).map(([type, cost]) => (
                      <div key={type} className="breakdown-item">
                        <div className="item-label">{type}</div>
                        <div className="item-bar">
                          <div
                            className="item-fill"
                            style={{
                              width: `${(cost / costData.total_cost) * 100}%`
                            }}
                          />
                        </div>
                        <div className="item-value">${cost.toFixed(2)}</div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Cost Trends */}
          <div className="trends-section">
            <h3>Cost Trends</h3>
            {trends.length === 0 ? (
              <div className="no-data">No trend data available</div>
            ) : (
              <div className="trends-container">
                {trends.map((trend, index) => (
                  <div key={index} className="trend-item">
                    <div className="trend-header">
                      <span className="trend-date">
                        {new Date(trend.date).toLocaleDateString()}
                      </span>
                      <span
                        className="trend-icon"
                        style={{ color: getTrendColor(trend.trend_percent) }}
                      >
                        {getTrendIcon(trend.trend_percent)}
                      </span>
                    </div>
                    <div className="trend-cost">${trend.total_cost.toFixed(2)}</div>
                    <div className="trend-change" style={{ color: getTrendColor(trend.trend_percent) }}>
                      {trend.trend_percent >= 0 ? '+' : ''}{trend.trend_percent.toFixed(1)}%
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Cost Analysis */}
          <div className="analysis-section">
            <h3>Cost Analysis</h3>
            <div className="analysis-insights">
              <div className="insight">
                <div className="insight-icon">📊</div>
                <div className="insight-content">
                  <strong>Daily Average</strong>
                  <p>${(costData.total_cost / parseInt(period)).toFixed(2)}/day</p>
                </div>
              </div>

              <div className="insight">
                <div className="insight-icon">🎯</div>
                <div className="insight-content">
                  <strong>Largest Cost Driver</strong>
                  <p>
                    {Object.entries(costData.by_type).reduce((a, b) => (a[1] > b[1] ? a : b))[0]}
                  </p>
                </div>
              </div>

              <div className="insight">
                <div className="insight-icon">💡</div>
                <div className="insight-content">
                  <strong>Optimization Opportunity</strong>
                  <p>Review batch processing to reduce API calls</p>
                </div>
              </div>
            </div>
          </div>

          {/* Budget Status */}
          <div className="budget-section">
            <h3>Monthly Budget Status</h3>
            <div className="budget-item">
              <div className="budget-info">
                <span className="budget-label">Monthly Budget</span>
                <span className="budget-limit">$1,000</span>
              </div>
              <div className="budget-bar">
                <div
                  className="budget-fill"
                  style={{
                    width: `${Math.min((costData.monthly_projection / 1000) * 100, 100)}%`,
                    backgroundColor:
                      costData.monthly_projection < 800
                        ? '#22c55e'
                        : costData.monthly_projection < 950
                          ? '#f59e0b'
                          : '#ef4444'
                  }}
                />
              </div>
              <div className="budget-status">
                {costData.monthly_projection < 1000 ? (
                  <span className="within-budget">
                    ✓ ${(1000 - costData.monthly_projection).toFixed(2)} remaining
                  </span>
                ) : (
                  <span className="over-budget">
                    ✕ ${(costData.monthly_projection - 1000).toFixed(2)} over budget
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Last Updated */}
          <div className="dashboard-footer">
            <span className="last-updated">
              Last updated: {new Date(costData.timestamp).toLocaleTimeString()}
            </span>
            <button className="refresh-button" onClick={loadCostData}>
              Refresh Now
            </button>
          </div>
        </>
      ) : null}
    </div>
  );
};

export default CostMonitoringDashboard;
