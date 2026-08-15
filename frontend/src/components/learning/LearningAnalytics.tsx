/**
 * Learning Analytics Component
 *
 * Visualization of learning patterns and trends across projects.
 * Shows knowledge graph statistics, entity distribution, and domain analysis.
 */

import React, { useState, useEffect } from 'react';
import './LearningAnalytics.css';

interface GraphNode {
  node_id: string;
  node_type: string;
  name: string;
  connection_count: number;
}

interface GraphStatistics {
  node_count: number;
  edge_count: number;
  node_types: Record<string, number>;
  edge_types: Record<string, number>;
}

interface DomainStats {
  domain: string;
  domain_name: string;
  pattern_count: number;
  average_success_rate: number;
  difficulty_distribution: {
    easy: number;
    medium: number;
    hard: number;
  };
}

export const LearningAnalytics: React.FC = () => {
  const [graphStats, setGraphStats] = useState<GraphStatistics | null>(null);
  const [domainStats, setDomainStats] = useState<DomainStats[]>([]);
  const [topNodes, setTopNodes] = useState<GraphNode[]>([]);
  const [activeView, setActiveView] = useState<'graph' | 'domains'>('graph');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load graph statistics
      const graphResponse = await fetch('/api/v1/learning/graph/statistics');
      if (graphResponse.ok) {
        const graphData = await graphResponse.json();
        setGraphStats(graphData);
      }

      // Load all domain statistics
      const domainsResponse = await fetch('/api/v1/learning/domains');
      if (domainsResponse.ok) {
        const domainsData = await domainsResponse.json();
        // Fetch stats for each domain
        const statsPromises = domainsData.domains.map((domain: any) =>
          fetch(`/api/v1/learning/domains/${domain.domain_key}/statistics`)
            .then(res => res.json())
            .catch(() => null)
        );
        const statsResults = await Promise.all(statsPromises);
        setDomainStats(statsResults.filter(s => s !== null));
      }
    } catch (err) {
      setError('Failed to load analytics');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="learning-analytics">
      <div className="analytics-header">
        <h2>Learning Analytics</h2>
        <p>Cross-project learning patterns and insights</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {/* View Selector */}
      <div className="view-selector">
        <button
          className={`view-btn ${activeView === 'graph' ? 'active' : ''}`}
          onClick={() => setActiveView('graph')}
        >
          📊 Knowledge Graph
        </button>
        <button
          className={`view-btn ${activeView === 'domains' ? 'active' : ''}`}
          onClick={() => setActiveView('domains')}
        >
          🗂️ Domain Analysis
        </button>
      </div>

      {/* Knowledge Graph View */}
      {activeView === 'graph' && (
        <div className="graph-view">
          {loading ? (
            <div className="loading">Loading graph analytics...</div>
          ) : graphStats ? (
            <>
              {/* Summary Cards */}
              <div className="summary-cards">
                <div className="card">
                  <h4>Total Nodes</h4>
                  <div className="value">{graphStats.node_count}</div>
                  <p>Entities in knowledge graph</p>
                </div>

                <div className="card">
                  <h4>Total Connections</h4>
                  <div className="value">{graphStats.edge_count}</div>
                  <p>Relationships between entities</p>
                </div>

                <div className="card">
                  <h4>Graph Density</h4>
                  <div className="value">
                    {graphStats.node_count > 0
                      ? (
                          (graphStats.edge_count /
                            (graphStats.node_count * (graphStats.node_count - 1))) *
                          100
                        ).toFixed(1)
                      : '0'}
                    %
                  </div>
                  <p>Interconnectedness score</p>
                </div>
              </div>

              {/* Node Type Distribution */}
              <div className="analytics-section">
                <h3>Entity Type Distribution</h3>
                <div className="distribution-grid">
                  {Object.entries(graphStats.node_types).map(([type, count]) => (
                    <div key={type} className="distribution-item">
                      <div className="type-label">{type}</div>
                      <div className="type-count">{count}</div>
                      <div className="type-bar">
                        <div
                          className="type-fill"
                          style={{
                            width: `${(count / graphStats.node_count) * 100}%`
                          }}
                        />
                      </div>
                      <div className="type-percentage">
                        {((count / graphStats.node_count) * 100).toFixed(1)}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Edge Type Distribution */}
              <div className="analytics-section">
                <h3>Relationship Type Distribution</h3>
                <div className="relationship-breakdown">
                  {Object.entries(graphStats.edge_types).map(([type, count]) => (
                    <div key={type} className="relationship-item">
                      <div className="rel-type">{type}</div>
                      <div className="rel-count">
                        {count}{' '}
                        <span className="rel-percentage">
                          ({((count / graphStats.edge_count) * 100).toFixed(0)}%)
                        </span>
                      </div>
                      <div className="rel-bar">
                        <div
                          className="rel-fill"
                          style={{
                            width: `${(count / graphStats.edge_count) * 100}%`
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : null}
        </div>
      )}

      {/* Domain Analysis View */}
      {activeView === 'domains' && (
        <div className="domain-view">
          {loading ? (
            <div className="loading">Loading domain analytics...</div>
          ) : domainStats.length > 0 ? (
            <div className="domains-grid">
              {domainStats.map(domain => (
                <div key={domain.domain} className="domain-card">
                  <div className="domain-header">
                    <h4>{domain.domain_name}</h4>
                    <span className="pattern-badge">{domain.pattern_count}</span>
                  </div>

                  <div className="success-metric">
                    <strong>Avg Success Rate:</strong>
                    <div className="success-bar">
                      <div
                        className="success-fill"
                        style={{
                          width: `${domain.average_success_rate * 100}%`,
                          backgroundColor:
                            domain.average_success_rate >= 0.8
                              ? '#22c55e'
                              : domain.average_success_rate >= 0.6
                                ? '#f59e0b'
                                : '#ef4444'
                        }}
                      />
                    </div>
                    <span>{(domain.average_success_rate * 100).toFixed(0)}%</span>
                  </div>

                  <div className="complexity-distribution">
                    <strong>Complexity Levels:</strong>
                    <div className="complexity-bars">
                      <div className="complexity-item">
                        <div className="complexity-label">Easy</div>
                        <div className="complexity-bar">
                          <div
                            className="complexity-fill easy"
                            style={{
                              width: `${
                                (domain.difficulty_distribution.easy /
                                  domain.pattern_count) *
                                100
                              }%`
                            }}
                          />
                        </div>
                        <div className="complexity-count">
                          {domain.difficulty_distribution.easy}
                        </div>
                      </div>

                      <div className="complexity-item">
                        <div className="complexity-label">Medium</div>
                        <div className="complexity-bar">
                          <div
                            className="complexity-fill medium"
                            style={{
                              width: `${
                                (domain.difficulty_distribution.medium /
                                  domain.pattern_count) *
                                100
                              }%`
                            }}
                          />
                        </div>
                        <div className="complexity-count">
                          {domain.difficulty_distribution.medium}
                        </div>
                      </div>

                      <div className="complexity-item">
                        <div className="complexity-label">Hard</div>
                        <div className="complexity-bar">
                          <div
                            className="complexity-fill hard"
                            style={{
                              width: `${
                                (domain.difficulty_distribution.hard /
                                  domain.pattern_count) *
                                100
                              }%`
                            }}
                          />
                        </div>
                        <div className="complexity-count">
                          {domain.difficulty_distribution.hard}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="no-data">No domain statistics available</div>
          )}
        </div>
      )}

      <div className="analytics-footer">
        <button className="refresh-button" onClick={loadAnalytics}>
          Refresh Analytics
        </button>
      </div>
    </div>
  );
};

export default LearningAnalytics;
