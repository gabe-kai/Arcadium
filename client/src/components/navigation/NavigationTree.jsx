import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useNavigationTree } from '../../services/api/pages';

const EXPANDED_STATE_KEY = 'arcadium_nav_expanded';
const SECTION_VIEW_KEY = 'arcadium_nav_section_view';
const EXPANDED_SECTIONS_KEY = 'arcadium_nav_expanded_sections';

/**
 * NavigationTree component displays hierarchical page navigation
 *
 * Features:
 * - Expandable/collapsible tree nodes
 * - Highlights current page
 * - Search/filter within tree
 * - Section grouping view
 * - Persists expanded state in localStorage
 */
export function NavigationTree() {
  const { data: tree, isLoading, isError } = useNavigationTree();
  const location = useLocation();
  const currentPageId = location.pathname.startsWith('/pages/')
    ? location.pathname.split('/pages/')[1]?.split('/')[0]
    : null;
  const [searchQuery, setSearchQuery] = useState('');
  const [sectionView, setSectionView] = useState(() => {
    // Load section view preference from localStorage, default to true
    try {
      const saved = localStorage.getItem(SECTION_VIEW_KEY);
      return saved !== null ? saved === 'true' : true;
    } catch {
      return true;
    }
  });
  const [expandedNodes, setExpandedNodes] = useState(() => {
    // Load expanded state from localStorage
    try {
      const saved = localStorage.getItem(EXPANDED_STATE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [expandedSections, setExpandedSections] = useState(() => {
    // Load expanded sections from localStorage
    try {
      const saved = localStorage.getItem(EXPANDED_SECTIONS_KEY);
      if (saved) {
        return JSON.parse(saved);
      }
      // Default: expand all sections (null means "expand all by default")
      return null;
    } catch {
      return null;
    }
  });

  // Save expanded state to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(EXPANDED_STATE_KEY, JSON.stringify(expandedNodes));
    } catch {
      // Ignore localStorage errors
    }
  }, [expandedNodes]);

  // Save expanded sections to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(EXPANDED_SECTIONS_KEY, JSON.stringify(expandedSections));
    } catch {
      // Ignore localStorage errors
    }
  }, [expandedSections]);

  // Save section view preference to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(SECTION_VIEW_KEY, String(sectionView));
    } catch {
      // Ignore localStorage errors
    }
  }, [sectionView]);

  // Toggle node expansion
  const toggleNode = (nodeId) => {
    setExpandedNodes((prev) =>
      prev.includes(nodeId)
        ? prev.filter((id) => id !== nodeId)
        : [...prev, nodeId]
    );
  };

  // Flatten tree to get all pages recursively
  const flattenTree = (nodes) => {
    const pages = [];
    const traverse = (node) => {
      pages.push(node);
      if (node.children && node.children.length > 0) {
        node.children.forEach(traverse);
      }
    };
    nodes.forEach(traverse);
    return pages;
  };

  // Group pages by section, preserving hierarchy
  const groupedBySection = useMemo(() => {
    if (!tree || !sectionView) return null;

    const allPages = flattenTree(tree);
    const groups = {};

    allPages.forEach((page) => {
      // Get section from page (stored in database from frontmatter)
      // The section field comes from the Page model's section column
      const section = page.section;

      // Determine section key - use "No Section" for pages without a section
      let sectionKey;
      if (section && typeof section === 'string' && section.trim().length > 0) {
        sectionKey = section.trim();
      } else {
        sectionKey = 'No Section';
      }

      if (!groups[sectionKey]) {
        groups[sectionKey] = [];
      }
      groups[sectionKey].push(page);
    });

    // Build tree structure for each section (preserve parent-child relationships)
    const sectionTrees = {};
    Object.keys(groups).forEach((section) => {
      const pages = groups[section];
      const pageMap = new Map();
      const roots = [];

      // Create map of all pages
      pages.forEach((page) => {
        pageMap.set(page.id, { ...page, children: [] });
      });

      // Build tree structure
      pages.forEach((page) => {
        const node = pageMap.get(page.id);
        if (page.parent_id && pageMap.has(page.parent_id)) {
          // Has parent in same section
          const parent = pageMap.get(page.parent_id);
          parent.children.push(node);
        } else {
          // Root page in this section
          roots.push(node);
        }
      });

      // Sort roots and children by title
      const sortNodes = (nodes) => {
        nodes.sort((a, b) => a.title.localeCompare(b.title));
        nodes.forEach((node) => {
          if (node.children.length > 0) {
            sortNodes(node.children);
          }
        });
      };
      sortNodes(roots);

      sectionTrees[section] = roots;
    });

    return sectionTrees;
  }, [tree, sectionView]);

  // Filter tree based on search query
  const filteredTree = useMemo(() => {
    if (!tree || !searchQuery.trim()) {
      return tree;
    }

    const query = searchQuery.toLowerCase();
    const filterNode = (node) => {
      const matches = node.title.toLowerCase().includes(query);
      const filteredChildren = node.children
        ? node.children.map(filterNode).filter(Boolean)
        : [];

      if (matches || filteredChildren.length > 0) {
        return {
          ...node,
          children: filteredChildren,
        };
      }
      return null;
    };

    return tree.map(filterNode).filter(Boolean);
  }, [tree, searchQuery]);

  // Filter grouped sections based on search query
  const filteredGroups = useMemo(() => {
    if (!groupedBySection || !searchQuery.trim()) {
      return groupedBySection;
    }

    const query = searchQuery.toLowerCase();
    const filtered = {};

    // Recursively filter tree nodes
    const filterTree = (nodes) => {
      const result = [];
      nodes.forEach((node) => {
        const matches = node.title.toLowerCase().includes(query);
        const filteredChildren = node.children && node.children.length > 0
          ? filterTree(node.children)
          : [];

        if (matches || filteredChildren.length > 0) {
          result.push({
            ...node,
            children: filteredChildren,
          });
        }
      });
      return result;
    };

    Object.keys(groupedBySection).forEach((section) => {
      const filteredPages = filterTree(groupedBySection[section]);
      if (filteredPages.length > 0) {
        filtered[section] = filteredPages;
      }
    });

    return filtered;
  }, [groupedBySection, searchQuery]);

  // Toggle section expansion (defined after groupedBySection)
  const toggleSection = useCallback((sectionName) => {
    setExpandedSections((prev) => {
      // If prev is null, initialize with all sections except the one being toggled
      if (prev === null) {
        // Get all section names from current groupedBySection
        const allSections = groupedBySection ? Object.keys(groupedBySection) : [];
        return allSections.filter((name) => name !== sectionName);
      }
      // Otherwise toggle normally
      return prev.includes(sectionName)
        ? prev.filter((name) => name !== sectionName)
        : [...prev, sectionName];
    });
  }, [groupedBySection]);

  // Initialize expanded sections to all sections on first load (if null)
  // Exception: "Regression-Testing" section is collapsed by default
  useEffect(() => {
    if (expandedSections === null && groupedBySection) {
      const allSections = Object.keys(groupedBySection);
      // Exclude "Regression-Testing" from default expanded sections
      const defaultExpanded = allSections.filter((section) => section !== 'Regression-Testing');
      setExpandedSections(defaultExpanded);
    }
  }, [expandedSections, groupedBySection]);

  // Auto-expand path to current page
  useEffect(() => {
    if (!tree || !currentPageId) return;

    const findPathToPage = (nodes, targetId, path = []) => {
      for (const node of nodes) {
        const newPath = [...path, node.id];
        if (node.id === targetId) {
          return newPath;
        }
        if (node.children) {
          const found = findPathToPage(node.children, targetId, newPath);
          if (found) return found;
        }
      }
      return null;
    };

    const path = findPathToPage(tree, currentPageId);
    if (path && path.length > 0) {
      // Expand all nodes in the path (except the current page itself)
      const pathToExpand = path.slice(0, -1);
      setExpandedNodes((prev) => {
        const merged = new Set([...prev, ...pathToExpand]);
        return Array.from(merged);
      });
    }

    // Also expand the section containing the current page
    if (sectionView && groupedBySection) {
      for (const [section, pages] of Object.entries(groupedBySection)) {
        const findInSection = (nodes) => {
          for (const node of nodes) {
            if (node.id === currentPageId) {
              return true;
            }
            if (node.children && node.children.length > 0) {
              if (findInSection(node.children)) {
                return true;
              }
            }
          }
          return false;
        };
        if (findInSection(pages)) {
          setExpandedSections((prev) => {
            if (prev === null) {
              // Initialize with all sections
              const allSections = Object.keys(groupedBySection);
              return allSections;
            }
            if (!prev.includes(section)) {
              return [...prev, section];
            }
            return prev;
          });
          // Also expand all parent nodes in the path
          break;
        }
      }
    }
  }, [tree, currentPageId, sectionView, groupedBySection]);

  // Auto-expand nodes when searching
  useEffect(() => {
    if (searchQuery.trim() && filteredTree && filteredTree.length > 0) {
      const autoExpandIds = new Set();
      const collectIds = (nodes) => {
        nodes.forEach((node) => {
          if (node.children && node.children.length > 0) {
            autoExpandIds.add(node.id);
            collectIds(node.children);
          }
        });
      };
      collectIds(filteredTree);

      // Merge with existing expanded nodes
      if (autoExpandIds.size > 0) {
        setExpandedNodes((prev) => {
          const merged = new Set([...prev, ...autoExpandIds]);
          return Array.from(merged);
        });
      }
    }
  }, [searchQuery, filteredTree]);

  if (isLoading) {
    return (
      <div className="arc-nav-tree">
        <p className="arc-muted">Loading navigation...</p>
      </div>
    );
  }

  if (isError || !tree) {
    return (
      <div className="arc-nav-tree">
        <p className="arc-error">Failed to load navigation</p>
      </div>
    );
  }

  return (
    <nav className="arc-nav-tree" aria-label="Page navigation">
      <div className="arc-nav-tree-search">
        <input
          type="search"
          placeholder="Search pages..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="arc-nav-tree-search-input"
        />
      </div>

      <div className="arc-nav-tree-controls">
        <label className="arc-nav-tree-toggle-label">
          <input
            type="checkbox"
            checked={sectionView}
            onChange={(e) => setSectionView(e.target.checked)}
            className="arc-nav-tree-toggle-checkbox"
          />
          <span className="arc-nav-tree-toggle-text">Section</span>
        </label>
      </div>

      {sectionView && filteredGroups ? (
        Object.keys(filteredGroups).length > 0 ? (
          <ul className="arc-nav-tree-list">
            {Object.keys(filteredGroups)
              .sort((a, b) => {
                // Sort "No Section" to the top
                if (a === 'No Section') return -1;
                if (b === 'No Section') return 1;
                return a.localeCompare(b);
              })
              .map((section) => (
                <SectionGroup
                  key={section}
                  section={section}
                  pages={filteredGroups[section] || []}
                  currentPageId={currentPageId}
                  isExpanded={expandedSections === null || (expandedSections && expandedSections.includes(section))}
                  onToggle={() => toggleSection(section)}
                  expandedNodes={expandedNodes}
                  onToggleNode={toggleNode}
                />
              ))}
          </ul>
        ) : (
          <div className="arc-nav-tree-empty" style={{ padding: '1rem', color: 'var(--arc-text-subtle)', fontSize: '0.875rem' }}>
            No pages found.
          </div>
        )
      ) : (
        <ul className="arc-nav-tree-list">
          {filteredTree.map((node) => (
            <TreeNode
              key={node.id}
              node={node}
              currentPageId={currentPageId}
              expandedNodes={expandedNodes}
              onToggle={toggleNode}
              level={0}
            />
          ))}
        </ul>
      )}
    </nav>
  );
}

/**
 * Count all descendant pages recursively
 */
function countDescendantPages(node) {
  let count = 0;
  if (node.children && node.children.length > 0) {
    count += node.children.length;
    node.children.forEach((child) => {
      count += countDescendantPages(child);
    });
  }
  return count;
}

/**
 * SectionGroup component for displaying pages grouped by section
 */
function SectionGroup({ section, pages, currentPageId, isExpanded, onToggle, expandedNodes, onToggleNode }) {
  // Count total pages including children
  const countTotalPages = (nodes) => {
    let count = 0;
    nodes.forEach((node) => {
      count += 1;
      if (node.children && node.children.length > 0) {
        count += countTotalPages(node.children);
      }
    });
    return count;
  };

  const totalCount = countTotalPages(pages);

  return (
    <li className="arc-nav-tree-item">
      <div className="arc-nav-tree-section-header">
        <button
          type="button"
          className="arc-nav-tree-toggle"
          onClick={onToggle}
          aria-expanded={isExpanded}
          aria-label={isExpanded ? 'Collapse section' : 'Expand section'}
        >
          <span className="arc-nav-tree-toggle-icon">
            {isExpanded ? '▼' : '▶'}
          </span>
        </button>
        <span className="arc-nav-tree-icon" aria-hidden="true">
          📁
        </span>
        <span className="arc-nav-tree-section-name">{section}</span>
        <span className="arc-nav-tree-section-count">({totalCount})</span>
      </div>
      {isExpanded && (
        <ul className="arc-nav-tree-list arc-nav-tree-list-section">
          {pages.map((page) => (
            <TreeNode
              key={page.id}
              node={page}
              currentPageId={currentPageId}
              expandedNodes={expandedNodes}
              onToggle={onToggleNode}
              level={0}
            />
          ))}
        </ul>
      )}
    </li>
  );
}

/**
 * TreeNode component for recursive tree rendering
 */
function TreeNode({ node, currentPageId, expandedNodes, onToggle, level }) {
  const hasChildren = node.children && node.children.length > 0;
  const isExpanded = expandedNodes.includes(node.id);
  const isCurrent = currentPageId === node.id;
  const pageCount = hasChildren ? countDescendantPages(node) : 0;

  return (
    <li className="arc-nav-tree-item">
      <div
        className={`arc-nav-tree-node ${isCurrent ? 'arc-nav-tree-node-current' : ''}`}
        style={{ paddingLeft: `${level * 1.25}rem` }}
      >
        {hasChildren && (
          <button
            type="button"
            className="arc-nav-tree-toggle"
            onClick={() => onToggle(node.id)}
            aria-expanded={isExpanded}
            aria-label={isExpanded ? 'Collapse' : 'Expand'}
          >
            <span className="arc-nav-tree-toggle-icon">
              {isExpanded ? '▼' : '▶'}
            </span>
          </button>
        )}
        {!hasChildren && <span className="arc-nav-tree-spacer" />}
        <Link
          to={`/pages/${node.id}`}
          className={`arc-nav-tree-link ${isCurrent ? 'arc-nav-tree-link-current' : ''}`}
        >
          <span className="arc-nav-tree-icon" aria-hidden="true">
            {hasChildren ? '📁' : '📄'}
          </span>
          <span className="arc-nav-tree-title">{node.title}</span>
          {hasChildren && pageCount > 0 && (
            <span className="arc-nav-tree-page-count" title={`${pageCount} page${pageCount !== 1 ? 's' : ''}`}>
              ({pageCount})
            </span>
          )}
          {node.status === 'draft' && (
            <span className="arc-nav-tree-draft-badge" title="Draft">D</span>
          )}
        </Link>
      </div>
      {hasChildren && isExpanded && (
        <ul className="arc-nav-tree-list arc-nav-tree-list-nested">
          {node.children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              currentPageId={currentPageId}
              expandedNodes={expandedNodes}
              onToggle={onToggle}
              level={level + 1}
            />
          ))}
        </ul>
      )}
    </li>
  );
}
