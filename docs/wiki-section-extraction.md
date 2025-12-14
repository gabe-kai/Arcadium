# Wiki Section Extraction Features

## Overview

Writers can extract sections from existing pages into new pages, helping manage page size and improve organization.

## Extraction Methods

### 1. Editor Selection Extraction

#### Process
1. Writer selects text in the editor
2. Clicks "Extract to New Page" button
3. Dialog opens with:
   - Selected content preview
   - New page title field (auto-filled from first heading if present)
   - New page slug (auto-generated)
   - Parent selection (default: current page as parent)
   - Section selection
4. Writer confirms
5. New page created with selected content
6. Selected content replaced with link to new page in original

#### Selection Rules
- Can select any text range
- If selection includes heading, heading becomes new page title
- If selection spans multiple headings, first heading becomes title
- Content below headings included in extraction

### 2. Heading-Based Extraction

#### Process
1. Writer selects a heading (H2, H3, etc.) in editor
2. Clicks "Extract Section" button
3. System automatically selects:
   - The heading
   - All content until next heading of same or higher level
4. Dialog opens (same as selection extraction)
5. New page created
6. Original page updated with link

#### Heading Selection
- Click heading in editor
- Or use "Extract Section" button on specific heading
- System identifies section boundaries automatically

### 3. TOC Promotion

#### Process
1. Writer views Table of Contents (right sidebar)
2. Each TOC entry has "Promote" button
3. Clicking "Promote" opens menu:
   - "Promote to Child Page" (creates child of current page)
   - "Promote to Sibling Page" (creates sibling, same parent)
4. Writer selects option
5. Dialog opens with:
   - Section title (from heading)
   - New page title (editable)
   - Parent selection (pre-filled based on choice)
   - Section selection
6. New page created
7. Section replaced with link in original

#### TOC Promotion UI
```
Table of Contents
├─ Introduction [Promote ▼]
│  ├─ Overview [Promote ▼]
│  └─ Getting Started [Promote ▼]
└─ Advanced Topics [Promote ▼]
```

**Promote Menu:**
- Promote to Child Page
- Promote to Sibling Page
- Cancel

## Extraction Behavior

### Content Replacement
- Extracted content replaced with: `[Section Title](new-page-slug)`
- Link styled as internal wiki link
- Preserves context around extraction point

### Link Creation
- Automatic bidirectional link created
- New page shows backlink to original
- Original page shows forward link to new page

### Version History
- Extraction creates new version of original page
- New page starts at version 1
- Version notes: "Section extracted to [new page title]"

## API Endpoints

### Extract Selection to New Page
```
POST /api/pages/{page_id}/extract
```

**Request Body:**
```json
{
  "selection_start": 100,
  "selection_end": 500,
  "new_title": "Extracted Section",
  "new_slug": "extracted-section",
  "parent_id": "uuid",
  "section": "section-name",
  "replace_with_link": true
}
```

**Response:**
```json
{
  "new_page": {
    "id": "uuid",
    "title": "Extracted Section",
    "slug": "extracted-section"
  },
  "original_page": {
    "id": "uuid",
    "version": 6
  }
}
```

### Extract Heading Section
```
POST /api/pages/{page_id}/extract-heading
```

**Request Body:**
```json
{
  "heading_text": "Section Title",
  "heading_level": 2,
  "new_title": "Extracted Section",
  "new_slug": "extracted-section",
  "parent_id": "uuid",
  "section": "section-name",
  "promote_as": "child"  // or "sibling"
}
```

### Promote from TOC
```
POST /api/pages/{page_id}/promote-section
```

**Request Body:**
```json
{
  "heading_anchor": "section-title",
  "promote_as": "child",  // or "sibling"
  "new_title": "Promoted Section",
  "new_slug": "promoted-section",
  "section": "section-name"
}
```

## UI Components

### Editor Toolbar Button
- "Extract Selection" button (enabled when text selected)
- Icon: Scissors or extract icon
- Tooltip: "Extract selected content to new page"

### TOC Promotion Button
- Small button next to each TOC entry
- Dropdown menu on click
- Visual indicator when hovering

### Extraction Dialog
```
Extract to New Page
─────────────────────
Selected Content Preview:
[Preview of selected content...]

New Page Title: [________________]
New Page Slug:  [extracted-section] (auto-generated, editable)

Parent Page: [Select parent... ▼]
Section:     [Select section... ▼]

○ Promote as Child Page
○ Promote as Sibling Page

[Cancel] [Extract]
```

## Use Cases

### Page Size Management
- Large page exceeds size limit
- Writer extracts sections to reduce size
- Original page becomes overview with links
- Detailed content in child pages

### Content Organization
- Page covers multiple topics
- Writer extracts each topic to separate page
- Better organization and navigation
- Easier to find specific content

### Collaborative Editing
- Multiple writers working on different sections
- Extract sections to allow parallel editing
- Merge back if needed (future feature)

## Implementation Notes

### Content Parsing
- Parse Markdown to identify section boundaries
- Handle nested headings correctly
- Preserve formatting in extracted content
- Maintain link references

### Link Replacement
- Smart link text generation
- Preserve context around link
- Update internal link references if needed

### Validation
- Ensure extracted content is valid Markdown
- Validate new page title and slug
- Check for circular references
- Verify parent exists

### Performance
- Efficient content extraction
- Fast section boundary detection
- Minimal database queries
- Optimize link updates

