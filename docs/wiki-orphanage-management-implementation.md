# Wiki Orphanage Management Implementation Guide

**Status**: Backend API ✅ Complete | Frontend UI ❌ Not Started
**Temporary File**: This guide will be removed after implementation is complete

## Overview

The orphanage system automatically collects orphaned pages when a parent page is deleted. This guide covers the frontend UI for managing orphaned pages. The backend API is fully implemented and ready to consume.

## Backend API Status

✅ **All endpoints implemented** in `services/wiki/app/routes/orphanage_routes.py`:
- `GET /api/orphanage` - Get orphaned pages
- `POST /api/orphanage/reassign` - Reassign orphaned pages
- `POST /api/orphanage/clear` - Clear orphanage (admin only)

**Permissions**:
- `GET /api/orphanage` - All authenticated users
- `POST /api/orphanage/reassign` - Writer, Admin
- `POST /api/orphanage/clear` - Admin only

---

## Frontend Implementation Plan

### Phase 1: Orphanage Page Component

**Goal**: Create page view for orphanage with list of orphaned pages

#### Tasks:
- [ ] Create `OrphanagePage` component
- [ ] Add route `/orphanage` (or `/pages/_orphanage`)
- [ ] Fetch orphaned pages from `GET /api/orphanage`
- [ ] Display orphaned pages list:
  - Grouped by original parent (if multiple deletions)
  - Show original parent name (from `orphaned_from`)
  - Show orphaned date
  - Visual indicator (orphaned badge/icon)
- [ ] Individual page actions:
  - View page
  - Reassign to new parent
  - Remove from orphanage (reassign)
- [ ] Bulk actions:
  - Select multiple pages
  - Reassign selected to same parent
  - Clear all (admin only)
- [ ] Filter by original parent
- [ ] Empty state when no orphaned pages

#### Component Structure:
```jsx
// client/src/pages/OrphanagePage.jsx
export function OrphanagePage() {
  const { data, isLoading, isError } = useOrphanage();
  const [selectedPages, setSelectedPages] = useState([]);
  const [parentFilter, setParentFilter] = useState('all');
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  if (isLoading) return <Loading />;
  if (isError) return <Error message="Failed to load orphaned pages" />;

  const orphanedPages = data?.pages || [];
  const groupedPages = data?.grouped_by_parent || {};

  return (
    <Layout sidebar={<Sidebar />}>
      <div className="arc-orphanage-page">
        <div className="arc-orphanage-header">
          <h1>Orphaned Pages</h1>
          <p>Pages that lost their parent page. Reassign them to a new parent.</p>
        </div>

        {orphanedPages.length === 0 ? (
          <div className="arc-orphanage-empty">
            <p>No orphaned pages. All pages have parents!</p>
          </div>
        ) : (
          <>
            <OrphanageFilters
              parentFilter={parentFilter}
              onFilterChange={setParentFilter}
              groupedPages={groupedPages}
            />

            <OrphanageActions
              selectedPages={selectedPages}
              onReassign={handleBulkReassign}
              onClear={isAdmin ? handleClear : null}
            />

            <OrphanagePageList
              pages={orphanedPages}
              groupedPages={groupedPages}
              selectedPages={selectedPages}
              onSelectionChange={setSelectedPages}
              onReassign={handleReassign}
              parentFilter={parentFilter}
            />
          </>
        )}
      </div>
    </Layout>
  );
}
```

---

### Phase 2: Orphanage API Functions

**Goal**: Create API functions for orphanage operations

#### Tasks:
- [ ] Create `useOrphanage` hook
- [ ] Create `reassignOrphanedPages` function
- [ ] Create `clearOrphanage` function
- [ ] Create mutation hooks for reassign and clear

#### API Functions:
```javascript
// client/src/services/api/pages.js
export async function fetchOrphanage(token) {
  const response = await apiClient.get('/orphanage', {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
}

export function useOrphanage() {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['orphanage'],
    queryFn: () => fetchOrphanage(token),
    enabled: !!token,
  });
}

export async function reassignOrphanedPages(pageIds, newParentId, reassignAll, token) {
  const response = await apiClient.post(
    '/orphanage/reassign',
    {
      page_ids: pageIds,
      new_parent_id: newParentId,
      reassign_all: reassignAll,
    },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
}

export function useReassignOrphanedPages() {
  const { token } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ pageIds, newParentId, reassignAll }) =>
      reassignOrphanedPages(pageIds, newParentId, reassignAll, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orphanage'] });
      queryClient.invalidateQueries({ queryKey: ['navigationTree'] });
    },
  });
}

export async function clearOrphanage(reassignTo, token) {
  const response = await apiClient.post(
    '/orphanage/clear',
    { reassign_to: reassignTo },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
}

export function useClearOrphanage() {
  const { token } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (reassignTo) => clearOrphanage(reassignTo, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orphanage'] });
      queryClient.invalidateQueries({ queryKey: ['navigationTree'] });
    },
  });
}
```

---

### Phase 3: Reassignment Dialog Component

**Goal**: Dialog for selecting new parent for orphaned pages

#### Tasks:
- [ ] Create `ReassignmentDialog` component
- [ ] Parent page searchable dropdown (reuse from MetadataForm)
- [ ] Display pages being reassigned (list of titles)
- [ ] Confirmation message
- [ ] Cancel and Reassign buttons
- [ ] Loading state during reassignment
- [ ] Success/error notifications

#### Component:
```jsx
// client/src/components/orphanage/ReassignmentDialog.jsx
export function ReassignmentDialog({
  isOpen,
  onClose,
  pages,
  onReassign,
}) {
  const [newParentId, setNewParentId] = useState(null);
  const reassignMutation = useReassignOrphanedPages();
  const { showSuccess, showError } = useNotificationContext();

  const handleReassign = () => {
    if (!newParentId) {
      showError('Please select a parent page');
      return;
    }

    const pageIds = pages.map(p => p.id);
    reassignMutation.mutate(
      {
        pageIds,
        newParentId,
        reassignAll: false,
      },
      {
        onSuccess: (data) => {
          showSuccess(`${data.reassigned} page(s) reassigned successfully`);
          onReassign();
          onClose();
        },
        onError: (error) => {
          showError(error.response?.data?.error || 'Failed to reassign pages');
        },
      }
    );
  };

  if (!isOpen) return null;

  return (
    <div className="arc-reassignment-dialog-overlay">
      <div className="arc-reassignment-dialog">
        <h3>Reassign Orphaned Pages</h3>
        <div className="arc-reassignment-pages">
          <p>Reassigning {pages.length} page(s):</p>
          <ul>
            {pages.map(page => (
              <li key={page.id}>{page.title}</li>
            ))}
          </ul>
        </div>
        <ParentPageSelector
          value={newParentId}
          onChange={setNewParentId}
          placeholder="Select new parent page..."
        />
        <div className="arc-reassignment-actions">
          <button onClick={onClose}>Cancel</button>
          <button
            onClick={handleReassign}
            disabled={!newParentId || reassignMutation.isPending}
          >
            {reassignMutation.isPending ? 'Reassigning...' : 'Reassign'}
          </button>
        </div>
      </div>
    </div>
  );
}
```

---

### Phase 4: Orphanage Page List Component

**Goal**: Display orphaned pages with actions

#### Tasks:
- [ ] Create `OrphanagePageList` component
- [ ] Display pages in groups (by original parent)
- [ ] Show for each page:
  - Title (link to page)
  - Original parent name
  - Orphaned date
  - Orphaned badge/icon
- [ ] Checkbox for selection (bulk actions)
- [ ] "Reassign" button per page
- [ ] Group header with "Reassign Group" button
- [ ] Filter by original parent

#### Component:
```jsx
// client/src/components/orphanage/OrphanagePageList.jsx
export function OrphanagePageList({
  pages,
  groupedPages,
  selectedPages,
  onSelectionChange,
  onReassign,
  parentFilter,
}) {
  const [showReassignDialog, setShowReassignDialog] = useState(false);
  const [pagesToReassign, setPagesToReassign] = useState([]);

  const handleReassignClick = (page) => {
    setPagesToReassign([page]);
    setShowReassignDialog(true);
  };

  const handleReassignGroup = (parentId) => {
    const groupPages = groupedPages[parentId] || [];
    setPagesToReassign(groupPages);
    setShowReassignDialog(true);
  };

  const handleBulkReassign = () => {
    const selected = pages.filter(p => selectedPages.includes(p.id));
    setPagesToReassign(selected);
    setShowReassignDialog(true);
  };

  // Filter pages by original parent
  const filteredPages = parentFilter === 'all'
    ? pages
    : pages.filter(p => p.orphaned_from?.id === parentFilter);

  // Group filtered pages
  const filteredGroups = {};
  filteredPages.forEach(page => {
    const parentId = page.orphaned_from?.id || 'unknown';
    if (!filteredGroups[parentId]) {
      filteredGroups[parentId] = [];
    }
    filteredGroups[parentId].push(page);
  });

  return (
    <div className="arc-orphanage-list">
      {Object.keys(filteredGroups).map(parentId => {
        const groupPages = filteredGroups[parentId];
        const originalParent = groupPages[0]?.orphaned_from;

        return (
          <div key={parentId} className="arc-orphanage-group">
            <div className="arc-orphanage-group-header">
              <h3>
                Originally from: {originalParent?.title || 'Unknown Parent'}
                <span className="arc-orphanage-count">({groupPages.length})</span>
              </h3>
              <button
                onClick={() => handleReassignGroup(parentId)}
                className="arc-reassign-group-button"
              >
                Reassign Group
              </button>
            </div>
            <ul className="arc-orphanage-pages">
              {groupPages.map(page => (
                <li key={page.id} className="arc-orphanage-item">
                  <input
                    type="checkbox"
                    checked={selectedPages.includes(page.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        onSelectionChange([...selectedPages, page.id]);
                      } else {
                        onSelectionChange(selectedPages.filter(id => id !== page.id));
                      }
                    }}
                  />
                  <Link to={`/pages/${page.id}`} className="arc-orphanage-link">
                    <span className="arc-orphanage-badge">Orphaned</span>
                    {page.title}
                  </Link>
                  <span className="arc-orphanage-date">
                    Orphaned: {formatDate(page.orphaned_at)}
                  </span>
                  <button
                    onClick={() => handleReassignClick(page)}
                    className="arc-reassign-button"
                  >
                    Reassign
                  </button>
                </li>
              ))}
            </ul>
          </div>
        );
      })}

      <ReassignmentDialog
        isOpen={showReassignDialog}
        onClose={() => setShowReassignDialog(false)}
        pages={pagesToReassign}
        onReassign={() => {
          onSelectionChange([]);
          // Refetch orphanage data
        }}
      />
    </div>
  );
}
```

---

### Phase 5: Delete Confirmation Enhancement

**Goal**: Enhance delete confirmation to show orphanage information

#### Tasks:
- [ ] Update `DeleteArchiveDialog` component
- [ ] Check if page has children before deletion
- [ ] If children exist, show message: "This page has X children. They will be moved to the Orphanage."
- [ ] Add option to reassign immediately after deletion
- [ ] Show notification after deletion with orphan count
- [ ] Add "Reassign Now" button in notification

#### Implementation:
```jsx
// client/src/components/page/DeleteArchiveDialog.jsx
// Enhanced delete confirmation
const handleDelete = async () => {
  // Check for children first
  const children = page?.children || [];
  const hasChildren = children.length > 0;

  if (hasChildren) {
    // Show enhanced confirmation
    const confirmed = confirm(
      `This page has ${children.length} child page(s). ` +
      `They will be moved to the Orphanage. Continue?`
    );
    if (!confirmed) return;
  }

  // Delete page
  deleteMutation.mutate(pageId, {
    onSuccess: (data) => {
      const orphanCount = data.orphaned_count || 0;
      if (orphanCount > 0) {
        showSuccess(
          `Page deleted. ${orphanCount} page(s) moved to Orphanage.`,
          {
            action: {
              label: 'Reassign Now',
              onClick: () => {
                navigate('/orphanage');
                // Optionally open reassignment dialog
              },
            },
          }
        );
      } else {
        showSuccess('Page deleted successfully');
      }
      onClose();
      navigate('/');
    },
  });
};
```

---

### Phase 6: Orphanage Navigation Integration

**Goal**: Add orphanage to navigation and make it easily accessible

#### Tasks:
- [ ] Add "Orphanage" link to admin dashboard
- [ ] Add orphanage indicator in navigation tree (if orphaned pages exist)
- [ ] Show orphan count badge
- [ ] Link to orphanage page from navigation

#### Implementation:
```jsx
// client/src/components/navigation/NavigationTree.jsx
// Add orphanage indicator
const { data: orphanage } = useOrphanage();
const orphanCount = orphanage?.pages?.length || 0;

// In navigation tree, add orphanage entry if pages exist:
{orphanCount > 0 && (
  <li className="arc-nav-tree-item arc-nav-tree-orphanage">
    <Link to="/orphanage" className="arc-nav-tree-link">
      <span className="arc-nav-tree-icon">📦</span>
      <span className="arc-nav-tree-title">Orphaned Pages</span>
      <span className="arc-nav-tree-badge">{orphanCount}</span>
    </Link>
  </li>
)}
```

---

## Component Structure

```
client/src/
  pages/
    OrphanagePage.jsx
    OrphanagePage.css
  components/
    orphanage/
      OrphanagePageList.jsx
      OrphanagePageList.css
      OrphanageFilters.jsx
      OrphanageActions.jsx
      ReassignmentDialog.jsx
      ReassignmentDialog.css
      OrphanageItem.jsx
    page/
      DeleteArchiveDialog.jsx (enhanced)
  services/
    api/
      pages.js (enhanced with orphanage functions)
```

---

## API Integration

### Request Format

**Reassign:**
```json
{
  "page_ids": ["uuid1", "uuid2"],
  "new_parent_id": "uuid",
  "reassign_all": false
}
```

**Clear:**
```json
{
  "reassign_to": "uuid"  // Optional
}
```

### Response Format

**Get Orphanage:**
```json
{
  "orphanage_id": "uuid",
  "pages": [
    {
      "id": "uuid",
      "title": "Orphaned Page",
      "orphaned_from": {
        "id": "uuid",
        "title": "Deleted Parent"
      },
      "orphaned_at": "2024-01-15T10:30:00Z"
    }
  ],
  "grouped_by_parent": {
    "parent-uuid-1": [...],
    "parent-uuid-2": [...]
  }
}
```

**Reassign:**
```json
{
  "reassigned": 2,
  "remaining_in_orphanage": 5
}
```

### Error Handling
- Handle 401/403 errors (redirect or show error)
- Handle validation errors (missing parent, invalid page IDs)
- Show user-friendly error messages
- Retry logic for network errors

---

## Testing Strategy

### Unit Tests
- OrphanagePage component tests
- OrphanagePageList component tests
- ReassignmentDialog component tests
- API function tests (mocked)

### Integration Tests
- Orphanage page load
- Reassign single page
- Reassign group
- Reassign all
- Clear orphanage
- Delete page with children (orphanage flow)

### Manual Testing Checklist
- [ ] Orphanage page displays orphaned pages
- [ ] Pages grouped by original parent
- [ ] Filter by original parent works
- [ ] Reassign single page works
- [ ] Reassign group works
- [ ] Reassign all works
- [ ] Clear orphanage works (admin only)
- [ ] Delete page with children shows confirmation
- [ ] Notification appears after deletion
- [ ] "Reassign Now" button navigates to orphanage
- [ ] Orphanage indicator in navigation tree

---

## Styling Notes

- Orphaned badge should be visually distinct (yellow/orange)
- Group headers should be clear and collapsible
- Reassign buttons should be prominent
- Empty state should be friendly
- List should be scrollable if many pages
- Match existing page list styling

---

## Related Documentation

- [Wiki Orphanage System](wiki-orphanage-system.md) - Feature specification
- [Wiki API Documentation](api/wiki-api.md) - Complete API reference
- [Wiki UI Implementation Guide](wiki-ui-implementation-guide.md) - General UI patterns
