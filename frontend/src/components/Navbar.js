import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { Mountain, User, LogOut, LayoutDashboard, Store, Compass, Shield, Menu } from 'lucide-react';
import { useState } from 'react';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <nav className="fixed top-0 w-full z-50 bg-background/95 backdrop-blur-md border-b border-border" data-testid="navbar">
      <div className="max-w-7xl mx-auto px-6 flex items-center justify-between h-16">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2" data-testid="nav-logo">
          <Mountain className="w-6 h-6 text-primary" strokeWidth={2} />
          <span className="font-heading font-extrabold text-lg text-foreground">Ladakh Moto</span>
        </Link>

        {/* Center Links */}
        <div className="hidden md:flex items-center gap-8">
          <Link to="/marketplace" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors" data-testid="nav-bikes">
            Explore
          </Link>
          {user?.role === 'shop_owner' && (
            <Link to="/shop" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors" data-testid="nav-shop">
              My Shop
            </Link>
          )}
          {user?.role === 'travel_agent' && (
            <Link to="/travel-agent" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors" data-testid="nav-travel-agent">
              Agent Portal
            </Link>
          )}
          {user?.role === 'admin' && (
            <Link to="/admin" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors" data-testid="nav-admin">
              Admin
            </Link>
          )}
        </div>

        {/* Right Side */}
        <div className="flex items-center gap-3">
          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="rounded-full px-3 py-2 h-auto gap-2 border-border hover:shadow-md transition-shadow" data-testid="user-menu-btn">
                  <Menu className="w-4 h-4 text-muted-foreground" />
                  <div className="w-7 h-7 rounded-full bg-foreground/10 flex items-center justify-center">
                    <User className="w-4 h-4 text-foreground" />
                  </div>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 bg-background border-border rounded-xl shadow-xl p-1" data-testid="user-dropdown">
                <DropdownMenuLabel className="px-3 py-2">
                  <p className="text-sm font-semibold">{user.name}</p>
                  <p className="text-xs text-muted-foreground">{user.email}</p>
                </DropdownMenuLabel>
                <DropdownMenuSeparator className="bg-border" />
                {user.role === 'shop_owner' ? (
                  <DropdownMenuItem onClick={() => navigate('/shop')} className="gap-2 cursor-pointer rounded-lg mx-1" data-testid="menu-shop">
                    <Store className="w-4 h-4" /> My Shop
                  </DropdownMenuItem>
                ) : user.role === 'travel_agent' ? (
                  <DropdownMenuItem onClick={() => navigate('/travel-agent')} className="gap-2 cursor-pointer rounded-lg mx-1" data-testid="menu-agent">
                    <Compass className="w-4 h-4" /> Agent Portal
                  </DropdownMenuItem>
                ) : user.role === 'admin' ? (
                  <DropdownMenuItem onClick={() => navigate('/admin')} className="gap-2 cursor-pointer rounded-lg mx-1" data-testid="menu-admin">
                    <Shield className="w-4 h-4" /> Admin Panel
                  </DropdownMenuItem>
                ) : (
                  <DropdownMenuItem onClick={() => navigate('/dashboard')} className="gap-2 cursor-pointer rounded-lg mx-1" data-testid="menu-dashboard">
                    <LayoutDashboard className="w-4 h-4" /> Dashboard
                  </DropdownMenuItem>
                )}
                <DropdownMenuSeparator className="bg-border" />
                <DropdownMenuItem onClick={handleLogout} className="gap-2 cursor-pointer rounded-lg mx-1 text-destructive" data-testid="menu-logout">
                  <LogOut className="w-4 h-4" /> Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Button
              onClick={() => navigate('/login')}
              className="bg-primary text-white hover:bg-primary/90 font-semibold px-5 py-2 rounded-lg text-sm"
              data-testid="nav-signin-btn"
            >
              Sign In
            </Button>
          )}
        </div>
      </div>
    </nav>
  );
}
