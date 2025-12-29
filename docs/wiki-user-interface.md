# Wiki User Interface Design

## Design Principles

- **Book-like reading experience**: Comfortable reading width, clean typography
- **Easy navigation**: Clear hierarchy, breadcrumbs, previous/next
- **Intuitive editing**: WYSIWYG editor that feels natural
- **Responsive design**: Works on desktop, tablet, and mobile

## Layout Structure

### Reading View

```
┌─────────────────────────────────────────────────────────┐
│  [Logo] Arcadium Wiki          [Search] [User Menu]     │
├─────────────────────────────────────────────────────────┤
│  Home > Section > Parent > Current Page                │
├──────────┬──────────────────────────────┬───────────────┤
│          │                              │               │
│  Nav     │                              │  Sidebar      │
│  Tree    │      Page Content            │  - TOC        │
│          │      (Continuous Scroll)     │  - Backlinks  │
│          │                              │               │
│          │      [Previous] [Next]       │               │
│          │                              │               │
│          ├──────────────────────────────┤               │
│          │      Comments Section        │               │
│          │      (Threaded, max 5 deep)  │               │
│          │                              │               │
└──────────┴──────────────────────────────┴───────────────┘
```

### Editing View

```
┌─────────────────────────────────────────────────────────┐
│  [Save] [Cancel] [Preview] [History] [Tiptap Toolbar] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Title: [_____________________________]                 │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │                                                 │   │
│  │  Tiptap WYSIWYG Editor                          │   │
│  │  (Visual editing area)                           │   │
│  │                                                 │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Parent Page: [Select...]                               │
│  Section: [Select...]                                   │
│  Version: 5 (View History)                              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Component Specifications

### Navigation Tree (Left Sidebar)

**Purpose**: Show hierarchical page structure

**Features**:
- Expandable/collapsible tree nodes
- Highlight current page
- Click to navigate
- Search within tree
- Show page count per section

**Visual Design**:
- Clean, minimal tree view
- Icons for pages vs sections
- Hover effects
- Active state highlighting

### Main Content Area

**Reading Mode**:
- Max width: 800px (optimal reading width)
- Comfortable line height: 1.6-1.8
- Generous margins
- Typography: Serif or sans-serif (to be determined)
- Code blocks with syntax highlighting
- Responsive images

**Content Features**:
- Auto-generated TOC (if page has multiple headings)
- Inline link styling (distinguish internal vs external)
- Image galleries
- Table formatting (GFM markdown tables with proper HTML rendering)
- Block quotes

### Table of Contents (Right Sidebar)

**Purpose**: Quick navigation within current page

**Features**:
- Auto-generated from H2, H3, H4, H5, H6 headings (H1 excluded, it's the page title)
- Click to scroll to section
- Highlight current section while scrolling
- Collapsible if page is short

**Visual Design**:
- Sticky positioning (stays visible while scrolling)
- Indentation for nested headings
- Active section highlighting

### Backlinks Section

**Purpose**: Show pages that link to current page

**Features**:
- List of linking pages
- Show context (snippet of where link appears)
- Click to navigate to linking page
- Count of backlinks

### Comments Section

**Layout**:
- Below main content
- Threaded replies (indented, maximum 5 levels deep)
- User avatars/names
- Timestamps
- Edit/delete for own comments
- "Recommend update" button (for players)

**Features**:
- Collapsible threads
- Reply button on each comment (disabled at max depth)
- Mark as recommendation (special styling)
- Pagination for long comment threads
- Visual indicator for thread depth

### Search Interface

**Global Search**:
- Search bar in header
- Dropdown with recent searches
- Search suggestions as you type
- Results show: title, snippet, section, relevance

**Index View**:
- Alphabetical listing
- Filter by section
- Click letter to jump
- Show page count per letter

## Editor Interface

### WYSIWYG Editor Requirements

**Editor**: Tiptap (selected)

**Toolbar**:
- Format dropdown (H1-H6, Paragraph)
- Bold, Italic, Underline
- Bullet list, Numbered list
- Link (with internal page search)
- Image upload/insert
- Code block
- Table
- Undo/Redo

**Editing Experience**:
- Visual editing (no Markdown code visible)
- Real-time preview option
- Auto-save drafts
- Link insertion dialog with page search
- Image upload with preview
- **Table insertion dialog** - Customizable rows (1-20) and columns (1-20) with optional header row
- **Table controls toolbar** - Second toolbar row appears when cursor is inside a table:
  - Add/Delete columns (before/after current column)
  - Add/Delete rows (before/after current row)
  - Delete entire table
- Tiptap extensions for enhanced features

**Tiptap Benefits**:
- Modern, extensible architecture
- Excellent React integration
- Collaborative editing support (future)
- Rich extension ecosystem
- Good performance

### Page Metadata Editor

**Fields**:
- Title (text input)
- Slug (auto-generated, editable)
- Parent page (dropdown with search)
- Section (dropdown or text input)
- Order (number input)

**Validation**:
- Title required
- Slug must be unique
- Parent must exist (if specified)
- Order must be positive integer

## Responsive Design

### Mobile (< 768px)
- Collapsible sidebars (hamburger menu)
- Stacked layout
- Full-width content
- Touch-friendly buttons
- Simplified editor toolbar

### Tablet (768px - 1024px)
- Sidebar can be toggled
- Comfortable reading width maintained
- Editor toolbar adapts

### Desktop (> 1024px)
- Full three-column layout
- All features visible
- Optimal reading experience

## Accessibility

- Keyboard navigation support
- Screen reader friendly
- ARIA labels on interactive elements
- Focus indicators
- High contrast mode support
- Alt text for images

## User Flows

### Reading Flow
1. User lands on wiki homepage
2. Browse navigation tree or search
3. Click page to read
4. Scroll through content
5. Use TOC to jump to sections
6. Read comments at bottom
7. Navigate via Previous/Next or breadcrumbs

### Commenting Flow (Player)
1. Scroll to comments section
2. Type comment in text area
3. Optionally mark as "recommendation"
4. Submit comment
5. See comment appear in thread

### Editing Flow (Writer)
1. Click "Edit" button on page
2. Editor opens with current content
3. Make changes using WYSIWYG tools
4. Preview changes
5. Save (creates new version)
6. Redirected to updated page

### Creating Flow (Writer)
1. Click "New Page" button
2. Choose parent page (optional)
3. Choose section
4. Enter title (slug auto-generated)
5. Write content in editor
6. Save page
7. Redirected to new page

## Visual Design Notes

### Color Scheme
- Primary: To be determined (game theme)
- Text: Dark gray on light background
- Links: Blue with hover effects
- Comments: Light background
- Editor: Clean white background

### Typography
- Headings: Bold, clear hierarchy
- Body: Readable serif or sans-serif
- Code: Monospace font
- Comfortable line spacing

### Spacing
- Generous whitespace
- Clear section separation
- Comfortable padding in editor

