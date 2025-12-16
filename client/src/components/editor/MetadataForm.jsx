import React, { useState, useEffect, useRef } from 'react';
import { generateSlug } from '../../utils/slug';
import { searchPages, validateSlug } from '../../services/api/pages';

/**
 * MetadataForm component for editing page metadata
 * 
 * Fields:
 * - Title (required)
 * - Slug (auto-generated from title, editable)
 * - Parent page (searchable dropdown)
 * - Section (text input)
 * - Order (number input)
 * - Status (published/draft toggle)
 */
export function MetadataForm({ 
  initialData = {}, 
  onChange, 
  errors = {},
  isNewPage = false,
  excludePageId = null 
}) {
  const safeInitialData = initialData || {};
  const [title, setTitle] = useState(safeInitialData.title || '');
  const [slug, setSlug] = useState(safeInitialData.slug || '');
  const [parentId, setParentId] = useState(safeInitialData.parent_id || '');
  const [parentSearch, setParentSearch] = useState('');
  const [parentOptions, setParentOptions] = useState([]);
  const [section, setSection] = useState(safeInitialData.section || '');
  const [order, setOrder] = useState(safeInitialData.order !== undefined ? safeInitialData.order : '');
  const [status, setStatus] = useState(safeInitialData.status || 'draft');
  const [slugValidation, setSlugValidation] = useState({ valid: true, message: '' });
  const [isValidatingSlug, setIsValidatingSlug] = useState(false);
  const [showParentDropdown, setShowParentDropdown] = useState(false);
  
  const slugValidationTimerRef = useRef(null);
  const parentSearchTimerRef = useRef(null);
  const parentDropdownRef = useRef(null);

  // Auto-generate slug from title
  useEffect(() => {
    if (isNewPage && title && !slug) {
      const generated = generateSlug(title);
      setSlug(generated);
    } else if (title && !slug) {
      // For existing pages, only auto-generate if slug is empty
      const generated = generateSlug(title);
      setSlug(generated);
    }
  }, [title, isNewPage, slug]);

  // Validate slug when it changes
  useEffect(() => {
    if (slugValidationTimerRef.current) {
      clearTimeout(slugValidationTimerRef.current);
    }

    if (slug && slug.trim()) {
      setIsValidatingSlug(true);
      slugValidationTimerRef.current = setTimeout(() => {
        validateSlug(slug.trim(), excludePageId).then((result) => {
          setSlugValidation(result);
          setIsValidatingSlug(false);
        });
      }, 500); // Debounce validation
    } else {
      setSlugValidation({ valid: false, message: 'Slug is required' });
      setIsValidatingSlug(false);
    }

    return () => {
      if (slugValidationTimerRef.current) {
        clearTimeout(slugValidationTimerRef.current);
      }
    };
  }, [slug, excludePageId]);

  // Search parent pages
  useEffect(() => {
    if (parentSearchTimerRef.current) {
      clearTimeout(parentSearchTimerRef.current);
    }

    if (parentSearch.trim().length > 0) {
      parentSearchTimerRef.current = setTimeout(() => {
        searchPages(parentSearch).then((pages) => {
          setParentOptions(pages);
          setShowParentDropdown(true);
        });
      }, 300); // Debounce search
    } else {
      setParentOptions([]);
      setShowParentDropdown(false);
    }

    return () => {
      if (parentSearchTimerRef.current) {
        clearTimeout(parentSearchTimerRef.current);
      }
    };
  }, [parentSearch]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (parentDropdownRef.current && !parentDropdownRef.current.contains(event.target)) {
        setShowParentDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Notify parent of changes
  useEffect(() => {
    if (onChange) {
      onChange({
        title: title.trim(),
        slug: slug.trim(),
        parent_id: parentId || null,
        section: section.trim() || null,
        order: order !== '' ? parseInt(order, 10) : null,
        status,
      });
    }
  }, [title, slug, parentId, section, order, status, onChange]);

  // Update form when initialData changes
  useEffect(() => {
    const safeData = initialData || {};
    if (safeData.title !== undefined) setTitle(safeData.title || '');
    if (safeData.slug !== undefined) setSlug(safeData.slug || '');
    if (safeData.parent_id !== undefined) setParentId(safeData.parent_id || '');
    if (safeData.section !== undefined) setSection(safeData.section || '');
    if (safeData.order !== undefined) setOrder(safeData.order !== null ? safeData.order : '');
    if (safeData.status !== undefined) setStatus(safeData.status || 'draft');
  }, [initialData]);

  const handleTitleChange = (e) => {
    const newTitle = e.target.value;
    setTitle(newTitle);
    
    // Auto-generate slug if it hasn't been manually edited
    if (isNewPage || !slug || slug === generateSlug(title)) {
      const generated = generateSlug(newTitle);
      setSlug(generated);
    }
  };

  const handleSlugChange = (e) => {
    setSlug(e.target.value);
  };

  const handleParentSelect = (page) => {
    setParentId(page.id);
    setParentSearch(page.title);
    setShowParentDropdown(false);
  };

  const handleClearParent = () => {
    setParentId('');
    setParentSearch('');
    setParentOptions([]);
  };

  const selectedParent = parentOptions.find(p => p.id === parentId);

  return (
    <div className="arc-metadata-form">
      <h3 className="arc-metadata-form-title">Page Metadata</h3>
      
      {/* Title */}
      <div className="arc-metadata-form-field">
        <label htmlFor="metadata-title" className="arc-metadata-form-label">
          Title <span className="arc-metadata-form-required">*</span>
        </label>
        <input
          id="metadata-title"
          type="text"
          className={`arc-metadata-form-input ${errors.title ? 'arc-metadata-form-input-error' : ''}`}
          value={title}
          onChange={handleTitleChange}
          placeholder="Enter page title"
          required
        />
        {errors.title && (
          <span className="arc-metadata-form-error">{errors.title}</span>
        )}
      </div>

      {/* Slug */}
      <div className="arc-metadata-form-field">
        <label htmlFor="metadata-slug" className="arc-metadata-form-label">
          Slug <span className="arc-metadata-form-required">*</span>
        </label>
        <div className="arc-metadata-form-slug-wrapper">
          <input
            id="metadata-slug"
            type="text"
            className={`arc-metadata-form-input ${errors.slug || !slugValidation.valid ? 'arc-metadata-form-input-error' : ''} ${slugValidation.valid && slug ? 'arc-metadata-form-input-valid' : ''}`}
            value={slug}
            onChange={handleSlugChange}
            placeholder="url-friendly-slug"
            required
          />
          {isValidatingSlug && (
            <span className="arc-metadata-form-validation">Validating...</span>
          )}
          {!isValidatingSlug && slug && (
            <span className={`arc-metadata-form-validation ${slugValidation.valid ? 'arc-metadata-form-validation-valid' : 'arc-metadata-form-validation-error'}`}>
              {slugValidation.message || (slugValidation.valid ? '✓ Available' : '✗ Invalid')}
            </span>
          )}
        </div>
        {errors.slug && (
          <span className="arc-metadata-form-error">{errors.slug}</span>
        )}
        {!slugValidation.valid && slugValidation.message && (
          <span className="arc-metadata-form-error">{slugValidation.message}</span>
        )}
      </div>

      {/* Parent Page */}
      <div className="arc-metadata-form-field">
        <label htmlFor="metadata-parent" className="arc-metadata-form-label">
          Parent Page
        </label>
        <div className="arc-metadata-form-parent-wrapper" ref={parentDropdownRef}>
          <input
            id="metadata-parent"
            type="text"
            className="arc-metadata-form-input"
            value={parentSearch}
            onChange={(e) => setParentSearch(e.target.value)}
            onFocus={() => {
              if (parentOptions.length > 0) {
                setShowParentDropdown(true);
              }
            }}
            placeholder="Search for parent page..."
          />
          {selectedParent && (
            <button
              type="button"
              className="arc-metadata-form-clear"
              onClick={handleClearParent}
              title="Clear parent"
            >
              ×
            </button>
          )}
          {showParentDropdown && parentOptions.length > 0 && (
            <div className="arc-metadata-form-dropdown">
              {parentOptions.map((page) => (
                <button
                  key={page.id}
                  type="button"
                  className={`arc-metadata-form-dropdown-item ${page.id === parentId ? 'arc-metadata-form-dropdown-item-selected' : ''}`}
                  onClick={() => handleParentSelect(page)}
                >
                  <span className="arc-metadata-form-dropdown-title">{page.title}</span>
                  {page.section && (
                    <span className="arc-metadata-form-dropdown-section">{page.section}</span>
                  )}
                </button>
              ))}
            </div>
          )}
          {showParentDropdown && parentSearch.trim().length > 0 && parentOptions.length === 0 && (
            <div className="arc-metadata-form-dropdown">
              <div className="arc-metadata-form-dropdown-empty">No pages found</div>
            </div>
          )}
        </div>
        {errors.parent_id && (
          <span className="arc-metadata-form-error">{errors.parent_id}</span>
        )}
      </div>

      {/* Section */}
      <div className="arc-metadata-form-field">
        <label htmlFor="metadata-section" className="arc-metadata-form-label">
          Section
        </label>
        <input
          id="metadata-section"
          type="text"
          className="arc-metadata-form-input"
          value={section}
          onChange={(e) => setSection(e.target.value)}
          placeholder="e.g., Game Rules, Lore, Mechanics"
        />
        {errors.section && (
          <span className="arc-metadata-form-error">{errors.section}</span>
        )}
      </div>

      {/* Order */}
      <div className="arc-metadata-form-field">
        <label htmlFor="metadata-order" className="arc-metadata-form-label">
          Order
        </label>
        <input
          id="metadata-order"
          type="number"
          min="0"
          className={`arc-metadata-form-input ${errors.order ? 'arc-metadata-form-input-error' : ''}`}
          value={order}
          onChange={(e) => {
            const value = e.target.value;
            if (value === '' || (!isNaN(value) && parseInt(value, 10) >= 0)) {
              setOrder(value);
            }
          }}
          placeholder="0"
        />
        <span className="arc-metadata-form-help">
          Lower numbers appear first in navigation
        </span>
        {errors.order && (
          <span className="arc-metadata-form-error">{errors.order}</span>
        )}
      </div>

      {/* Status */}
      <div className="arc-metadata-form-field">
        <label className="arc-metadata-form-label">Status</label>
        <div className="arc-metadata-form-status-group">
          <label className="arc-metadata-form-radio">
            <input
              type="radio"
              name="status"
              value="draft"
              checked={status === 'draft'}
              onChange={(e) => setStatus(e.target.value)}
            />
            <span>Draft</span>
          </label>
          <label className="arc-metadata-form-radio">
            <input
              type="radio"
              name="status"
              value="published"
              checked={status === 'published'}
              onChange={(e) => setStatus(e.target.value)}
            />
            <span>Published</span>
          </label>
        </div>
        {errors.status && (
          <span className="arc-metadata-form-error">{errors.status}</span>
        )}
      </div>
    </div>
  );
}
