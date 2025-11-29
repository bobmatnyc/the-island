import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import { Home } from '@/pages/Home'
import { Entities } from '@/pages/Entities'
import { EntityDetail } from '@/pages/EntityDetail'
import { Documents } from '@/pages/Documents'
import { DocumentDetail } from '@/pages/DocumentDetail'
import { Network } from '@/pages/Network'
import { Timeline } from '@/pages/Timeline'
import { Flights } from '@/pages/Flights'
import { Activity } from '@/pages/Activity'
import { Matrix } from '@/pages/Matrix'
import { NewsPage } from '@/pages/NewsPage'
import { ArticleDetailPage } from '@/pages/ArticleDetailPage'
import { Analytics } from '@/pages/Analytics'
import { AdvancedSearch } from '@/pages/AdvancedSearch'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          {/* Redirect old dashboard route to home */}
          <Route path="dashboard" element={<Navigate to="/" replace />} />
          <Route path="entities" element={<Entities />} />
          {/* Support both legacy ID-based and new GUID/name-based URLs */}
          <Route path="entities/:guid/:name?" element={<EntityDetail />} />
          {/* Legacy route for backward compatibility - redirects to new format if GUID available */}
          <Route path="entities-legacy/:id" element={<EntityDetail />} />
          <Route path="documents" element={<Documents />} />
          <Route path="documents/:id" element={<DocumentDetail />} />
          <Route path="network" element={<Network />} />
          <Route path="timeline" element={<Timeline />} />
          <Route path="flights" element={<Flights />} />
          <Route path="activity" element={<Activity />} />
          <Route path="matrix" element={<Matrix />} />
          <Route path="news" element={<Navigate to="/timeline" replace />} />
          <Route path="news-legacy" element={<NewsPage />} />
          <Route path="news/:articleId" element={<ArticleDetailPage />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="search" element={<AdvancedSearch />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
