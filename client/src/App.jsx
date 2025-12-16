import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { PageView } from './pages/PageView';
import { EditPage } from './pages/EditPage';
import { SearchPage } from './pages/SearchPage';
import { IndexPage } from './pages/IndexPage';

export function App() {
  return (
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/pages/:pageId" element={<PageView />} />
        <Route path="/pages/:pageId/edit" element={<EditPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/index" element={<IndexPage />} />
        {/* Fallback */}
        <Route path="*" element={<HomePage />} />
      </Routes>
    </BrowserRouter>
  );
}
