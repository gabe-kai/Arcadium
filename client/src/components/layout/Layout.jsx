import React from 'react';
import { Header } from './Header';
import { Footer } from './Footer';

export function Layout({ sidebar, rightSidebar, children }) {
  const mainClasses = [
    'arc-main',
    rightSidebar ? 'arc-main-with-right-sidebar' : '',
    !sidebar ? 'arc-main-no-sidebar' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className="arc-app">
      <Header />
      <div className={mainClasses}>
        {sidebar && <aside className="arc-sidebar arc-sidebar-left">{sidebar}</aside>}
        <main className="arc-content">{children}</main>
        {rightSidebar && <aside className="arc-sidebar arc-sidebar-right">{rightSidebar}</aside>}
      </div>
      <Footer />
    </div>
  );
}
