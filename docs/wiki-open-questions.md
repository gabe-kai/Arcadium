# Wiki Service - Open Questions

This document tracks questions that need clarification before implementation begins.

## Resolved Questions ✅

1. ✅ **File format details**: Markdown with YAML frontmatter - **CONFIRMED**
2. ✅ **Book-reading format**: Continuous scroll - **CONFIRMED**
3. ✅ **TOC generation**: Auto-generated only - **CONFIRMED**
4. ✅ **Index scope**: Both full-text search AND keywords - **CONFIRMED**
5. ✅ **WYSIWYG editor**: Tiptap selected - **CONFIRMED**
6. ✅ **Comment threading depth**: Maximum 5 levels - **CONFIRMED**
7. ✅ **Version history**: Full history with diffs - **CONFIRMED**

## All Questions Resolved ✅

All questions have been answered and documented. See [Wiki Service Specification](wiki-service-specification.md) for complete details.

### Summary of Decisions

1. ✅ **Page deletion**: Orphanage system with placeholder parent
2. ✅ **Slug generation**: Auto-generate, allow override, enforce uniqueness
3. ✅ **Section creation**: Writers can create sections
4. ✅ **Image storage**: Centralized in `data/uploads/images/` (UUID-based naming)
5. ✅ **File size limits**: Admin configurable (presets + custom)
6. ✅ **Search**: Full-text search (PostgreSQL relevance)
7. ✅ **Keywords**: Both automatic extraction and manual tagging
8. ✅ **Version retention**: Keep all versions
9. ✅ **Version comparison**: Both side-by-side and inline
10. ✅ **Draft status**: Yes, writers can save drafts
11. ✅ **Page visibility**: All pages public
12. ✅ **Rate limiting**: Not needed
13. ✅ **Page size limits**: Admin configurable with monitoring dashboard
14. ✅ **Section extraction**: Editor functions and TOC promotion added

## Additional Considerations

10. **Page templates**: Should writers be able to create pages from templates?
    - **Status**: Future enhancement (not in MVP)

11. **Page approval workflow**: Should writer-created pages require approval?
    - **Status**: Future enhancement (not in MVP)

12. **Watchlist**: Should users be able to watch pages for changes?
    - **Status**: Future enhancement (not in MVP)

## Next Steps

Once these questions are answered, we can proceed with implementation. The documentation has been structured to accommodate the most likely answers, but final confirmation will ensure we build exactly what's needed.
