# Wiki Service Implementation Guide

This guide provides a step-by-step approach to implementing the Wiki Service, including testing strategies to ensure all design requirements are met.

## Prerequisites

- Python 3.9+
- PostgreSQL 14+
- Docker and Docker Compose (for local development)
- Node.js 18+ (for client development, if needed)

## Implementation Phases

### Phase 1: Foundation Setup

#### 1.1 Project Structure
- [ ] Set up Flask application structure
- [ ] Configure database connection
- [ ] Set up environment variables
- [ ] Create base configuration files

#### 1.2 Database Setup
- [ ] Create database migrations for all tables:
  - `pages` (with `is_system_page` field)
  - `comments` (with `thread_depth` field)
  - `page_links`
  - `index_entries` (with `is_manual` field)
  - `page_versions`
  - `images` and `page_images`
  - `wiki_config`
  - `oversized_page_notifications`
- [ ] Create indexes as specified in architecture doc
- [ ] Set up database connection pooling

**Testing:**
```bash
# Run migration tests
pytest tests/test_migrations.py

# Verify schema matches architecture doc
python scripts/verify_schema.py
```

**Validation:** Compare database schema with `docs/architecture/wiki-architecture.md`

---

### Phase 2: Core Data Models

#### 2.1 Page Model
- [ ] Implement Page model with all fields from specification
- [ ] Add validation for slug uniqueness
- [ ] Implement parent-child relationships
- [ ] Add `is_system_page` flag handling
- [ ] Implement orphanage detection

**Testing:**
```python
# tests/test_models/test_page.py
def test_page_creation()
def test_slug_uniqueness()
def test_parent_child_relationship()
def test_orphanage_assignment()
def test_section_independence()
```

**Validation:** Check against `docs/wiki-service-specification.md` Page Structure

#### 2.2 Comment Model
- [ ] Implement Comment model
- [ ] Add thread depth calculation
- [ ] Enforce maximum depth (5 levels)
- [ ] Support recommendations flag

**Testing:**
```python
# tests/test_models/test_comment.py
def test_comment_creation()
def test_thread_depth_calculation()
def test_max_depth_enforcement()
def test_recommendation_flag()
```

**Validation:** Check against `docs/wiki-service-specification.md` Comments System

#### 2.3 Link Tracking Model
- [ ] Implement PageLink model
- [ ] Support bidirectional link tracking
- [ ] Validate link targets exist

**Testing:**
```python
# tests/test_models/test_page_link.py
def test_link_creation()
def test_bidirectional_tracking()
def test_invalid_link_handling()
```

**Validation:** Check against `docs/architecture/wiki-architecture.md` Link Tracking

#### 2.4 Version History Model
- [ ] Implement PageVersion model
- [ ] Store full content (not just diffs)
- [ ] Calculate and store diff data
- [ ] Support change summaries

**Testing:**
```python
# tests/test_models/test_page_version.py
def test_version_creation()
def test_diff_calculation()
def test_version_retention()
```

**Validation:** Check against `docs/wiki-version-history.md`

#### 2.5 Index Model
- [ ] Implement IndexEntry model
- [ ] Support both full-text and keyword entries
- [ ] Track manual vs auto-extracted keywords

**Testing:**
```python
# tests/test_models/test_index_entry.py
def test_index_entry_creation()
def test_keyword_vs_fulltext()
def test_manual_vs_auto_keywords()
```

**Validation:** Check against `docs/architecture/wiki-architecture.md` Index Entries

---

### Phase 3: File System Integration

#### 3.1 File Storage Service
- [ ] Implement file path calculation (section + parent hierarchy)
- [ ] Create file structure mirroring hierarchy
- [ ] Handle file moves when page structure changes
- [ ] Implement YAML frontmatter parsing

**Testing:**
```python
# tests/test_services/test_file_service.py
def test_file_path_calculation()
def test_directory_structure_creation()
def test_file_move_on_parent_change()
def test_frontmatter_parsing()
```

**Validation:** Check against `docs/architecture/wiki-architecture.md` File Path Calculation

#### 3.2 Markdown Processing
- [ ] Implement Markdown to HTML conversion
- [ ] Extract headings for TOC (H2-H6)
- [ ] Generate anchors from headings
- [ ] Preserve formatting

**Testing:**
```python
# tests/test_services/test_markdown_service.py
def test_markdown_to_html()
def test_toc_generation()
def test_anchor_generation()
def test_heading_levels()
```

**Validation:** Check against `docs/wiki-service-specification.md` TOC Generation

---

### Phase 4: Core Business Logic

#### 4.1 Page Service
- [ ] Implement page CRUD operations
- [ ] Handle draft vs published status
- [ ] Calculate word count and size (images excluded)
- [ ] Enforce permissions (Viewer, Player, Writer, Admin)
- [ ] Handle page deletion with orphanage

**Testing:**
```python
# tests/test_services/test_page_service.py
def test_create_page()
def test_update_page()
def test_delete_page_with_orphans()
def test_draft_visibility()
def test_permission_enforcement()
def test_size_calculation()
```

**Validation:** Check against `docs/wiki-service-specification.md` User Roles and Permissions

#### 4.2 Orphanage Service
- [ ] Create orphanage system page on first deletion
- [ ] Move orphaned pages to orphanage
- [ ] Support reassignment (individual and bulk)
- [ ] Group by original parent

**Testing:**
```python
# tests/test_services/test_orphanage_service.py
def test_orphanage_creation()
def test_orphan_assignment()
def test_reassignment()
def test_grouping_by_parent()
```

**Validation:** Check against `docs/wiki-orphanage-system.md`

#### 4.3 Link Service
- [ ] Parse Markdown for internal links
- [ ] Support formats: `[text](slug)`, `[text](slug#anchor)`, `[text](/wiki/pages/slug)`
- [ ] Track external links (not stored)
- [ ] Update bidirectional relationships
- [ ] Handle slug changes

**Testing:**
```python
# tests/test_services/test_link_service.py
def test_link_extraction()
def test_link_formats()
def test_bidirectional_tracking()
def test_slug_change_updates()
```

**Validation:** Check against `docs/architecture/wiki-architecture.md` Link Format and Parsing

#### 4.4 Search Index Service
- [ ] Implement full-text indexing (PostgreSQL)
- [ ] Implement keyword extraction (TF-IDF)
- [ ] Support manual keyword tagging
- [ ] Synchronous indexing on save
- [ ] Incremental updates

**Testing:**
```python
# tests/test_services/test_index_service.py
def test_fulltext_indexing()
def test_keyword_extraction()
def test_manual_keywords()
def test_incremental_updates()
def test_search_relevance()
```

**Validation:** Check against `docs/architecture/wiki-architecture.md` Search Indexing

#### 4.5 Version Service
- [ ] Create version on every edit
- [ ] Store full content (not just diffs)
- [ ] Calculate diff data
- [ ] Support version comparison
- [ ] Implement rollback (Writers for own pages, Admins for any)

**Testing:**
```python
# tests/test_services/test_version_service.py
def test_version_creation()
def test_diff_calculation()
def test_version_comparison()
def test_rollback_permissions()
def test_version_retention()
```

**Validation:** Check against `docs/wiki-version-history.md`

---

### Phase 5: API Endpoints

#### 5.1 Page Endpoints
- [ ] `GET /api/pages` - List with draft filtering
- [ ] `GET /api/pages/{id}` - Get single page
- [ ] `POST /api/pages` - Create page
- [ ] `PUT /api/pages/{id}` - Update page
- [ ] `DELETE /api/pages/{id}` - Delete page

**Testing:**
```python
# tests/test_api/test_page_routes.py
def test_list_pages()
def test_list_pages_with_drafts()
def test_get_page()
def test_get_draft_page_permissions()
def test_create_page()
def test_update_page()
def test_delete_page()
```

**Validation:** Check against `docs/api/wiki-api.md` Pages section

#### 5.2 Comment Endpoints
- [ ] `GET /api/pages/{id}/comments` - Get comments
- [ ] `POST /api/pages/{id}/comments` - Create comment
- [ ] `PUT /api/comments/{id}` - Update comment
- [ ] `DELETE /api/comments/{id}` - Delete comment
- [ ] Enforce 5-level depth limit

**Testing:**
```python
# tests/test_api/test_comment_routes.py
def test_get_comments()
def test_create_comment()
def test_thread_depth_enforcement()
def test_update_comment()
def test_delete_comment()
```

**Validation:** Check against `docs/api/wiki-api.md` Comments section

#### 5.3 Search Endpoints
- [ ] `GET /api/search` - Full-text search
- [ ] `GET /api/index` - Master index
- [ ] Support draft filtering

**Testing:**
```python
# tests/test_api/test_search_routes.py
def test_search_pages()
def test_search_relevance()
def test_search_draft_filtering()
def test_master_index()
```

**Validation:** Check against `docs/api/wiki-api.md` Search section

#### 5.4 Navigation Endpoints
- [ ] `GET /api/navigation` - Page hierarchy (draft filtering)
- [ ] `GET /api/pages/{id}/breadcrumb` - Breadcrumb
- [ ] `GET /api/pages/{id}/navigation` - Previous/Next

**Testing:**
```python
# tests/test_api/test_navigation_routes.py
def test_navigation_tree()
def test_navigation_draft_filtering()
def test_breadcrumb()
def test_previous_next()
```

**Validation:** Check against `docs/api/wiki-api.md` Navigation section

#### 5.5 Version History Endpoints
- [ ] `GET /api/pages/{id}/versions` - Version list
- [ ] `GET /api/pages/{id}/versions/{version}` - Get version
- [ ] `GET /api/pages/{id}/versions/compare` - Compare versions
- [ ] `POST /api/pages/{id}/versions/{version}/restore` - Rollback

**Testing:**
```python
# tests/test_api/test_version_routes.py
def test_get_version_history()
def test_get_specific_version()
def test_compare_versions()
def test_restore_version()
def test_restore_permissions()
```

**Validation:** Check against `docs/api/wiki-api.md` Version History section

#### 5.6 Orphanage Endpoints
- [ ] `GET /api/orphanage` - Get orphanage
- [ ] `POST /api/orphanage/reassign` - Reassign pages
- [ ] `POST /api/orphanage/clear` - Clear orphanage

**Testing:**
```python
# tests/test_api/test_orphanage_routes.py
def test_get_orphanage()
def test_reassign_orphaned_pages()
def test_clear_orphanage()
def test_orphanage_permissions()
```

**Validation:** Check against `docs/api/wiki-api.md` Orphanage Management section

#### 5.7 Section Extraction Endpoints
- [ ] `POST /api/pages/{id}/extract` - Extract selection
- [ ] `POST /api/pages/{id}/extract-heading` - Extract heading
- [ ] `POST /api/pages/{id}/promote-section` - Promote from TOC

**Testing:**
```python
# tests/test_api/test_extraction_routes.py
def test_extract_selection()
def test_extract_heading()
def test_promote_section()
def test_link_replacement()
```

**Validation:** Check against `docs/api/wiki-api.md` Section Extraction section

#### 5.8 Admin Endpoints
- [ ] `GET /api/admin/dashboard/stats` - Dashboard stats
- [ ] `GET /api/admin/dashboard/size-distribution` - Size charts
- [ ] `POST /api/admin/config/upload-size` - File upload config
- [ ] `POST /api/admin/config/page-size` - Page size config
- [ ] `GET /api/admin/oversized-pages` - Oversized pages list
- [ ] `PUT /api/admin/oversized-pages/{id}/status` - Update status

**Testing:**
```python
# tests/test_api/test_admin_routes.py
def test_dashboard_stats()
def test_size_distribution()
def test_upload_size_config()
def test_page_size_config()
def test_oversized_pages_list()
def test_admin_permissions()
```

**Validation:** Check against `docs/api/wiki-api.md` Admin Dashboard section

#### 5.9 File Upload Endpoints
- [ ] `POST /api/upload/image` - Upload image (UUID naming)
- [ ] Validate file size against config
- [ ] Store metadata in database

**Testing:**
```python
# tests/test_api/test_upload_routes.py
def test_image_upload()
def test_file_size_validation()
def test_uuid_naming()
def test_metadata_storage()
```

**Validation:** Check against `docs/api/wiki-api.md` File Upload section

---

### Phase 6: Sync Utility (AI Content)

#### 6.1 Sync Utility Implementation
- [ ] File scanner for markdown files
- [ ] Frontmatter parser
- [ ] Database sync logic
- [ ] Link updater
- [ ] Index updater
- [ ] Admin user assignment

**Testing:**
```python
# tests/test_sync/test_sync_utility.py
def test_file_scanning()
def test_frontmatter_parsing()
def test_database_sync()
def test_parent_slug_resolution()
def test_admin_assignment()
```

**Validation:** Check against `docs/wiki-ai-content-management.md`

---

### Phase 7: Admin Dashboard Features

#### 7.1 Size Monitoring
- [ ] Calculate page sizes (KB) and word counts
- [ ] Generate size distribution charts
- [ ] Track oversized pages
- [ ] Send notifications via Notification Service

**Testing:**
```python
# tests/test_services/test_size_monitoring.py
def test_size_calculation()
def test_size_distribution()
def test_oversized_detection()
def test_notification_triggering()
```

**Validation:** Check against `docs/wiki-admin-dashboard.md`

#### 7.2 Configuration Management
- [ ] File upload size limits (presets + custom)
- [ ] Page size limits
- [ ] Resolution due dates
- [ ] Status tracking

**Testing:**
```python
# tests/test_services/test_admin_service.py
def test_upload_size_config()
def test_page_size_config()
def test_config_persistence()
```

**Validation:** Check against `docs/wiki-admin-dashboard.md`

---

### Phase 8: Integration & Polish

#### 8.1 Auth Service Integration
- [ ] JWT token validation
- [ ] Role-based access control middleware
- [ ] User profile retrieval

**Testing:**
```python
# tests/test_integration/test_auth_integration.py
def test_jwt_validation()
def test_role_enforcement()
def test_user_profile_retrieval()
```

**Validation:** Check against `docs/services/service-dependencies.md`

#### 8.2 Notification Service Integration
- [ ] Send oversized page notifications
- [ ] Internal messaging integration

**Testing:**
```python
# tests/test_integration/test_notification_integration.py
def test_oversized_page_notification()
def test_internal_messaging()
```

**Validation:** Check against `docs/services/notification-service.md`

#### 8.3 Performance Optimization
- [ ] Cache rendered HTML
- [ ] Cache TOC generation
- [ ] Lazy-load comments
- [ ] Database query optimization

**Testing:**
```python
# tests/test_performance/test_caching.py
def test_html_caching()
def test_toc_caching()
def test_lazy_loading()
```

**Validation:** Check against `docs/architecture/wiki-architecture.md` Performance Optimizations

---

## Testing Strategy

### Unit Tests
- Test each model, service, and utility independently
- Mock external dependencies (Auth Service, Notification Service)
- Aim for >80% code coverage

### Integration Tests
- Test API endpoints with database
- Test file system operations
- Test service-to-service communication

### End-to-End Tests
- Test complete user workflows:
  - Create page → Edit → Delete
  - Comment → Reply (5 levels)
  - Search → Navigate → View
  - Admin: Configure → Monitor → Notify

### Test Data Setup
```python
# tests/fixtures/
- test_pages.json
- test_users.json
- test_comments.json
- test_links.json
```

### Continuous Testing
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Run specific phase
pytest tests/test_models/
pytest tests/test_services/
pytest tests/test_api/
```

---

## Validation Checklist

After each phase, validate against design documents:

### Specification Validation
- [ ] All user roles implemented correctly
- [ ] All permissions enforced
- [ ] All features from specification present

### API Validation
- [ ] All endpoints match API documentation
- [ ] Request/response formats correct
- [ ] Error handling matches spec
- [ ] Permissions match spec

### Architecture Validation
- [ ] Database schema matches architecture doc
- [ ] File structure matches spec
- [ ] Data flow matches diagrams
- [ ] Component structure matches

### UI Validation
- [ ] TOC generation matches UI spec
- [ ] Comment threading matches spec
- [ ] Navigation matches spec
- [ ] Editor features match spec

---

## Implementation Order Recommendation

1. **Foundation** (Phase 1-2) - Database and models
2. **Core Services** (Phase 3-4) - File system and business logic
3. **API Layer** (Phase 5) - REST endpoints
4. **Features** (Phase 6-7) - Sync utility and admin features
5. **Integration** (Phase 8) - External services and optimization

---

## Key Milestones

### Milestone 1: Basic CRUD
- Pages can be created, read, updated, deleted
- File system integration working
- Basic permissions enforced

### Milestone 2: Full Feature Set
- Comments, links, search working
- Version history implemented
- Orphanage system working

### Milestone 3: Admin Features
- Admin dashboard functional
- Size monitoring working
- Notifications integrated

### Milestone 4: Production Ready
- All tests passing
- Performance optimized
- Documentation complete

---

## Common Pitfalls to Avoid

1. **Don't skip tests** - Write tests as you implement
2. **Don't hardcode permissions** - Use middleware
3. **Don't forget draft filtering** - Check all list endpoints
4. **Don't ignore file system** - Keep files and DB in sync
5. **Don't skip validation** - Validate against design docs regularly

---

## Next Steps After Implementation

1. Code review against design documents
2. Performance testing
3. Security audit
4. User acceptance testing
5. Documentation review
6. Deployment preparation

