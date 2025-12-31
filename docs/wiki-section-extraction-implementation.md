# Wiki Section Extraction Implementation Guide

**Status**: Backend API ✅ Complete | Frontend UI ❌ Not Started
**Temporary File**: This guide will be removed after implementation is complete

## Overview

Section extraction allows writers to extract sections from existing pages into new pages, helping manage page size and improve organization. The backend API is fully implemented and ready to consume.

## Backend API Status

✅ **All endpoints implemented** in `services/wiki/app/routes/extraction_routes.py`:
- `POST /api/pages/{page_id}/extract` - Extract text selection
- `POST /api/pages/{page_id}/extract-heading` - Extract heading section
- `POST /api/pages/{page_id}/promote-section` - Promote section from TOC

**Permissions**: All endpoints require writer or admin role (`@require_role(["writer", "admin"])`)

---

## Frontend Implementation Plan

### Phase 1: Extraction Dialog Component

**Goal**: Create reusable dialog component for all extraction methods

#### Tasks:
- [ ] Create `ExtractionDialog` component
- [ ] Dialog fields:
  - Selected content preview (read-only, markdown rendered)
  - New page title input (required, auto-filled from heading if present)
  - New page slug input (auto-generated from title, editable)
  - Parent page dropdown (searchable, default: current page)
  - Section input (text input, optional)
  - Promotion type radio buttons (Child Page / Sibling Page) - for TOC promotion
- [ ] Validation:
  - Title required
  - Slug required and unique (debounced validation)
  - Parent must exist (if specified)
- [ ] Cancel and Extract buttons
- [ ] Loading state during extraction
- [ ] Success/error notifications

#### Component Structure:
```jsx
// client/src/components/editor/ExtractionDialog.jsx
export function ExtractionDialog({
  isOpen,
  onClose,
  pageId,
  selectedContent,
  defaultTitle,
  defaultParentId,
  promotionType, // 'child' | 'sibling' | null
  onExtract,
}) {
  const [title, setTitle] = useState(defaultTitle || '');
  const [slug, setSlug] = useState('');
  const [parentId, setParentId] = useState(defaultParentId || null);
  const [section, setSection] = useState('');
  const [promoteAs, setPromoteAs] = useState(promotionType || 'child');

  // Auto-generate slug from title
  useEffect(() => {
    if (title && !slug) {
      const generated = generateSlug(title);
      setSlug(generated);
    }
  }, [title]);

  const handleExtract = () => {
    if (!title.trim() || !slug.trim()) {
      showError('Title and slug are required');
      return;
    }

    onExtract({
      new_title: title.trim(),
      new_slug: slug.trim(),
      parent_id: parentId,
      section: section.trim() || null,
      promote_as: promotionType ? promoteAs : undefined,
    });
  };

  if (!isOpen) return null;

  return (
    <div className="arc-extraction-dialog-overlay">
      <div className="arc-extraction-dialog">
        <h3>Extract to New Page</h3>
        <div className="arc-extraction-preview">
          <h4>Selected Content Preview:</h4>
          <div className="arc-extraction-content">
            {renderMarkdown(selectedContent)}
          </div>
        </div>
        <div className="arc-extraction-form">
          <label>
            New Page Title:
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </label>
          <label>
            New Page Slug:
            <input
              type="text"
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              required
            />
          </label>
          <ParentPageSelector
            value={parentId}
            onChange={setParentId}
            defaultParentId={defaultParentId}
          />
          <label>
            Section:
            <input
              type="text"
              value={section}
              onChange={(e) => setSection(e.target.value)}
              placeholder="Optional"
            />
          </label>
          {promotionType && (
            <div className="arc-promotion-type">
              <label>
                <input
                  type="radio"
                  value="child"
                  checked={promoteAs === 'child'}
                  onChange={() => setPromoteAs('child')}
                />
                Promote as Child Page
              </label>
              <label>
                <input
                  type="radio"
                  value="sibling"
                  checked={promoteAs === 'sibling'}
                  onChange={() => setPromoteAs('sibling')}
                />
                Promote as Sibling Page
              </label>
            </div>
          )}
        </div>
        <div className="arc-extraction-actions">
          <button onClick={onClose}>Cancel</button>
          <button onClick={handleExtract}>Extract</button>
        </div>
      </div>
    </div>
  );
}
```

---

### Phase 2: Editor Selection Extraction

**Goal**: Extract selected text from editor to new page

#### Tasks:
- [ ] Add "Extract Selection" button to EditorToolbar
- [ ] Button enabled only when text is selected
- [ ] Get selected text from Tiptap editor
- [ ] Detect if selection includes heading (for auto-title)
- [ ] Get selection start/end positions (character offsets)
- [ ] Open ExtractionDialog with:
  - Selected content preview
  - Auto-filled title (from first heading if present)
  - Default parent: current page
- [ ] Call `POST /api/pages/{page_id}/extract` with:
  - `selection_start` (character offset)
  - `selection_end` (character offset)
  - `new_title`
  - `new_slug`
  - `parent_id` (optional)
  - `section` (optional)
  - `replace_with_link` (true)
- [ ] On success:
  - Replace selected content with link to new page
  - Navigate to new page or show success message
  - Refresh current page content

#### Implementation:
```jsx
// client/src/components/editor/EditorToolbar.jsx
const [showExtractionDialog, setShowExtractionDialog] = useState(false);
const [selectedText, setSelectedText] = useState('');
const [selectionRange, setSelectionRange] = useState(null);

// Get selection from editor
const handleExtractSelection = () => {
  if (!editor) return;

  const { from, to } = editor.state.selection;
  const selectedText = editor.state.doc.textBetween(from, to);

  // Get markdown content for preview
  const markdown = editor.storage.markdown.getMarkdown();
  const selectedMarkdown = markdown.substring(from, to);

  // Check if selection includes heading
  const headingMatch = selectedMarkdown.match(/^#+\s+(.+)$/m);
  const defaultTitle = headingMatch ? headingMatch[1] : '';

  setSelectedText(selectedMarkdown);
  setSelectionRange({ start: from, end: to });
  setShowExtractionDialog(true);
};

// Extract mutation
const extractMutation = useMutation({
  mutationFn: (data) => extractSelection(pageId, data),
  onSuccess: (result) => {
    // Replace selection with link
    const { from, to } = selectionRange;
    const linkText = `[${data.new_title}](/pages/${result.new_page.id})`;
    editor.chain().setTextSelection({ from, to }).insertContent(linkText).run();

    // Navigate to new page
    navigate(`/pages/${result.new_page.id}`);
    showSuccess('Section extracted successfully');
  },
});

// In toolbar:
<button
  onClick={handleExtractSelection}
  disabled={!editor?.state.selection.empty}
  title="Extract selected content to new page"
>
  ✂️ Extract Selection
</button>
```

#### API Function:
```javascript
// client/src/services/api/pages.js
export async function extractSelection(pageId, data) {
  const response = await apiClient.post(
    `/pages/${pageId}/extract`,
    {
      selection_start: data.selection_start,
      selection_end: data.selection_end,
      new_title: data.new_title,
      new_slug: data.new_slug,
      parent_id: data.parent_id,
      section: data.section,
      replace_with_link: true,
    }
  );
  return response.data;
}
```

---

### Phase 3: Heading-Based Extraction

**Goal**: Extract heading and its content to new page

#### Tasks:
- [ ] Detect when cursor is on a heading in editor
- [ ] Add "Extract Section" button to EditorToolbar (enabled when on heading)
- [ ] Get heading text and level from editor
- [ ] Automatically select:
  - The heading
  - All content until next heading of same or higher level
- [ ] Open ExtractionDialog with:
  - Selected content preview
  - Auto-filled title (from heading text)
  - Default parent: current page
- [ ] Call `POST /api/pages/{page_id}/extract-heading` with:
  - `heading_text`
  - `heading_level` (2-6)
  - `new_title`
  - `new_slug`
  - `parent_id` (optional)
  - `section` (optional)
  - `promote_as` ('child' or 'sibling')
- [ ] On success: same as selection extraction

#### Implementation:
```jsx
// client/src/components/editor/EditorToolbar.jsx
const handleExtractHeading = () => {
  if (!editor) return;

  // Check if cursor is on a heading
  const { $anchor } = editor.state.selection;
  const headingNode = $anchor.parent;

  if (!headingNode || headingNode.type.name !== 'heading') {
    showError('Please place cursor on a heading');
    return;
  }

  const headingText = headingNode.textContent;
  const headingLevel = headingNode.attrs.level;

  // Find section boundaries (content until next heading of same or higher level)
  const { from, to } = findHeadingSection(editor, $anchor, headingLevel);
  const selectedMarkdown = editor.storage.markdown.getMarkdown().substring(from, to);

  setSelectedText(selectedMarkdown);
  setSelectionRange({ start: from, end: to });
  setHeadingInfo({ text: headingText, level: headingLevel });
  setShowExtractionDialog(true);
};

// Extract heading mutation
const extractHeadingMutation = useMutation({
  mutationFn: (data) => extractHeadingSection(pageId, data),
  onSuccess: (result) => {
    // Replace section with link
    const { from, to } = selectionRange;
    const linkText = `[${data.new_title}](/pages/${result.new_page.id})`;
    editor.chain().setTextSelection({ from, to }).insertContent(linkText).run();

    navigate(`/pages/${result.new_page.id}`);
    showSuccess('Section extracted successfully');
  },
});
```

#### API Function:
```javascript
// client/src/services/api/pages.js
export async function extractHeadingSection(pageId, data) {
  const response = await apiClient.post(
    `/pages/${pageId}/extract-heading`,
    {
      heading_text: data.heading_text,
      heading_level: data.heading_level,
      new_title: data.new_title,
      new_slug: data.new_slug,
      parent_id: data.parent_id,
      section: data.section,
      promote_as: data.promote_as || 'child',
    }
  );
  return response.data;
}
```

---

### Phase 4: TOC Promotion

**Goal**: Promote sections from TOC to child/sibling pages

#### Tasks:
- [ ] Add "Promote" button to each TOC entry in TableOfContents component
- [ ] Button opens dropdown menu:
  - "Promote to Child Page"
  - "Promote to Sibling Page"
  - "Cancel"
- [ ] On menu selection:
  - Get heading anchor from TOC entry
  - Get heading text and level
  - Open ExtractionDialog with:
    - Section title (from heading)
    - Editable new page title (default: heading text)
    - Pre-filled parent selection:
      - Child: current page
      - Sibling: current page's parent
    - Promotion type set
- [ ] Call `POST /api/pages/{page_id}/promote-section` with:
  - `heading_anchor` (e.g., "section-title")
  - `promote_as` ('child' or 'sibling')
  - `new_title`
  - `new_slug`
  - `section` (optional)
- [ ] On success:
  - Refresh current page (to show link replacement)
  - Navigate to new page or show success message

#### Implementation:
```jsx
// client/src/components/navigation/TableOfContents.jsx
const [promoteMenuOpen, setPromoteMenuOpen] = useState(null);
const [showExtractionDialog, setShowExtractionDialog] = useState(false);
const { user } = useAuth();
const canExtract = user?.role === 'writer' || user?.role === 'admin';

const handlePromoteClick = (heading, event) => {
  event.stopPropagation();
  setPromoteMenuOpen(heading.anchor);
};

const handlePromoteOption = (heading, promoteAs) => {
  setPromoteMenuOpen(null);

  // Get current page data for parent selection
  const defaultParentId = promoteAs === 'child' ? pageId : page?.parent_id;

  setExtractionData({
    heading_anchor: heading.anchor,
    heading_text: heading.text,
    default_title: heading.text,
    default_parent_id: defaultParentId,
    promotion_type: promoteAs,
  });
  setShowExtractionDialog(true);
};

// In TOC rendering:
{tocItems.map(item => (
  <li key={item.anchor} className="arc-toc-item">
    <a href={`#${item.anchor}`}>{item.text}</a>
    {canExtract && (
      <div className="arc-toc-promote">
        <button
          onClick={(e) => handlePromoteClick(item, e)}
          className="arc-toc-promote-button"
        >
          Promote ▼
        </button>
        {promoteMenuOpen === item.anchor && (
          <div className="arc-toc-promote-menu">
            <button onClick={() => handlePromoteOption(item, 'child')}>
              Promote to Child Page
            </button>
            <button onClick={() => handlePromoteOption(item, 'sibling')}>
              Promote to Sibling Page
            </button>
            <button onClick={() => setPromoteMenuOpen(null)}>Cancel</button>
          </div>
        )}
      </div>
    )}
  </li>
))}
```

#### API Function:
```javascript
// client/src/services/api/pages.js
export async function promoteSectionFromTOC(pageId, data) {
  const response = await apiClient.post(
    `/pages/${pageId}/promote-section`,
    {
      heading_anchor: data.heading_anchor,
      promote_as: data.promote_as,
      new_title: data.new_title,
      new_slug: data.new_slug,
      section: data.section,
    }
  );
  return response.data;
}
```

---

## Component Structure

```
client/src/
  components/
    editor/
      ExtractionDialog.jsx
      ExtractionDialog.css
      EditorToolbar.jsx (enhanced)
    navigation/
      TableOfContents.jsx (enhanced)
  services/
    api/
      pages.js (enhanced with extraction functions)
```

---

## Helper Functions

### Find Heading Section Boundaries
```javascript
// client/src/utils/extraction.js
export function findHeadingSection(editor, anchor, headingLevel) {
  // Find start of heading
  const headingStart = anchor.start();

  // Find end of section (next heading of same or higher level, or end of document)
  let sectionEnd = editor.state.doc.content.size;

  editor.state.doc.nodesBetween(headingStart, editor.state.doc.content.size, (node, pos) => {
    if (node.type.name === 'heading' && node.attrs.level <= headingLevel) {
      if (pos > headingStart) {
        sectionEnd = pos;
        return false; // Stop traversal
      }
    }
  });

  return { start: headingStart, end: sectionEnd };
}
```

### Generate Link Text
```javascript
// client/src/utils/extraction.js
export function generateExtractionLink(title, pageId) {
  return `[${title}](/pages/${pageId})`;
}
```

---

## API Integration

### Request Format
All extraction endpoints require:
- `new_title` (string, required)
- `new_slug` (string, required)
- `parent_id` (UUID string, optional)
- `section` (string, optional)
- Method-specific fields (selection_start/end, heading_text/level, heading_anchor)

### Response Format
All endpoints return:
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

### Error Handling
- Validate title and slug before submission
- Handle API errors (400, 401, 403, 500)
- Show user-friendly error messages
- Retry logic for network errors

---

## Testing Strategy

### Unit Tests
- ExtractionDialog component tests
- Form validation tests
- Slug generation tests
- Heading detection tests
- Section boundary detection tests

### Integration Tests
- Editor selection extraction flow
- Heading extraction flow
- TOC promotion flow
- Link replacement verification
- Navigation after extraction

### Manual Testing Checklist
- [ ] Extract selection creates new page
- [ ] Selected content replaced with link
- [ ] Heading extraction works correctly
- [ ] Section boundaries detected correctly
- [ ] TOC promotion works (child and sibling)
- [ ] Parent selection works
- [ ] Section assignment works
- [ ] Slug validation works
- [ ] Error handling works
- [ ] Success notifications appear

---

## Styling Notes

- Extraction dialog should match existing dialog styles (LinkDialog, ImageUploadDialog)
- TOC promote button should be subtle (small, icon-only on hover)
- Promote menu should be dropdown-style
- Content preview should be scrollable if long
- Form inputs should match existing design system

---

## Related Documentation

- [Wiki Section Extraction](wiki-section-extraction.md) - Feature specification
- [Wiki API Documentation](api/wiki-api.md) - Complete API reference
- [Wiki UI Implementation Guide](wiki-ui-implementation-guide.md) - General UI patterns
