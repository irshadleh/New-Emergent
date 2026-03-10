import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Mountain, Mail, Lock, User as UserIcon, Phone } from 'lucide-react';
import { toast } from 'sonner';
import api from '../lib/api';

export default function Login() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const getRedirectPath = (role) => {
    switch (role) {
      case 'admin': return '/admin';
      case 'shop_owner': return '/shop';
      case 'travel_agent': return '/travel-agent';
      default: return '/dashboard';
    }
  };

  // Redirect if already logged in
  if (user) {
    navigate(getRedirectPath(user.role), { replace: true });
    return null;
  }

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    const formData = new FormData(e.target);
    try {
      const res = await api.post('/auth/login', {
        email: formData.get('email'),
        password: formData.get('password')
      });
      login(res.data.user, res.data.token);
      toast.success('Welcome back!');
      navigate(getRedirectPath(res.data.user.role), { replace: true });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    const formData = new FormData(e.target);
    try {
      const res = await api.post('/auth/register', {
        email: formData.get('email'),
        password: formData.get('password'),
        name: formData.get('name'),
        role: formData.get('role') || 'customer',
        phone: formData.get('phone') || ''
      });
      login(res.data.user, res.data.token);
      toast.success('Account created!');
      navigate(getRedirectPath(res.data.user.role), { replace: true });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  const handleGoogleLogin = () => {
    const redirectUrl = window.location.origin + '/dashboard';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div className="min-h-screen bg-background pt-16 flex" data-testid="login-page">
      {/* Left side - image */}
      <div className="hidden lg:block lg:w-1/2 relative">
        <img
          src="https://images.unsplash.com/photo-1634899288126-2930c39001ab?q=80&w=1200&auto=format&fit=crop"
          alt="Ladakh landscape"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-transparent to-background" />
        <div className="absolute bottom-12 left-12 max-w-md">
          <p className="font-accent text-xl text-primary opacity-80">adventure awaits</p>
          <h2 className="font-heading font-bold text-3xl uppercase tracking-tight text-white mt-2">
            18,380 ft. Above sea level.
          </h2>
          <p className="text-sm text-white/70 font-body mt-2">Khardung La — the highest motorable pass in the world.</p>
        </div>
      </div>

      {/* Right side - auth forms */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 md:p-12">
        <div className="w-full max-w-md">
          {/* Logo */}
          <div className="flex items-center gap-2 mb-8">
            <Mountain className="w-6 h-6 text-primary" strokeWidth={1.5} />
            <span className="font-heading font-bold text-lg uppercase tracking-wider">Ladakh Moto</span>
          </div>

          <Tabs defaultValue="login" className="w-full">
            <TabsList className="w-full bg-secondary rounded-sm mb-6">
              <TabsTrigger value="login" className="flex-1 rounded-sm font-heading uppercase tracking-wider text-xs" data-testid="login-tab">
                Sign In
              </TabsTrigger>
              <TabsTrigger value="register" className="flex-1 rounded-sm font-heading uppercase tracking-wider text-xs" data-testid="register-tab">
                Create Account
              </TabsTrigger>
            </TabsList>

            <TabsContent value="login">
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <Label className="text-xs uppercase tracking-widest font-bold text-muted-foreground">Email</Label>
                  <div className="relative mt-1">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" strokeWidth={1.5} />
                    <Input name="email" type="email" required placeholder="rider@example.com" className="pl-10 bg-background border-border rounded-none h-12" data-testid="login-email" />
                  </div>
                </div>
                <div>
                  <Label className="text-xs uppercase tracking-widest font-bold text-muted-foreground">Password</Label>
                  <div className="relative mt-1">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" strokeWidth={1.5} />
                    <Input name="password" type="password" required placeholder="Enter password" className="pl-10 bg-background border-border rounded-none h-12" data-testid="login-password" />
                  </div>
                </div>
                <Button type="submit" disabled={loading} className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-bold uppercase tracking-wider rounded-sm h-12" data-testid="login-submit-btn">
                  {loading ? 'Signing in...' : 'Sign In'}
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="register">
              <form onSubmit={handleRegister} className="space-y-4">
                <div>
                  <Label className="text-xs uppercase tracking-widest font-bold text-muted-foreground">Full Name</Label>
                  <div className="relative mt-1">
                    <UserIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" strokeWidth={1.5} />
                    <Input name="name" required placeholder="John Rider" className="pl-10 bg-background border-border rounded-none h-12" data-testid="register-name" />
                  </div>
                </div>
                <div>
                  <Label className="text-xs uppercase tracking-widest font-bold text-muted-foreground">Email</Label>
                  <div className="relative mt-1">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" strokeWidth={1.5} />
                    <Input name="email" type="email" required placeholder="rider@example.com" className="pl-10 bg-background border-border rounded-none h-12" data-testid="register-email" />
                  </div>
                </div>
                <div>
                  <Label className="text-xs uppercase tracking-widest font-bold text-muted-foreground">Phone (Optional)</Label>
                  <div className="relative mt-1">
                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" strokeWidth={1.5} />
                    <Input name="phone" placeholder="+91-9876543210" className="pl-10 bg-background border-border rounded-none h-12" data-testid="register-phone" />
                  </div>
                </div>
                <div>
                  <Label className="text-xs uppercase tracking-widest font-bold text-muted-foreground">Password</Label>
                  <div className="relative mt-1">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" strokeWidth={1.5} />
                    <Input name="password" type="password" required minLength={6} placeholder="Min 6 characters" className="pl-10 bg-background border-border rounded-none h-12" data-testid="register-password" />
                  </div>
                </div>
                <div>
                  <Label className="text-xs uppercase tracking-widest font-bold text-muted-foreground">I want to</Label>
                  <Select name="role" defaultValue="customer">
                    <SelectTrigger className="bg-background border-border rounded-none h-12 mt-1" data-testid="register-role">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-950 border-zinc-800 rounded-sm">
                      <SelectItem value="customer">Rent Bikes (Customer)</SelectItem>
                      <SelectItem value="shop_owner">List My Bikes (Shop Owner)</SelectItem>
                      <SelectItem value="travel_agent">Refer Customers (Travel Agent)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button type="submit" disabled={loading} className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-bold uppercase tracking-wider rounded-sm h-12" data-testid="register-submit-btn">
                  {loading ? 'Creating Account...' : 'Create Account'}
                </Button>
              </form>
            </TabsContent>
          </Tabs>

          {/* Divider */}
          <div className="flex items-center gap-4 my-6">
            <div className="flex-1 border-t border-border" />
            <span className="text-xs text-muted-foreground uppercase tracking-widest">or</span>
            <div className="flex-1 border-t border-border" />
          </div>

          {/* Google OAuth */}
          <Button
            onClick={handleGoogleLogin}
            variant="outline"
            className="w-full border-white/20 text-white hover:bg-white/10 font-bold uppercase tracking-wider rounded-sm h-12"
            data-testid="google-login-btn"
          >
            <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </Button>
        </div>
      </div>
    </div>
  );
}
