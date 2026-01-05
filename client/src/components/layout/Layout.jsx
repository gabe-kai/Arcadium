import React, { useState, useEffect } from 'react';
import { Header } from './Header';
import { Footer } from './Footer';

export function Layout({ sidebar, rightSidebar, children }) {
  const [isMobile, setIsMobile] = useState(false);
  const [isLeftSidebarOpen, setIsLeftSidebarOpen] = useState(false);
  const [isRightSidebarOpen, setIsRightSidebarOpen] = useState(false);

  // Detect mobile viewport
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Close sidebars when clicking overlay
  const handleOverlayClick = () => {
    setIsLeftSidebarOpen(false);
    setIsRightSidebarOpen(false);
  };

  // Close sidebars on escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        setIsLeftSidebarOpen(false);
        setIsRightSidebarOpen(false);
      }
    };

    if (isMobile) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isMobile]);

  // Prevent body scroll when mobile sidebar is open
  useEffect(() => {
    if (isMobile && (isLeftSidebarOpen || isRightSidebarOpen)) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isMobile, isLeftSidebarOpen, isRightSidebarOpen]);

  const mainClasses = [
    'arc-main',
    rightSidebar ? 'arc-main-with-right-sidebar' : '',
    !sidebar ? 'arc-main-no-sidebar' : '',
  ]
    .filter(Boolean)
    .join(' ');

  const leftSidebarClasses = [
    'arc-sidebar',
    'arc-sidebar-left',
    isMobile ? 'arc-sidebar-mobile' : '',
    isMobile && isLeftSidebarOpen ? 'active' : '',
  ]
    .filter(Boolean)
    .join(' ');

  const rightSidebarClasses = [
    'arc-sidebar',
    'arc-sidebar-right',
    isMobile ? 'arc-sidebar-mobile' : '',
    isMobile && isRightSidebarOpen ? 'active' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className="arc-app">
      <Header
        onMenuToggle={() => setIsLeftSidebarOpen(!isLeftSidebarOpen)}
        isLeftSidebarOpen={isLeftSidebarOpen}
      />
      {(isLeftSidebarOpen || isRightSidebarOpen) && isMobile && (
        <div
          className={`arc-sidebar-overlay ${isLeftSidebarOpen || isRightSidebarOpen ? 'active' : ''}`}
          onClick={handleOverlayClick}
          aria-hidden="true"
        />
      )}
      <div className={mainClasses}>
        {sidebar && <aside className={leftSidebarClasses}>{sidebar}</aside>}
        <main className="arc-content">{children}</main>
        {rightSidebar && <aside className={rightSidebarClasses}>{rightSidebar}</aside>}
      </div>
      {rightSidebar && isMobile && (
        <button
          className="arc-right-sidebar-toggle"
          onClick={() => setIsRightSidebarOpen(!isRightSidebarOpen)}
          aria-label="Toggle table of contents"
          title="Table of Contents"
        >
          📑
        </button>
      )}
      <Footer />
    </div>
  );
}
