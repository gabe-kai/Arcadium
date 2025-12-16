import React from 'react';
import { Layout } from '../components/layout/Layout';
import { Sidebar } from '../components/layout/Sidebar';

export function SearchPage() {
  return (
    <Layout sidebar={<Sidebar />}>
      <section>
        <h1>Search</h1>
        <p>
          Global search results will appear here, powered by the wiki search
          endpoints.
        </p>
      </section>
    </Layout>
  );
}
