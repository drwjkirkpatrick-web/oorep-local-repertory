# OOREP Dashboard Components

Clinical Mission Control Dashboard for the OOREP Homeopathic Repertory System.

## Version
**v3.8** - Enhanced with 20+ UI/UX improvements for better practitioner experience

## Overview

The dashboard provides a comprehensive interface for homeopathic practitioners to:
- Enter and manage patient cases
- Run multi-layer statistical analysis
- Compare remedies side-by-side
- Visualize repertorization results
- Export clinical reports

## Component Architecture

### Core Layout Components

| Component | Purpose |
|-----------|---------|
| `StickyDashboardHeader` | Fixed header with quick actions, patient context, keyboard shortcuts |
| `ModulePickerSidebar` | Module selection sidebar with 120+ available modules |
| `DashboardCanvas` | Main content area with grid layout for panels |
| `ReportActionBar` | Bottom action bar for report generation |

### Case Management

| Component | Purpose |
|-----------|---------|
| `CaseEntryPanel` | Patient case input form |
| `CaseListPanel` | Saved cases list with load/delete |

### Remedy Display & Interaction

| Component | Purpose |
|-----------|---------|
| `RepertorizationPanel` | Classical repertorization results table |
| `RemedyConfidenceBadge` | Visual confidence scoring with tier system |
| `RemedyHoverCard` | Rich hover preview with relationships |
| `RemedyComparisonView` | Side-by-side differential analysis |

### Filtering & Organization

| Component | Purpose |
|-----------|---------|
| `QuickFilterBar` | Kingdom/family/tier filtering |
| `CollapsiblePanel` | Expandable/collapsible panel sections |

### Error Handling & UX

| Component | Purpose |
|-----------|---------|
| `PanelErrorBoundary` | Graceful error handling per panel |
| `PanelSkeleton` | Loading skeletons for all panel types |

### Statistical Analysis Panels (v3.8)

| Component | Analysis Type |
|-----------|---------------|
| `ThompsonSamplingPanel` | Bayesian remedy ranking |
| `RubricBanditSelector` | UCB1 rubric selection |
| `PropensityScoredPanel` | IPW bias correction |
| `EnsembleStackingPanel` | Meta-learner ensemble |

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `⌘ + Enter` | Run all active modules |
| `⌘ + E` | Export report |
| `⌘ + K` | Show keyboard shortcuts help |
| `ESC` | Close modals/panels |
| `↑ / ↓` | Navigate remedy list |
| `Space` | Toggle remedy pin |

## Usage

### Basic Import

```tsx
import { 
  StickyDashboardHeader,
  RepertorizationPanel,
  RemedyConfidenceBadge 
} from '@/components/dashboard';
```

### With Error Boundary

```tsx
import { PanelErrorBoundary, withErrorBoundary } from '@/components/dashboard';

// Wrap component
<PanelErrorBoundary panelName="My Panel" onRetry={handleRetry}>
  <MyPanel data={data} />
</PanelErrorBoundary>

// Or use HOC
const SafePanel = withErrorBoundary(MyPanel, "My Panel");
```

### Loading States

```tsx
import { PanelSkeleton, RemedyRowSkeleton } from '@/components/dashboard';

// Full panel skeleton
<PanelSkeleton height="lg" rows={5} />

// Remedy row skeleton
<RemedyRowSkeleton count={10} />
```

## File Structure

```
src/components/dashboard/
├── index.ts                      # Barrel exports
├── README.md                     # This file
│
├── StickyDashboardHeader.tsx     # Fixed header with actions
├── ModulePickerSidebar.tsx       # Module selection
├── DashboardCanvas.tsx           # Main grid layout
├── ReportActionBar.tsx           # Bottom actions
│
├── CaseEntryPanel.tsx            # Case input form
├── CaseListPanel.tsx             # Saved cases list
│
├── RepertorizationPanel.tsx      # Main results table
├── RemedyConfidenceBadge.tsx     # Confidence scoring
├── RemedyHoverCard.tsx           # Hover previews
├── RemedyComparisonView.tsx      # Side-by-side compare
│
├── QuickFilterBar.tsx            # Filter controls
├── CollapsiblePanel.tsx          # Panel organization
│
├── PanelErrorBoundary.tsx        # Error handling
├── PanelSkeleton.tsx             # Loading states
│
├── ThompsonSamplingPanel.tsx     # Statistical panels
├── RubricBanditPanel.tsx
├── PropensityScoredPanel.tsx
└── EnsembleStackingPanel.tsx
```

## Changelog

### v3.8 (2025-06-11)
- Added 20+ dashboard improvements
- Sticky header with patient context
- Remedy confidence badges
- Keyboard shortcuts
- Side-by-side remedy comparison
- Quick filters (kingdom/family/tier)
- Hover preview cards
- Collapsible panel sections
- Error boundaries for resilience
- Loading skeletons
- Panel refresh functionality

### v3.7 (Previous)
- Base dashboard architecture
- Module system with 111 modules
- Basic repertorization display

## License

Part of the OOREP Homeopathic Repertory System
