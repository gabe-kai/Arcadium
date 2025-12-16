import React from 'react';
import { Header } from './Header';
import { Footer } from './Footer';

export function Layout({ sidebar, rightSidebar, children }) {
  return (
    <div className="arc-app">
      <Header />
      <div className={`arc-main ${rightSidebar ? 'arc-main-with-right-sidebar' : ''}`}>
        {sidebar && <aside className="arc-sidebar arc-sidebar-left">{sidebar}</aside>}
        <main className="arc-content">{children}</main>
        {rightSidebar && <aside className="arc-sidebar arc-sidebar-right">{rightSidebar}</aside>}
      </div>
      <Footer />
    </div>
  );
}
