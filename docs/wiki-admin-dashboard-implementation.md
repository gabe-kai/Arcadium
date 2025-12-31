# Wiki Admin Dashboard Implementation Guide

**Status**: Backend API ✅ Complete | Frontend UI ❌ Not Started
**Temporary File**: This guide will be removed after implementation is complete

## Overview

The Admin Dashboard provides system configuration, monitoring, and management tools for wiki administrators. The backend API is fully implemented and ready to consume.

## Backend API Status

✅ **All endpoints implemented** in `services/wiki/app/routes/admin_routes.py`:
- `GET /api/admin/dashboard/stats` - Dashboard statistics
- `GET /api/admin/dashboard/size-distribution` - Size distribution charts
- `POST /api/admin/config/upload-size` - Configure upload size
- `POST /api/admin/config/page-size` - Configure page size limit
- `GET /api/admin/oversized-pages` - Get oversized pages list
- `PUT /api/admin/oversized-pages/{page_id}/status` - Update oversized page status

**Permissions**: All endpoints require admin role (`@require_role(["admin"])`)

---

## Frontend Implementation Plan

### Phase 1: Admin Dashboard Page Component

**Goal**: Create the main admin dashboard page with navigation to all sections

#### Tasks:
- [ ] Create `AdminDashboardPage` component
- [ ] Add route `/admin/dashboard` (protected, admin only)
- [ ] Create navigation tabs/sections:
  - Overview (stats)
  - File Upload Configuration
  - Page Size Monitoring
  - Oversized Pages
  - Orphanage Management (link to orphanage page)
- [ ] Add admin-only check (redirect if not admin)
- [ ] Layout with sidebar or tabs for section navigation

#### Component Structure:
```jsx
// client/src/pages/AdminDashboardPage.jsx
export function AdminDashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  // Check admin role
  useEffect(() => {
    if (user?.role !== 'admin') {
      navigate('/');
    }
  }, [user, navigate]);

  const [activeTab, setActiveTab] = useState('overview');

  return (
    <Layout sidebar={<Sidebar />}>
      <div className="arc-admin-dashboard">
        <h1>Admin Dashboard</h1>
        <Tabs activeTab={activeTab} onTabChange={setActiveTab}>
          <Tab id="overview" label="Overview">
            <DashboardStats />
          </Tab>
          <Tab id="upload-config" label="File Upload">
            <FileUploadConfig />
          </Tab>
          <Tab id="page-size" label="Page Size">
            <PageSizeMonitoring />
          </Tab>
          <Tab id="oversized" label="Oversized Pages">
            <OversizedPagesList />
          </Tab>
        </Tabs>
      </div>
    </Layout>
  );
}
```

#### Files to Create:
- `client/src/pages/AdminDashboardPage.jsx`
- `client/src/pages/AdminDashboardPage.css`
- `client/src/components/admin/DashboardStats.jsx`
- `client/src/components/admin/FileUploadConfig.jsx`
- `client/src/components/admin/PageSizeMonitoring.jsx`
- `client/src/components/admin/OversizedPagesList.jsx`
- `client/src/services/api/admin.js` - API functions

---

### Phase 2: Dashboard Statistics Component

**Goal**: Display system statistics overview

#### Tasks:
- [ ] Create `DashboardStats` component
- [ ] Fetch stats from `GET /api/admin/dashboard/stats`
- [ ] Display statistics cards:
  - Total pages
  - Total sections
  - Total users (by role) - placeholder (0) until user service integration
  - Total comments
  - Storage usage (MB)
- [ ] Display recent activity (empty for now)
- [ ] Loading and error states
- [ ] Auto-refresh every 30 seconds

#### API Function:
```javascript
// client/src/services/api/admin.js
export async function fetchDashboardStats(token) {
  const response = await apiClient.get('/admin/dashboard/stats', {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
}

export function useDashboardStats() {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['admin', 'dashboard', 'stats'],
    queryFn: () => fetchDashboardStats(token),
    enabled: !!token,
    refetchInterval: 30000, // 30 seconds
  });
}
```

#### Component:
```jsx
// client/src/components/admin/DashboardStats.jsx
export function DashboardStats() {
  const { data, isLoading, isError } = useDashboardStats();

  if (isLoading) return <Loading />;
  if (isError) return <Error message="Failed to load statistics" />;

  return (
    <div className="arc-dashboard-stats">
      <div className="arc-stats-grid">
        <StatCard label="Total Pages" value={data.total_pages} />
        <StatCard label="Total Sections" value={data.total_sections} />
        <StatCard label="Total Comments" value={data.total_comments} />
        <StatCard label="Storage Usage" value={`${data.storage_usage_mb} MB`} />
      </div>
      <div className="arc-users-stats">
        <h3>Users by Role</h3>
        <div className="arc-users-grid">
          <UserRoleCard role="Admins" count={data.total_users.admins} />
          <UserRoleCard role="Writers" count={data.total_users.writers} />
          <UserRoleCard role="Players" count={data.total_users.players} />
          <UserRoleCard role="Viewers" count={data.total_users.viewers} />
        </div>
      </div>
    </div>
  );
}
```

---

### Phase 3: File Upload Configuration Component

**Goal**: Allow admins to configure maximum file upload size

#### Tasks:
- [ ] Create `FileUploadConfig` component
- [ ] Fetch current config (from stats or separate endpoint)
- [ ] Radio buttons for preset sizes: 1MB, 2MB, 5MB, 10MB
- [ ] Custom size input (number input in MB)
- [ ] Display current setting prominently
- [ ] Save button (calls `POST /api/admin/config/upload-size`)
- [ ] Success/error notifications
- [ ] Loading state during save

#### API Function:
```javascript
// client/src/services/api/admin.js
export async function configureUploadSize(maxSizeMb, isCustom, token) {
  const response = await apiClient.post(
    '/admin/config/upload-size',
    { max_size_mb: maxSizeMb, is_custom: isCustom },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
}

export function useConfigureUploadSize() {
  const { token } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ maxSizeMb, isCustom }) =>
      configureUploadSize(maxSizeMb, isCustom, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'dashboard'] });
    },
  });
}
```

#### Component:
```jsx
// client/src/components/admin/FileUploadConfig.jsx
export function FileUploadConfig() {
  const { data: stats } = useDashboardStats();
  const configureMutation = useConfigureUploadSize();
  const { showSuccess, showError } = useNotificationContext();

  const [selectedSize, setSelectedSize] = useState('10');
  const [isCustom, setIsCustom] = useState(false);
  const [customSize, setCustomSize] = useState('');

  const handleSave = () => {
    const size = isCustom ? parseFloat(customSize) : parseFloat(selectedSize);
    if (isNaN(size) || size <= 0) {
      showError('Please enter a valid size');
      return;
    }

    configureMutation.mutate(
      { maxSizeMb: size, isCustom },
      {
        onSuccess: () => showSuccess('Upload size limit updated'),
        onError: (error) => showError(error.response?.data?.error || 'Failed to update'),
      }
    );
  };

  return (
    <div className="arc-upload-config">
      <h2>Maximum File Upload Size</h2>
      <div className="arc-upload-presets">
        {[1, 2, 5, 10].map(size => (
          <label key={size}>
            <input
              type="radio"
              value={size}
              checked={!isCustom && selectedSize === String(size)}
              onChange={() => {
                setSelectedSize(String(size));
                setIsCustom(false);
              }}
            />
            {size} MB
          </label>
        ))}
        <label>
          <input
            type="radio"
            checked={isCustom}
            onChange={() => setIsCustom(true)}
          />
          Custom: <input
            type="number"
            value={customSize}
            onChange={(e) => setCustomSize(e.target.value)}
            min="0.1"
            step="0.1"
            disabled={!isCustom}
          /> MB
        </label>
      </div>
      <button
        onClick={handleSave}
        disabled={configureMutation.isPending}
      >
        {configureMutation.isPending ? 'Saving...' : 'Save Configuration'}
      </button>
    </div>
  );
}
```

---

### Phase 4: Page Size Monitoring Component

**Goal**: Display size distribution charts and configure page size limits

#### Tasks:
- [ ] Create `PageSizeMonitoring` component
- [ ] Fetch size distribution from `GET /api/admin/dashboard/size-distribution`
- [ ] Create bar charts (using a charting library like Chart.js or Recharts):
  - Chart 1: Pages by Size (KB) - buckets: 0-10, 10-50, 50-100, 100-500, 500-1000, 1000+
  - Chart 2: Pages by Word Count - buckets: 0-500, 500-1000, 1000-2500, 2500-5000, 5000-10000, 10000+
- [ ] Chart interactivity: hover shows exact counts, click filters pages
- [ ] Page size limit configuration:
  - Input field for maximum size (KB)
  - "Set Maximum" button
  - "Remove Limit" button
  - Date picker for resolution due date (when setting limit)
- [ ] Save configuration (calls `POST /api/admin/config/page-size`)
- [ ] Success/error notifications

#### API Functions:
```javascript
// client/src/services/api/admin.js
export async function fetchSizeDistribution(token) {
  const response = await apiClient.get('/admin/dashboard/size-distribution', {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
}

export function useSizeDistribution() {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['admin', 'size-distribution'],
    queryFn: () => fetchSizeDistribution(token),
    enabled: !!token,
  });
}

export async function configurePageSize(maxSizeKb, resolutionDueDate, token) {
  const response = await apiClient.post(
    '/admin/config/page-size',
    {
      max_size_kb: maxSizeKb,
      resolution_due_date: resolutionDueDate?.toISOString(),
    },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
}

export function useConfigurePageSize() {
  const { token } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ maxSizeKb, resolutionDueDate }) =>
      configurePageSize(maxSizeKb, resolutionDueDate, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin'] });
    },
  });
}
```

#### Component:
```jsx
// client/src/components/admin/PageSizeMonitoring.jsx
export function PageSizeMonitoring() {
  const { data: distribution, isLoading } = useSizeDistribution();
  const configureMutation = useConfigurePageSize();
  const { showSuccess, showError } = useNotificationContext();

  const [maxSizeKb, setMaxSizeKb] = useState('');
  const [dueDate, setDueDate] = useState('');

  const handleSetLimit = () => {
    const size = parseFloat(maxSizeKb);
    if (isNaN(size) || size <= 0) {
      showError('Please enter a valid size');
      return;
    }
    if (!dueDate) {
      showError('Please select a resolution due date');
      return;
    }

    configureMutation.mutate(
      { maxSizeKb: size, resolutionDueDate: new Date(dueDate) },
      {
        onSuccess: () => showSuccess('Page size limit configured'),
        onError: (error) => showError(error.response?.data?.error || 'Failed to configure'),
      }
    );
  };

  if (isLoading) return <Loading />;

  return (
    <div className="arc-page-size-monitoring">
      <h2>Page Size Distribution</h2>
      <div className="arc-size-charts">
        <SizeChart
          title="Pages by Size (KB)"
          data={distribution.by_size_kb}
          buckets={['0-10', '10-50', '50-100', '100-500', '500-1000', '1000+']}
        />
        <SizeChart
          title="Pages by Word Count"
          data={distribution.by_word_count}
          buckets={['0-500', '500-1000', '1000-2500', '2500-5000', '5000-10000', '10000+']}
        />
      </div>

      <div className="arc-page-size-config">
        <h3>Maximum Page Size Configuration</h3>
        <div className="arc-config-form">
          <label>
            Maximum Size (KB):
            <input
              type="number"
              value={maxSizeKb}
              onChange={(e) => setMaxSizeKb(e.target.value)}
              min="1"
            />
          </label>
          <label>
            Resolution Due Date:
            <input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
            />
          </label>
          <button onClick={handleSetLimit} disabled={configureMutation.isPending}>
            Set Maximum
          </button>
          <button onClick={handleRemoveLimit} disabled={configureMutation.isPending}>
            Remove Limit
          </button>
        </div>
      </div>
    </div>
  );
}
```

---

### Phase 5: Oversized Pages List Component

**Goal**: Display and manage oversized pages

#### Tasks:
- [ ] Create `OversizedPagesList` component
- [ ] Fetch oversized pages from `GET /api/admin/oversized-pages`
- [ ] Display table with columns:
  - Page title (link to page)
  - Current size (KB)
  - Word count
  - Author(s)
  - Due date
  - Status (pending, in_progress, resolved)
- [ ] Filter by status (dropdown)
- [ ] Sort by due date, size, etc.
- [ ] Status update functionality:
  - Dropdown to change status per page
  - Option to extend due date
  - Calls `PUT /api/admin/oversized-pages/{page_id}/status`
- [ ] Bulk actions (future enhancement)
- [ ] Pagination if many pages

#### API Functions:
```javascript
// client/src/services/api/admin.js
export async function fetchOversizedPages(token, filters = {}) {
  const params = new URLSearchParams();
  if (filters.status) params.append('status', filters.status);
  if (filters.limit) params.append('limit', filters.limit);
  if (filters.offset) params.append('offset', filters.offset);

  const response = await apiClient.get(
    `/admin/oversized-pages?${params.toString()}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
}

export function useOversizedPages(filters) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['admin', 'oversized-pages', filters],
    queryFn: () => fetchOversizedPages(token, filters),
    enabled: !!token,
  });
}

export async function updateOversizedPageStatus(pageId, status, extendDueDate, token) {
  const response = await apiClient.put(
    `/admin/oversized-pages/${pageId}/status`,
    {
      status,
      extend_due_date: extendDueDate?.toISOString(),
    },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
}

export function useUpdateOversizedPageStatus() {
  const { token } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ pageId, status, extendDueDate }) =>
      updateOversizedPageStatus(pageId, status, extendDueDate, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'oversized-pages'] });
    },
  });
}
```

#### Component:
```jsx
// client/src/components/admin/OversizedPagesList.jsx
export function OversizedPagesList() {
  const [statusFilter, setStatusFilter] = useState('all');
  const filters = statusFilter !== 'all' ? { status: statusFilter } : {};

  const { data, isLoading } = useOversizedPages(filters);
  const updateStatusMutation = useUpdateOversizedPageStatus();
  const { showSuccess, showError } = useNotificationContext();

  const handleStatusChange = (pageId, newStatus, extendDueDate) => {
    updateStatusMutation.mutate(
      { pageId, status: newStatus, extendDueDate },
      {
        onSuccess: () => showSuccess('Status updated'),
        onError: (error) => showError(error.response?.data?.error || 'Failed to update'),
      }
    );
  };

  if (isLoading) return <Loading />;

  return (
    <div className="arc-oversized-pages">
      <h2>Oversized Pages</h2>
      <div className="arc-filters">
        <label>
          Filter by Status:
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="all">All</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
          </select>
        </label>
      </div>
      <table className="arc-oversized-table">
        <thead>
          <tr>
            <th>Page Title</th>
            <th>Size (KB)</th>
            <th>Word Count</th>
            <th>Authors</th>
            <th>Due Date</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {data?.pages?.map(page => (
            <OversizedPageRow
              key={page.id}
              page={page}
              onStatusChange={handleStatusChange}
            />
        </tbody>
      </table>
    </div>
  );
}
```

---

## Component Structure

```
client/src/
  pages/
    AdminDashboardPage.jsx
    AdminDashboardPage.css
  components/
    admin/
      DashboardStats.jsx
      DashboardStats.css
      FileUploadConfig.jsx
      FileUploadConfig.css
      PageSizeMonitoring.jsx
      PageSizeMonitoring.css
      SizeChart.jsx
      SizeChart.css
      OversizedPagesList.jsx
      OversizedPagesList.css
      OversizedPageRow.jsx
      StatCard.jsx
      UserRoleCard.jsx
  services/
    api/
      admin.js
```

---

## API Integration

### Authentication
- All endpoints require admin role
- JWT token in `Authorization: Bearer <token>` header
- Handle 401/403 errors (redirect to home or show error)

### Error Handling
- User-friendly error messages
- Loading states for all async operations
- Retry logic for failed requests
- Network error handling

---

## Testing Strategy

### Unit Tests
- Component tests for each admin component
- API function tests (mocked)
- Form validation tests
- Error handling tests

### Integration Tests
- Admin dashboard access (role check)
- Configuration save flows
- Status update flows
- Chart rendering tests

### Manual Testing Checklist
- [ ] Admin can access dashboard
- [ ] Non-admin redirected
- [ ] Stats display correctly
- [ ] Upload size configuration saves
- [ ] Page size limit configuration saves
- [ ] Charts render correctly
- [ ] Oversized pages list displays
- [ ] Status updates work
- [ ] Notifications appear on success/error

---

## Styling Notes

- Use consistent admin dashboard styling
- Charts should be responsive
- Tables should be scrollable on mobile
- Form inputs should match existing design system
- Status badges with color coding (pending=yellow, in_progress=blue, resolved=green)

---

## Related Documentation

- [Wiki Admin Dashboard](wiki-admin-dashboard.md) - Feature specification
- [Wiki API Documentation](api/wiki-api.md) - Complete API reference
- [Wiki UI Implementation Guide](wiki-ui-implementation-guide.md) - General UI patterns
