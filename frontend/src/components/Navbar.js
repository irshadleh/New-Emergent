import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger
} from '../components/ui/dropdown-menu';
import { Mountain, User, LogOut, LayoutDashboard, Store, Bell, Compass } from 'lucide-react';
import { useState, useEffect } from 'react';
import api from '../lib/api';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (!user) return;
    const fetchNotifs = async () => {
      try {
        const res = await api.get('/notifications?unread_only=true');
        setUnreadCount(res.data.unread_count || 0);
      } catch {}
    };
    fetchNotifs();
    const interval = setInterval(fetchNotifs, 30000);
    return () => clearInterval(interval);
  }, [user]);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <nav className="fixed top-0 w-full z-50 border-b border-white/10 bg-background/80 backdrop-blur-xl" data-testid="main-navbar">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group" data-testid="logo-link">
            <Mountain className="w-6 h-6 text-primary" strokeWidth={1.5} />
            <span className="font-heading font-bold text-lg uppercase tracking-wider text-foreground group-hover:text-primary transition-colors">
              Ladakh Moto
            </span>
          </Link>

          {/* Center nav */}
          <div className="hidden md:flex items-center gap-8">
            <Link to="/marketplace" className="text-sm font-body text-muted-foreground hover:text-primary transition-colors uppercase tracking-widest" data-testid="nav-marketplace">
              Bikes
            </Link>
            {user && (
              <Link to="/dashboard" className="text-sm font-body text-muted-foreground hover:text-primary transition-colors uppercase tracking-widest" data-testid="nav-dashboard">
                My Rides
              </Link>
            )}
            {user?.role === 'shop_owner' && (
              <Link to="/shop" className="text-sm font-body text-muted-foreground hover:text-primary transition-colors uppercase tracking-widest" data-testid="nav-shop">
                My Shop
              </Link>
            )}
            {user?.role === 'travel_agent' && (
              <Link to="/travel-agent" className="text-sm font-body text-muted-foreground hover:text-primary transition-colors uppercase tracking-widest" data-testid="nav-travel-agent">
                Agent Portal
              </Link>
            )}
          </div>

          {/* Right side */}
          <div className="flex items-center gap-3">
            {user ? (
              <>
                {/* Notification bell */}
                <button
                  onClick={() => navigate('/dashboard')}
                  className="relative p-2 text-muted-foreground hover:text-primary transition-colors"
                  data-testid="notification-bell"
                >
                  <Bell className="w-5 h-5" strokeWidth={1.5} />
                  {unreadCount > 0 && (
                    <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-destructive text-[10px] font-bold rounded-full flex items-center justify-center text-white">
                      {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                  )}
                </button>

                {/* User dropdown */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="rounded-none px-3 gap-2" data-testid="user-menu-trigger">
                      {user.profile_picture ? (
                        <img src={user.profile_picture} alt="" className="w-6 h-6 rounded-full object-cover" />
                      ) : (
                        <User className="w-4 h-4" strokeWidth={1.5} />
                      )}
                      <span className="hidden sm:inline text-sm font-body">{user.name?.split(' ')[0]}</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-48 bg-zinc-950 border-zinc-800 rounded-sm">
                    <DropdownMenuItem onClick={() => navigate('/dashboard')} className="gap-2 cursor-pointer" data-testid="menu-dashboard">
                      <LayoutDashboard className="w-4 h-4" strokeWidth={1.5} />
                      Dashboard
                    </DropdownMenuItem>
                    {user.role === 'shop_owner' ? (
                      <DropdownMenuItem onClick={() => navigate('/shop')} className="gap-2 cursor-pointer" data-testid="menu-shop">
                        <Store className="w-4 h-4" strokeWidth={1.5} />
                        My Shop
                      </DropdownMenuItem>
                    ) : user.role === 'travel_agent' ? (
                      <DropdownMenuItem onClick={() => navigate('/travel-agent')} className="gap-2 cursor-pointer" data-testid="menu-agent">
                        <Compass className="w-4 h-4" strokeWidth={1.5} />
                        Agent Portal
                      </DropdownMenuItem>
                    ) : (
                      <DropdownMenuItem onClick={() => navigate('/shop')} className="gap-2 cursor-pointer" data-testid="menu-become-owner">
                        <Store className="w-4 h-4" strokeWidth={1.5} />
                        List Your Bikes
                      </DropdownMenuItem>
                    )}
                    <DropdownMenuSeparator className="bg-zinc-800" />
                    <DropdownMenuItem onClick={handleLogout} className="gap-2 cursor-pointer text-destructive" data-testid="menu-logout">
                      <LogOut className="w-4 h-4" strokeWidth={1.5} />
                      Logout
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            ) : (
              <Button
                onClick={() => navigate('/login')}
                className="bg-primary text-primary-foreground hover:bg-primary/90 font-bold uppercase tracking-wider text-xs px-6 py-2 rounded-sm"
                data-testid="nav-login-btn"
              >
                Sign In
              </Button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
