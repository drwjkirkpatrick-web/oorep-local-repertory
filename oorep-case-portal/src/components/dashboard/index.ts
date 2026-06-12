/**
 * Dashboard Components Index
 * 
 * OOREP Clinical Mission Control Dashboard Components
 * v3.8 - Enhanced with 20+ UI/UX improvements
 * 
 * @module dashboard
 */

// Core Layout Components
export { default as StickyDashboardHeader } from './StickyDashboardHeader';
export { default as ModulePickerSidebar } from './ModulePickerSidebar';
export { default as DashboardCanvas } from './DashboardCanvas';
export { default as ReportActionBar } from './ReportActionBar';

// Case Management
export { default as CaseEntryPanel } from './CaseEntryPanel';
export { default as CaseListPanel } from './CaseListPanel';

// Remedy Display & Interaction
export { default as RepertorizationPanel } from './RepertorizationPanel';
export { default as RemedyConfidenceBadge, RemedyComparisonRow } from './RemedyConfidenceBadge';
export { default as RemedyHoverCard } from './RemedyHoverCard';
export { default as RemedyComparisonView } from './RemedyComparisonView';

// Filtering & Organization
export { default as QuickFilterBar } from './QuickFilterBar';
export { default as CollapsiblePanel, PanelSection } from './CollapsiblePanel';

// Error Handling & Loading States
export { default as PanelErrorBoundary, withErrorBoundary } from './PanelErrorBoundary';
export { default as PanelSkeleton, RemedyRowSkeleton, ChartSkeleton, TableSkeleton } from './PanelSkeleton';

// Statistical Analysis Panels (v3.8)
export { default as ThompsonSamplingPanel } from './ThompsonSamplingPanel';
export { default as RubricBanditPanel } from './RubricBanditPanel';
export { default as PropensityScoredPanel } from './PropensityScoredPanel';
export { default as EnsembleStackingPanel } from './EnsembleStackingPanel';

// Re-export types
export type { CaseFormData } from './CaseEntryPanel';
export type { SavedCase } from './CaseListPanel';
