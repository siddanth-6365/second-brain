'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Brain, Search, Network, MessageSquare, BarChart3, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useAuth } from '@/components/auth-provider'

export function Navigation() {
  const pathname = usePathname()
  const { user, signOut, loading } = useAuth()

  const routes = [
    {
      href: '/',
      label: 'Home',
      icon: Brain,
      active: pathname === '/'
    },
    {
      href: '/ingest',
      label: 'Add Memory',
      icon: Plus,
      active: pathname === '/ingest'
    },
    {
      href: '/search',
      label: 'Search',
      icon: Search,
      active: pathname === '/search'
    },
    {
      href: '/graph',
      label: 'Graph',
      icon: Network,
      active: pathname === '/graph'
    },
    {
      href: '/chat',
      label: 'Chat',
      icon: MessageSquare,
      active: pathname === '/chat'
    },
    {
      href: '/dashboard',
      label: 'Dashboard',
      icon: BarChart3,
      active: pathname === '/dashboard'
    }
  ]

  return (
    <nav className="border-b border-white/10 bg-white/5 backdrop-blur-xl sticky top-0 z-50 shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between gap-4">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity group">
            <div className="relative">
              <div className="absolute inset-0 bg-blue-500 blur-xl opacity-50 rounded-full group-hover:opacity-75 transition-opacity"></div>
              <Brain className="w-8 h-8 text-blue-400 relative z-10 drop-shadow-lg" />
            </div>
            <span className="text-xl font-bold text-white drop-shadow-lg">Second Brain</span>
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center gap-2">
            {routes.map((route) => {
              const Icon = route.icon
              return (
                <Link
                  key={route.href}
                  href={route.href}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-xl transition-all duration-200",
                    route.active
                      ? "bg-white/20 text-white backdrop-blur-md shadow-lg border border-white/20"
                      : "text-white/70 hover:bg-white/10 hover:text-white hover:backdrop-blur-md"
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-sm font-medium">{route.label}</span>
                </Link>
              )
            })}
          </div>

          {/* Auth Actions */}
          <div className="flex items-center gap-3">
            {user ? (
              <>
                <div className="hidden md:flex flex-col text-right">
                  <span className="text-xs text-white/50">Logged in as</span>
                  <span className="text-sm font-medium text-white truncate max-w-[180px]">
                    {user.email}
                  </span>
                </div>
                <Button
                  variant="outline"
                  className="border-white/20 text-white hover:bg-white/10"
                  disabled={loading}
                  onClick={() => signOut()}
                >
                  Logout
                </Button>
              </>
            ) : (
              <Button className="bg-blue-600 hover:bg-blue-700" asChild>
                <Link href="/login">Login</Link>
              </Button>
            )}
          </div>
        </div>

        {/* Mobile Menu */}
        <div className="md:hidden pb-4 space-y-2">
          {routes.map((route) => {
            const Icon = route.icon
            return (
              <Link
                key={route.href}
                href={route.href}
                className={cn(
                  "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200",
                  route.active
                    ? "bg-white/20 text-white backdrop-blur-md shadow-lg border border-white/20"
                    : "text-white/70 hover:bg-white/10 hover:text-white hover:backdrop-blur-md"
                )}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{route.label}</span>
              </Link>
            )
          })}
        </div>
      </div>
    </nav>
  )
}
