import React from 'react';
import { useParams } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Sidebar } from '../components/layout/Sidebar';

export function EditPage() {
  const { pageId } = useParams();

  return (
    <Layout sidebar={<Sidebar />}>
      <section>
        <h1>Edit Page</h1>
        <p>
          This screen will host the Tiptap-based editor and metadata form (Phases
          7-10 in the UI guide).
        </p>
        <p>
          Editing page id: <code>{pageId || 'new'}</code>
        </p>
      </section>
    </Layout>
  );
}
