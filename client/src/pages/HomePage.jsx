import React from 'react';
import { Layout } from '../components/layout/Layout';
import { Sidebar } from '../components/layout/Sidebar';

export function HomePage() {
  return (
    <Layout sidebar={<Sidebar />}>
      <section>
        <h1>Welcome to the Arcadium Wiki</h1>
        <p>
          This is the frontend UI for the Arcadium Wiki service. Use the
          navigation tree and search to explore documentation.
        </p>
        <p>
          The UI is being implemented in phases, following the
          <code>wiki-ui-implementation-guide.md</code>.
        </p>
      </section>
    </Layout>
  );
}
