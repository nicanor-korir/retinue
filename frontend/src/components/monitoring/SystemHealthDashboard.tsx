/**
 * System Health Dashboard Component
 *
 * Displays overall system health status including:
 * - Health indicators for different subsystems
 * - Active alerts with severity levels
 * - Performance metrics
 */

import React, { useState, useEffect } from 'react';
import './SystemHealthDashboard.css';

interface HealthStatus {
  timestamp: string;
  overall_health: string;
  rag_effectiveness_healthy: boolean;
  pattern_discovery_healthy: boolean;
  cost_monitoring_healthy: boolean;
  performance_healthy: boolean;
  error_rate_healthy: boolean;
  active_alerts: number;
  critical_alerts: number;
}

interface Alert {
  alert_id: string;
  severity: string;
  category: string;
  title: string;
  description: string;
  created_at: string;
  recommended_action: string;
}

export const SystemHealthDashboard: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadHealth();
    const interval = setInterval(loadHealth, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadHealth = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load health status
      const healthResponse = await fetch('/api/v1/monitoring/health');
      if (healthResponse.ok) {
        const healthData = await healthResponse.json();
        setHealth(healthData);
      }

      // Load alerts
      const alertsResponse = await fetch('/api/v1/monitoring/alerts?limit=5');
      if (alertsResponse.ok) {
        const alertsData = await alertsResponse.json();
        setAlerts(alertsData);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getHealthColor = (healthy: boolean | string): string => {
    if (typeof healthy === 'boolean') {
      return healthy ? '#22c55e' : '#ef4444';
    }
    if (healthy === 'healthy') return '#22c55e';
    if (healthy === 'degraded') return '#f59e0b';
    return '#ef4444';
  };

  const getHealthLabel = (healthy: boolean | string): string => {
    if (typeof healthy === 'boolean') {
      return healthy ? 'Healthy' : 'Unhealthy';
    }
    return healthy.charAt(0).toUpperCase() + healthy.slice(1);
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return '#ef4444';
      case 'warning':
        return '#f59e0b';
      default:
        return '#3b82f6';
    }
  };

  return (
    <div className="system-health-dashboard">
      <div className="dashboard-header">
        <h2>System Health Monitor</h2>
        <p>Real-time monitoring of system health and active alerts</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {loading && !health ? (
        <div className="loading">Loading system health...</div>
      ) : health ? (
        <>
          {/* Overall Health Status */}
          <div className="overall-health-card">
            <div className="health-indicator" style={{ backgroundColor: getHealthColor(health.overall_health) }}>
              {health.overall_health === 'healthy' && '✓'}
              {health.overall_health === 'degraded' && '⚠'}
              {health.overall_health === 'critical' && '✕'}
            </div>
            <div className="health-info">
              <h3>Overall System Health</h3>
              <div className="health-status" style={{ color: getHealthColor(health.overall_health) }}>
                {getHealthLabel(health.overall_health)}
              </div>
              <p>
                {health.critical_alerts} critical, {health.active_alerts} total alerts
              </p>
            </div>
          </div>

          {/* Subsystem Health */}
          <div className="subsystems-grid">
            <div className="subsystem-card">
              <div
                className="subsystem-indicator"
                style={{ backgroundColor: getHealthColor(health.rag_effectiveness_healthy) }}
              >
                {health.rag_effectiveness_healthy ? '✓' : '✕'}
              </div>
              <h4>RAG Effectiveness</h4>
              <span className="subsystem-status">
                {health.rag_effectiveness_healthy ? 'Healthy' : 'Issues Detected'}
              </span>
            </div>

            <div className="subsystem-card">
              <div
                className="subsystem-indicator"
                style={{ backgroundColor: getHealthColor(health.pattern_discovery_healthy) }}
              >
                {health.pattern_discovery_healthy ? '✓' : '✕'}
              </div>
              <h4>Pattern Discovery</h4>
              <span className="subsystem-status">
                {health.pattern_discovery_healthy ? 'Healthy' : 'Issues Detected'}
              </span>
            </div>

            <div className="subsystem-card">
              <div
                className="subsystem-indicator"
                style={{ backgroundColor: getHealthColor(health.cost_monitoring_healthy) }}
              >
                {health.cost_monitoring_healthy ? '✓' : '✕'}
              </div>
              <h4>Cost Monitoring</h4>
              <span className="subsystem-status">
                {health.cost_monitoring_healthy ? 'Healthy' : 'Issues Detected'}
              </span>
            </div>

            <div className="subsystem-card">
              <div
                className="subsystem-indicator"
                style={{ backgroundColor: getHealthColor(health.performance_healthy) }}
              >
                {health.performance_healthy ? '✓' : '✕'}
              </div>
              <h4>Performance</h4>
              <span className="subsystem-status">
                {health.performance_healthy ? 'Healthy' : 'Degraded'}
              </span>
            </div>

            <div className="subsystem-card">
              <div
                className="subsystem-indicator"
                style={{ backgroundColor: getHealthColor(health.error_rate_healthy) }}
              >
                {health.error_rate_healthy ? '✓' : '✕'}
              </div>
              <h4>Error Rate</h4>
              <span className="subsystem-status">
                {health.error_rate_healthy ? 'Normal' : 'Elevated'}
              </span>
            </div>
          </div>

          {/* Active Alerts */}
          <div className="alerts-section">
            <h3>Active Alerts</h3>
            {alerts.length === 0 ? (
              <div className="no-alerts">No active alerts</div>
            ) : (
              <div className="alerts-list">
                {alerts.map(alert => (
                  <div
                    key={alert.alert_id}
                    className="alert-item"
                    style={{
                      borderLeftColor: getSeverityColor(alert.severity)
                    }}
                  >
                    <div className="alert-header">
                      <div className="alert-severity" style={{ backgroundColor: getSeverityColor(alert.severity) }}>
                        {alert.severity.charAt(0).toUpperCase()}
                      </div>
                      <div className="alert-title">{alert.title}</div>
                      <div className="alert-time">
                        {new Date(alert.created_at).toLocaleTimeString()}
                      </div>
                    </div>
                    <div className="alert-description">{alert.description}</div>
                    {alert.recommended_action && (
                      <div className="alert-action">
                        <strong>Action:</strong> {alert.recommended_action}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Last Updated */}
          <div className="dashboard-footer">
            <span className="last-updated">
              Last updated: {new Date(health.timestamp).toLocaleTimeString()}
            </span>
            <button className="refresh-button" onClick={loadHealth}>
              Refresh Now
            </button>
          </div>
        </>
      ) : null}
    </div>
  );
};

export default SystemHealthDashboard;
