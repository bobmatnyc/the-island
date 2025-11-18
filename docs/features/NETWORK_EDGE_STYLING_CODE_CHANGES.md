# Network Edge Styling - Code Changes Reference

## File Modified
`/Users/masa/Projects/epstein/server/web/app.js`

## Change 1: Edge Thickness Function (Lines 1187-1197)

### Before
```javascript
function getEdgeThickness(weight) {
    if (weight >= 100) return 8;      // Very strong (100+ flights)
    if (weight >= 50) return 6;       // Strong (50-99 flights)
    if (weight >= 10) return 4;       // Medium (10-49 flights)
    if (weight >= 5) return 2.5;      // Weak (5-9 flights)
    return 1.5;                       // Very weak (1-4 flights)
}
```

### After
```javascript
/**
 * Get edge thickness based on connection strength (weight)
 * 5 tiers as per requirements
 */
function getEdgeThickness(weight) {
    if (weight >= 21) return 8;       // Very bold (21+ connections)
    if (weight >= 11) return 6.5;     // Bold (11-20 connections)
    if (weight >= 6) return 5;        // Medium (6-10 connections)
    if (weight >= 3) return 3;        // Light (3-5 connections)
    return 1.5;                       // Thin (1-2 connections)
}
```

### Rationale
Changed thresholds to match exact requirements:
- 21+ connections → 8px (was 100+)
- 11-20 connections → 6.5px (was 50-99)
- 6-10 connections → 5px (was 10-49)
- 3-5 connections → 3px (was 5-9)
- 1-2 connections → 1.5px (was 1-4)

## Change 2: Enhanced Legend (Lines 1303-1440)

### Before (Simple Legend)
```javascript
// Add legend box
const legend = g.append('g')
    .attr('class', 'network-legend')
    .attr('transform', 'translate(20, ' + (height - 120) + ')');

legend.append('rect')
    .attr('width', 220)
    .attr('height', 100)
    .attr('fill', 'var(--bg-secondary)')
    .attr('stroke', 'var(--border-color)')
    .attr('stroke-width', 1)
    .attr('rx', 8);

legend.append('text')
    .attr('x', 10)
    .attr('y', 20)
    .attr('font-size', 13)
    .attr('font-weight', 600)
    .attr('fill', textPrimary)
    .text('Connection Strength:');

// Add line samples with descriptions
const lineData = [
    {strength: "Strong (>100)", width: 4, y: 40},
    {strength: "Medium (20-100)", width: 2, y: 60},
    {strength: "Weak (<20)", width: 1, y: 80}
];

lineData.forEach(d => {
    legend.append('line')
        .attr('x1', 10)
        .attr('x2', 40)
        .attr('y1', d.y)
        .attr('y2', d.y)
        .attr('stroke', accentBlue)
        .attr('stroke-width', d.width);

    legend.append('text')
        .attr('x', 50)
        .attr('y', d.y + 4)
        .attr('font-size', 11)
        .attr('fill', textPrimary)
        .text(d.strength);
});
```

### After (Enhanced Dual-Section Legend)
```javascript
// Enhanced legend with thickness tiers and relationship colors
const legend = g.append('g')
    .attr('class', 'network-legend')
    .attr('transform', 'translate(20, ' + (height - 340) + ')');

// Legend background with increased height for both sections
legend.append('rect')
    .attr('width', 240)
    .attr('height', 320)
    .attr('fill', 'var(--bg-secondary)')
    .attr('stroke', 'var(--border-color)')
    .attr('stroke-width', 1)
    .attr('rx', 8)
    .style('opacity', 0.95);

// Section 1: Connection Strength
legend.append('text')
    .attr('x', 10)
    .attr('y', 20)
    .attr('font-size', 13)
    .attr('font-weight', 600)
    .attr('fill', textPrimary)
    .text('Connection Strength:');

// All 5 thickness tiers with accurate widths
const lineData = [
    {strength: "Very Bold (21+)", width: 8, y: 40},
    {strength: "Bold (11-20)", width: 6.5, y: 60},
    {strength: "Medium (6-10)", width: 5, y: 80},
    {strength: "Light (3-5)", width: 3, y: 100},
    {strength: "Thin (1-2)", width: 1.5, y: 120}
];

lineData.forEach(d => {
    legend.append('line')
        .attr('x1', 10)
        .attr('x2', 50)
        .attr('y1', d.y)
        .attr('y2', d.y)
        .attr('stroke', accentBlue)
        .attr('stroke-width', d.width)
        .attr('stroke-opacity', 0.8);

    legend.append('text')
        .attr('x', 60)
        .attr('y', d.y + 4)
        .attr('font-size', 11)
        .attr('fill', textPrimary)
        .text(d.strength);
});

// Section 2: Relationship Types
legend.append('text')
    .attr('x', 10)
    .attr('y', 155)
    .attr('font-size', 13)
    .attr('font-weight', 600)
    .attr('fill', textPrimary)
    .text('Relationship Types:');

const colorData = [
    {type: 'FLEW_TOGETHER', y: 175},
    {type: 'BUSINESS', y: 200},
    {type: 'FAMILY', y: 225},
    {type: 'LEGAL', y: 250},
    {type: 'EMPLOYMENT', y: 275}
];

let activeTypeFilter = null;

colorData.forEach(d => {
    const typeConfig = CONNECTION_TYPES[d.type];

    // Clickable colored line
    const line = legend.append('line')
        .attr('x1', 10)
        .attr('x2', 50)
        .attr('y1', d.y)
        .attr('y2', d.y)
        .attr('stroke', typeConfig.color)
        .attr('stroke-width', 4)
        .attr('stroke-opacity', 0.8)
        .style('cursor', 'pointer')
        .on('click', function() {
            // Toggle filter for this relationship type
            if (activeTypeFilter === d.type) {
                // Clear filter
                activeTypeFilter = null;
                link.transition().duration(300)
                    .attr('stroke-opacity', 0.6)
                    .attr('display', 'block');
                d3.select(this).attr('stroke-opacity', 0.8);
            } else {
                // Apply filter
                activeTypeFilter = d.type;
                link.transition().duration(300)
                    .attr('stroke-opacity', edge =>
                        (edge.relationship_type || 'FLEW_TOGETHER') === d.type ? 0.9 : 0.1)
                    .attr('display', edge =>
                        (edge.relationship_type || 'FLEW_TOGETHER') === d.type ? 'block' : 'none');

                // Highlight this legend item
                legend.selectAll('line').filter(function() {
                    return this !== line.node();
                }).attr('stroke-opacity', 0.3);
                d3.select(this).attr('stroke-opacity', 1);
            }
        })
        .on('mouseover', function() {
            if (activeTypeFilter !== d.type) {
                d3.select(this).attr('stroke-opacity', 1);
            }
        })
        .on('mouseout', function() {
            if (activeTypeFilter !== d.type) {
                d3.select(this).attr('stroke-opacity', 0.8);
            } else if (activeTypeFilter === null) {
                d3.select(this).attr('stroke-opacity', 0.8);
            }
        });

    legend.append('text')
        .attr('x', 60)
        .attr('y', d.y + 4)
        .attr('font-size', 11)
        .attr('fill', textPrimary)
        .text(typeConfig.label)
        .style('pointer-events', 'none');
});

// Add hint text
legend.append('text')
    .attr('x', 10)
    .attr('y', 305)
    .attr('font-size', 9)
    .attr('fill', 'var(--text-tertiary)')
    .attr('font-style', 'italic')
    .text('Click colors to filter connections');
```

### Rationale
- Expanded legend to show all 5 thickness tiers (was 3)
- Added second section for relationship type colors
- Made color legend interactive (click to filter)
- Added visual feedback for hover and active states
- Increased legend size to accommodate both sections
- Added hint text to explain interactivity

## Change 3: Enhanced Edge Tooltips (Lines 1683-1742)

### Before
```javascript
const sourceName = edgeData.source.id || edgeData.source;
const targetName = edgeData.target.id || edgeData.target;
const weight = edgeData.weight || 1;
const contexts = edgeData.contexts || ['unknown'];

const contextText = contexts.map(c => {
    if (c === 'flight_log') return 'Flight Logs';
    if (c === 'contact_book') return 'Contact Book';
    if (c === 'document') return 'Documents';
    return c;
}).join(', ');

const tooltipContent = `
    <div style="margin-bottom: 8px;">
        <strong style="color: var(--accent-blue);">${weight} co-occurrence${weight > 1 ? 's' : ''}</strong>
    </div>
    <div style="margin-bottom: 4px;">
        <strong>Between:</strong><br/>
        ${formatEntityName(sourceName)} ↔ ${formatEntityName(targetName)}
    </div>
    <div style="color: var(--text-secondary); font-size: 11px; margin-top: 8px;">
        <strong>Source:</strong> ${contextText}
    </div>
    <div style="color: var(--text-tertiary); font-size: 10px; margin-top: 8px; font-style: italic;">
        Click for details
    </div>
`;
```

### After
```javascript
const sourceName = edgeData.source.id || edgeData.source;
const targetName = edgeData.target.id || edgeData.target;
const weight = edgeData.weight || 1;
const contexts = edgeData.contexts || ['unknown'];
const relType = edgeData.relationship_type || 'FLEW_TOGETHER';

const contextText = contexts.map(c => {
    if (c === 'flight_log') return 'Flight Logs';
    if (c === 'contact_book') return 'Contact Book';
    if (c === 'document') return 'Documents';
    return c;
}).join(', ');

// Get relationship type info (defined earlier in initializeNetworkGraph)
const typeColors = {
    FLEW_TOGETHER: '#0969da',
    BUSINESS: '#8250df',
    FAMILY: '#cf222e',
    LEGAL: '#bf8700',
    EMPLOYMENT: '#1a7f37',
    UNKNOWN: 'var(--border-color)'
};
const typeLabels = {
    FLEW_TOGETHER: 'Flew Together',
    BUSINESS: 'Business Partner',
    FAMILY: 'Family Member',
    LEGAL: 'Legal/Attorney',
    EMPLOYMENT: 'Employment',
    UNKNOWN: 'Connection'
};
const relColor = typeColors[relType] || typeColors.UNKNOWN;
const relLabel = typeLabels[relType] || typeLabels.UNKNOWN;

// Determine strength tier
let strengthTier = 'Thin';
if (weight >= 21) strengthTier = 'Very Bold';
else if (weight >= 11) strengthTier = 'Bold';
else if (weight >= 6) strengthTier = 'Medium';
else if (weight >= 3) strengthTier = 'Light';

const tooltipContent = `
    <div style="margin-bottom: 8px;">
        <strong style="color: ${relColor};">${weight} connection${weight > 1 ? 's' : ''}</strong>
        <span style="color: var(--text-secondary); font-size: 10px; margin-left: 8px;">(${strengthTier})</span>
    </div>
    <div style="margin-bottom: 8px;">
        <div style="display: inline-block; width: 12px; height: 3px; background: ${relColor}; margin-right: 6px; vertical-align: middle;"></div>
        <strong style="color: ${relColor};">${relLabel}</strong>
    </div>
    <div style="margin-bottom: 4px;">
        <strong>Between:</strong><br/>
        ${formatEntityName(sourceName)} ↔ ${formatEntityName(targetName)}
    </div>
    <div style="color: var(--text-secondary); font-size: 11px; margin-top: 8px;">
        <strong>Source:</strong> ${contextText}
    </div>
    <div style="color: var(--text-tertiary); font-size: 10px; margin-top: 8px; font-style: italic;">
        Click for details
    </div>
`;
```

### Rationale
- Added relationship type extraction from edge data
- Added strength tier calculation (Very Bold, Bold, etc.)
- Created type color and label mappings
- Added relationship type badge with color indicator
- Colored connection count with relationship color
- Added strength tier label next to count
- Changed "co-occurrence" to "connection" for clarity

## Change 4: Enhanced Connection Details Panel (Lines 1770-1845)

### Before
```javascript
const sourceName = edgeData.source.id || edgeData.source;
const targetName = edgeData.target.id || edgeData.target;
const weight = edgeData.weight || 1;
const contexts = edgeData.contexts || ['unknown'];

// Escape HTML in names
const escapedSource = sourceName.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const escapedTarget = targetName.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

// ... context list generation ...

panel.innerHTML = `
    ...
    <div class="panel-scrollable-content" style="padding: 20px;">
        <div style="background: var(--bg-tertiary); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
            <div style="font-size: 24px; font-weight: 700; color: var(--accent-blue); margin-bottom: 4px;">
                ${weight}
            </div>
            <div style="font-size: 12px; color: var(--text-secondary);">
                Total co-occurrence${weight > 1 ? 's' : ''}
            </div>
        </div>
    ...
`;
```

### After
```javascript
const sourceName = edgeData.source.id || edgeData.source;
const targetName = edgeData.target.id || edgeData.target;
const weight = edgeData.weight || 1;
const contexts = edgeData.contexts || ['unknown'];
const relType = edgeData.relationship_type || 'FLEW_TOGETHER';

// Escape HTML in names
const escapedSource = sourceName.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const escapedTarget = targetName.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

// Get relationship type display info
const typeColors = {
    FLEW_TOGETHER: '#0969da',
    BUSINESS: '#8250df',
    FAMILY: '#cf222e',
    LEGAL: '#bf8700',
    EMPLOYMENT: '#1a7f37'
};
const typeLabels = {
    FLEW_TOGETHER: 'Flew Together',
    BUSINESS: 'Business Partnership',
    FAMILY: 'Family Relationship',
    LEGAL: 'Legal/Attorney',
    EMPLOYMENT: 'Employment'
};
const relColor = typeColors[relType] || '#0969da';
const relLabel = typeLabels[relType] || 'Connection';

// ... context list generation ...

panel.innerHTML = `
    ...
    <div class="panel-scrollable-content" style="padding: 20px;">
        <div style="background: var(--bg-tertiary); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
            <div style="margin-bottom: 12px;">
                <span style="display: inline-block; padding: 6px 12px; background: ${relColor}; color: white; border-radius: 4px; font-size: 12px; font-weight: 600;">
                    ${relLabel}
                </span>
            </div>
            <div style="font-size: 24px; font-weight: 700; color: var(--accent-blue); margin-bottom: 4px;">
                ${weight}
            </div>
            <div style="font-size: 12px; color: var(--text-secondary);">
                Total connection${weight > 1 ? 's' : ''}
            </div>
        </div>
    ...
`;
```

### Rationale
- Added relationship type extraction
- Created colored badge for relationship type
- Badge appears above connection count
- Uses relationship color for visual consistency
- Changed "co-occurrence" to "connection" for clarity
- Badge styling: white text on colored background with rounded corners

## Summary of Changes

| Change | Lines | Type | Impact |
|--------|-------|------|--------|
| Edge thickness tiers | 1187-1197 | Modified | Matches exact requirements |
| Enhanced legend | 1303-1440 | Expanded | Dual-section with interactivity |
| Edge tooltips | 1683-1742 | Enhanced | Shows type and tier |
| Details panel | 1770-1845 | Enhanced | Colored type badge |

## Net Impact

- **Total Lines Modified**: ~170 lines
- **Net New Lines**: +150 LOC
- **Deleted Lines**: ~20 LOC (old simple legend)
- **Performance Impact**: Negligible (efficient D3.js updates)
- **Breaking Changes**: None (backward compatible)

## Testing Commands

```bash
# Syntax check
node -c server/web/app.js

# Start server (if not running)
cd server
python app.py

# Access network graph
# Navigate to: http://localhost:5000
# Click "Network" tab
```

## Verification Checklist

- [x] Syntax check passes (no errors)
- [x] Edge thickness function updated with correct tiers
- [x] Legend shows all 5 thickness tiers
- [x] Legend shows all 5 relationship colors
- [x] Legend is interactive (click to filter)
- [x] Tooltips show relationship type
- [x] Tooltips show strength tier
- [x] Details panel shows colored badge
- [x] No breaking changes to existing functionality
- [x] Code follows existing patterns (D3.js)
- [x] Performance maintained (1,624 edges)
