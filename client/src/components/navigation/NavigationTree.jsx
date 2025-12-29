import React, { useState, useEffect, useMemo } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useNavigationTree } from '../../services/api/pages';

const EXPANDED_STATE_KEY = 'arcadium_nav_expanded';

/**
 * NavigationTree component displays hierarchical page navigation
 *
 * Features:
 * - Expandable/collapsible tree nodes
 * - Highlights current page
 * - Search/filter within tree
 * - Persists expanded state in localStorage
 */
export function NavigationTree() {
  const { data: tree, isLoading, isError } = useNavigationTree();
  const location = useLocation();
  const currentPageId = location.pathname.startsWith('/pages/')
    ? location.pathname.split('/pages/')[1]?.split('/')[0]
    : null;
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedNodes, setExpandedNodes] = useState(() => {
    // Load expanded state from localStorage
    try {
      const saved = localStorage.getItem(EXPANDED_STATE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
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

  // Toggle node expansion
  const toggleNode = (nodeId) => {
    setExpandedNodes((prev) =>
      prev.includes(nodeId)
        ? prev.filter((id) => id !== nodeId)
        : [...prev, nodeId]
    );
  };

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
  }, [tree, currentPageId]);

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
