/**
 * Pattern Library Browser Component
 *
 * Displays and filters domain-specific patterns by domain, complexity level,
 * and search query. Allows users to browse and select patterns for reuse.
 */

import React, { useState, useEffect } from 'react';
import './PatternLibraryBrowser.css';

interface Pattern {
  pattern_name: string;
  description: string;
  success_score: number;
  technologies: string[];
  effort_minutes: number;
  task_id: string;
}

interface Domain {
  domain_key: string;
  domain_name: string;
  description: string;
  pattern_count: number;
  keywords: string[];
}

export interface PatternLibraryBrowserProps {
  onPatternSelect?: (pattern: Pattern) => void;
}

export const PatternLibraryBrowser: React.FC<PatternLibraryBrowserProps> = ({ onPatternSelect }) => {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [filteredPatterns, setFilteredPatterns] = useState<Pattern[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [complexityFilter, setComplexityFilter] = useState<string>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load domains on component mount
  useEffect(() => {
    const loadDomains = async () => {
      setLoading(true);
      try {
        const response = await fetch('/api/v1/learning/domains');
        const data = await response.json();
        setDomains(data.domains || []);

        // Select first domain by default
        if (data.domains && data.domains.length > 0) {
          setSelectedDomain(data.domains[0].domain_key);
        }
      } catch (err) {
        setError('Failed to load domains');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadDomains();
  }, []);

  // Load patterns when domain changes
  useEffect(() => {
    if (selectedDomain) {
      loadPatternsForDomain();
    }
  }, [selectedDomain]);

  // Filter patterns based on search and complexity
  useEffect(() => {
    let filtered = patterns;

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(p =>
        p.pattern_name.toLowerCase().includes(query) ||
        p.description.toLowerCase().includes(query)
      );
    }

    // Filter by complexity
    if (complexityFilter !== 'all') {
      filtered = filtered.filter(p => {
        const score = p.success_score;
        if (complexityFilter === 'easy') return score >= 0.8;
        if (complexityFilter === 'medium') return score >= 0.6 && score < 0.8;
        if (complexityFilter === 'hard') return score < 0.6;
        return true;
      });
    }

    setFilteredPatterns(filtered);
  }, [patterns, searchQuery, complexityFilter]);

  const loadPatternsForDomain = async () => {
    if (!selectedDomain) return;

    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/v1/learning/domains/${selectedDomain}`);
      if (!response.ok) throw new Error('Failed to load patterns');

      const data = await response.json();
      setPatterns(data.patterns || []);
    } catch (err) {
      setError('Failed to load patterns');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getComplexityLabel = (score: number): string => {
    if (score >= 0.8) return 'Easy';
    if (score >= 0.6) return 'Medium';
    return 'Hard';
  };

  const getComplexityColor = (score: number): string => {
    if (score >= 0.8) return '#22c55e'; // green
    if (score >= 0.6) return '#f59e0b'; // amber
    return '#ef4444'; // red
  };

  return (
    <div className="pattern-library-browser">
      <div className="browser-header">
        <h2>Pattern Library Browser</h2>
        <p>Explore patterns across different domains and technologies</p>
      </div>

      <div className="browser-container">
        {/* Sidebar - Domains */}
        <div className="domain-sidebar">
          <h3>Domains</h3>
          <div className="domain-list">
            {domains.map(domain => (
              <button
                key={domain.domain_key}
                className={`domain-item ${selectedDomain === domain.domain_key ? 'active' : ''}`}
                onClick={() => setSelectedDomain(domain.domain_key)}
              >
                <div className="domain-name">{domain.domain_name}</div>
                <div className="pattern-count">{domain.pattern_count} patterns</div>
              </button>
            ))}
          </div>
        </div>

        {/* Main Content - Patterns */}
        <div className="patterns-content">
          {/* Search and Filter Bar */}
          <div className="search-filter-bar">
            <input
              type="text"
              className="search-input"
              placeholder="Search patterns..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <select
              className="filter-select"
              value={complexityFilter}
              onChange={(e) => setComplexityFilter(e.target.value)}
            >
              <option value="all">All Complexity Levels</option>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>

          {/* Patterns List */}
          <div className="patterns-list">
            {loading ? (
              <div className="loading">Loading patterns...</div>
            ) : error ? (
              <div className="error">{error}</div>
            ) : filteredPatterns.length === 0 ? (
              <div className="no-patterns">
                <p>No patterns found matching your criteria</p>
              </div>
            ) : (
              filteredPatterns.map((pattern, idx) => (
                <div key={idx} className="pattern-card">
                  <div className="pattern-header">
                    <h4>{pattern.pattern_name}</h4>
                    <div className="complexity-badge">
                      <span
                        className="complexity-dot"
                        style={{ backgroundColor: getComplexityColor(pattern.success_score) }}
                      />
                      {getComplexityLabel(pattern.success_score)}
                    </div>
                  </div>

                  <p className="pattern-description">{pattern.description}</p>

                  <div className="pattern-metrics">
                    <div className="metric">
                      <span className="label">Success Rate:</span>
                      <span className="value">{(pattern.success_score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="metric">
                      <span className="label">Effort:</span>
                      <span className="value">{pattern.effort_minutes} min</span>
                    </div>
                  </div>

                  <div className="pattern-technologies">
                    <strong>Technologies:</strong>
                    <div className="tech-tags">
                      {pattern.technologies.map((tech, i) => (
                        <span key={i} className="tech-tag">{tech}</span>
                      ))}
                    </div>
                  </div>

                  <button
                    className="view-button"
                    onClick={() => onPatternSelect?.(pattern)}
                  >
                    View Details
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PatternLibraryBrowser;
