import React from 'react';
import { NavigationTree } from '../navigation/NavigationTree';

export function SidebarPlaceholder() {
  return (
    <div className="arc-sidebar-placeholder">
      <h3>Navigation</h3>
      <p>
        Navigation tree will appear here once implemented (Phase 3 in the
        UI guide).
      </p>
    </div>
  );
}

export function Sidebar() {
  return <NavigationTree />;
}
