import { Outlet } from 'react-router-dom'
import { Header } from './Header'
import { ChatSidebar } from '@/components/chat/ChatSidebar'

export function Layout() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto py-6">
        <Outlet />
      </main>
      <ChatSidebar />
    </div>
  )
}
