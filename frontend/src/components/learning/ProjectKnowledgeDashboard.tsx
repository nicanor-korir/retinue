/**
 * Project Knowledge Dashboard Component
 *
 * Shows cross-project learnings, insights, and related projects.
 * Displays proven patterns, success metrics, and related project recommendations.
 */

import React, { useState, useEffect } from 'react';
import './ProjectKnowledgeDashboard.css';

interface CrossProjectPattern {
  pattern_id: string;
  pattern_name: string;
  success_rate: number;
  usage_count: number;
  project_count: number;
  effectiveness_score: number;
  best_practices: string[];
}

interface SimilarProject {
  project_id: string;
  name: string;
  similarity_score: number;
  patterns: string[];
}

interface PatternStatistics {
  total_patterns: number;
  total_categories: number;
  average_success_rate: number;
  average_usage_count: number;
  top_patterns: CrossProjectPattern[];
}

export interface ProjectKnowledgeDashboardProps {
  projectId: string;
  projectName: string;
}

export const ProjectKnowledgeDashboard: React.FC<ProjectKnowledgeDashboardProps> = ({
  projectId,
  projectName
}) => {
  const [patterns, setPatterns] = useState<CrossProjectPattern[]>([]);
  const [statistics, setStatistics] = useState<PatternStatistics | null>(null);
  const [similarProjects, setSimilarProjects] = useState<SimilarProject[]>([]);
  const [activeTab, setActiveTab] = useState<'patterns' | 'statistics' | 'similar'>('patterns');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [projectId]);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load patterns for this project
      const patternResponse = await fetch('/api/v1/learning/patterns/cross-project?days_back=180');
      if (patternResponse.ok) {
        const patternData = await patternResponse.json();
        setPatterns(patternData.patterns || []);
      }

      // Load statistics
      const statsResponse = await fetch('/api/v1/learning/patterns/statistics');
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStatistics(statsData);
      }
    } catch (err) {
      setError('Failed to load project knowledge');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getEffectivenessColor = (score: number): string => {
    if (score >= 0.8) return '#22c55e';
    if (score >= 0.6) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div className="project-knowledge-dashboard">
      <div className="dashboard-header">
        <h2>Knowledge Dashboard</h2>
        <p>Learnings and patterns from {projectName}</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {/* Tab Navigation */}
      <div className="tab-navigation">
        <button
          className={`tab ${activeTab === 'patterns' ? 'active' : ''}`}
          onClick={() => setActiveTab('patterns')}
        >
          💡 Proven Patterns
        </button>
        <button
          className={`tab ${activeTab === 'statistics' ? 'active' : ''}`}
          onClick={() => setActiveTab('statistics')}
        >
          📊 Statistics
        </button>
        <button
          className={`tab ${activeTab === 'similar' ? 'active' : ''}`}
          onClick={() => setActiveTab('similar')}
        >
          🔗 Related Projects
        </button>
      </div>

      {/* Content Sections */}
      <div className="dashboard-content">
        {/* Patterns Tab */}
        {activeTab === 'patterns' && (
          <div className="patterns-section">
            <h3>Proven Patterns Used Across Projects</h3>

            {loading ? (
              <div className="loading">Loading patterns...</div>
            ) : patterns.length === 0 ? (
              <div className="no-content">No patterns found</div>
            ) : (
              <div className="patterns-grid">
                {patterns.slice(0, 6).map(pattern => (
                  <div key={pattern.pattern_id} className="pattern-card">
                    <div className="pattern-header">
                      <h4>{pattern.pattern_name}</h4>
                      <div
                        className="effectiveness-badge"
                        style={{ backgroundColor: getEffectivenessColor(pattern.effectiveness_score) }}
                      >
                        {(pattern.effectiveness_score * 100).toFixed(0)}%
                      </div>
                    </div>

                    <div className="pattern-stats">
                      <div className="stat">
                        <span className="label">Success Rate:</span>
                        <span className="value">{(pattern.success_rate * 100).toFixed(0)}%</span>
                      </div>
                      <div className="stat">
                        <span className="label">Used in:</span>
                        <span className="value">{pattern.project_count} projects</span>
                      </div>
                      <div className="stat">
                        <span className="label">Occurrences:</span>
                        <span className="value">{pattern.usage_count} times</span>
                      </div>
                    </div>

                    <div className="best-practices">
                      <strong>Key Insights:</strong>
                      <ul>
                        {pattern.best_practices.slice(0, 2).map((practice, i) => (
                          <li key={i}>{practice}</li>
                        ))}
                      </ul>
                    </div>

                    <button className="apply-button">Apply to Current Project</button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Statistics Tab */}
        {activeTab === 'statistics' && (
          <div className="statistics-section">
            {loading ? (
              <div className="loading">Loading statistics...</div>
            ) : statistics ? (
              <div className="stats-grid">
                <div className="stat-card">
                  <h4>Total Patterns</h4>
                  <div className="stat-value">{statistics.total_patterns}</div>
                </div>

                <div className="stat-card">
                  <h4>Categories</h4>
                  <div className="stat-value">{statistics.total_categories}</div>
                </div>

                <div className="stat-card">
                  <h4>Average Success Rate</h4>
                  <div className="stat-value">
                    {(statistics.average_success_rate * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="stat-card">
                  <h4>Average Usage</h4>
                  <div className="stat-value">
                    {statistics.average_usage_count.toFixed(1)} times
                  </div>
                </div>
              </div>
            ) : null}

            {statistics && statistics.top_patterns.length > 0 && (
              <div className="top-patterns">
                <h3>Top Performing Patterns</h3>
                <div className="patterns-list">
                  {statistics.top_patterns.map((pattern, idx) => (
                    <div key={idx} className="pattern-row">
                      <div className="pattern-info">
                        <strong>{pattern.pattern_name}</strong>
                        <p>{pattern.usage_count} uses • {pattern.project_count} projects</p>
                      </div>
                      <div className="pattern-score">
                        <div className="success-bar">
                          <div
                            className="success-fill"
                            style={{
                              width: `${pattern.success_rate * 100}%`,
                              backgroundColor: getEffectivenessColor(pattern.success_rate)
                            }}
                          />
                        </div>
                        <span>{(pattern.success_rate * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Related Projects Tab */}
        {activeTab === 'similar' && (
          <div className="similar-section">
            <h3>Related Projects Using Similar Patterns</h3>
            <div className="related-projects">
              {loading ? (
                <div className="loading">Loading related projects...</div>
              ) : similarProjects.length === 0 ? (
                <div className="no-content">No related projects found</div>
              ) : (
                similarProjects.map(project => (
                  <div key={project.project_id} className="project-card">
                    <h4>{project.name}</h4>
                    <div className="similarity">
                      <span>Similarity Score:</span>
                      <div className="similarity-bar">
                        <div
                          className="similarity-fill"
                          style={{
                            width: `${project.similarity_score * 100}%`,
                            backgroundColor: getEffectivenessColor(project.similarity_score)
                          }}
                        />
                      </div>
                      <span>{(project.similarity_score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="shared-patterns">
                      <strong>Shared Patterns:</strong>
                      <div className="pattern-tags">
                        {project.patterns.slice(0, 3).map((pattern, i) => (
                          <span key={i} className="pattern-tag">{pattern}</span>
                        ))}
                        {project.patterns.length > 3 && (
                          <span className="pattern-tag">+{project.patterns.length - 3} more</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>

      <div className="dashboard-footer">
        <button className="primary-button" onClick={loadData}>
          Refresh Data
        </button>
      </div>
    </div>
  );
};

export default ProjectKnowledgeDashboard;
