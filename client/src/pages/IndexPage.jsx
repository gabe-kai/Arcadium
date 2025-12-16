import React from 'react';
import { Layout } from '../components/layout/Layout';
import { Sidebar } from '../components/layout/Sidebar';

export function IndexPage() {
  return (
    <Layout sidebar={<Sidebar />}>
      <section>
        <h1>Index</h1>
        <p>
          An alphabetical index of pages will be implemented here (Phase 6: Index
          View).
        </p>
      </section>
    </Layout>
  );
}
