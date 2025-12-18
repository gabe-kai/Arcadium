import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { PageView } from './pages/PageView';
import { EditPage } from './pages/EditPage';
import { PageHistoryPage } from './pages/PageHistoryPage';
import { PageVersionView } from './pages/PageVersionView';
import { PageVersionCompare } from './pages/PageVersionCompare';
import { SearchPage } from './pages/SearchPage';
import { IndexPage } from './pages/IndexPage';
import { SignInPage } from './pages/SignInPage';

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
        <Route path="/pages/:pageId/history" element={<PageHistoryPage />} />
        <Route path="/pages/:pageId/versions/:version" element={<PageVersionView />} />
        <Route path="/pages/:pageId/versions/compare" element={<PageVersionCompare />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/index" element={<IndexPage />} />
        <Route path="/signin" element={<SignInPage />} />
        {/* Fallback */}
        <Route path="*" element={<HomePage />} />
      </Routes>
    </BrowserRouter>
  );
}
