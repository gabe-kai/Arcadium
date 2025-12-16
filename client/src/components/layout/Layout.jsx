import React from 'react';
import { Header } from './Header';
import { Footer } from './Footer';

export function Layout({ sidebar, children }) {
  return (
    <div className="arc-app">
      <Header />
      <div className="arc-main">
        {sidebar && <aside className="arc-sidebar">{sidebar}</aside>}
        <main className="arc-content">{children}</main>
      </div>
      <Footer />
    </div>
  );
}
