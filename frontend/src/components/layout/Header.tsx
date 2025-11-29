import { Link } from 'react-router-dom'
import { ChevronDown, AlertCircle } from 'lucide-react'
import { useState, useEffect } from 'react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Alert, AlertDescription } from '@/components/ui/alert'

export function Header() {
  const [backendStatus, setBackendStatus] = useState<'online' | 'offline' | 'checking'>('checking')

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8081'
        const response = await fetch(`${API_BASE_URL}/api/timeline`)
        if (response.ok) {
          setBackendStatus('online')
        } else {
          setBackendStatus('offline')
        }
      } catch (error) {
        setBackendStatus('offline')
      }
    }

    checkBackend()
    const interval = setInterval(checkBackend, 30000) // Check every 30 seconds

    return () => clearInterval(interval)
  }, [])

  return (
    <>
      {backendStatus === 'offline' && (
        <Alert variant="destructive" className="rounded-none border-x-0 border-t-0">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Backend server is offline. Some features may not work correctly.
          </AlertDescription>
        </Alert>
      )}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center">
        <div className="mr-4 flex">
          <Link to="/" className="mr-6 flex items-center space-x-2">
            <span className="font-bold text-xl">Epstein Archive</span>
          </Link>
        </div>
        <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
          <nav className="flex items-center space-x-6 text-sm font-medium">
            <Link
              to="/"
              className="transition-colors hover:text-foreground/80 text-foreground/60"
            >
              Home
            </Link>
            <Link
              to="/timeline"
              className="transition-colors hover:text-foreground/80 text-foreground/60"
            >
              Timeline
            </Link>
            <Link
              to="/entities"
              className="transition-colors hover:text-foreground/80 text-foreground/60"
            >
              Entities
            </Link>
            <Link
              to="/flights"
              className="transition-colors hover:text-foreground/80 text-foreground/60"
            >
              Flights
            </Link>
            <Link
              to="/documents"
              className="transition-colors hover:text-foreground/80 text-foreground/60"
            >
              Documents
            </Link>
            <DropdownMenu>
              <DropdownMenuTrigger className="flex items-center gap-1 transition-colors hover:text-foreground/80 text-foreground/60 outline-none">
                Visualizations
                <ChevronDown className="h-4 w-4" />
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem asChild>
                  <Link to="/analytics" className="cursor-pointer">
                    Analytics Dashboard
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link to="/network" className="cursor-pointer">
                    Network Graph
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link to="/matrix" className="cursor-pointer">
                    Adjacency Matrix
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link to="/activity" className="cursor-pointer">
                    Calendar Heatmap
                  </Link>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </nav>
        </div>
      </div>
    </header>
    </>
  )
}
