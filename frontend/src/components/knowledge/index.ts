/**
 * Knowledge Components Index
 *
 * Exports all knowledge system components for easy importing.
 */

// Core search and display
export { KnowledgeSearch } from './knowledge-search';
export { KnowledgeDetail } from './knowledge-detail';
export { ExtractionReview } from './extraction-review';
export { AgentPredictions } from './agent-predictions';
export { KnowledgeAnalytics } from './knowledge-analytics';

// Component props types
export type { default as KnowledgeSearchProps } from './knowledge-search';
export type { default as KnowledgeDetailProps } from './knowledge-detail';
export type { default as ExtractionReviewProps } from './extraction-review';
export type { default as AgentPredictionsProps } from './agent-predictions';
