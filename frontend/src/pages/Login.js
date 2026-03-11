import { useState } from 'react';
import { useNavigate, Navigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
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

  if (user) {
    return <Navigate to={getRedirectPath(user.role)} replace />;
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
        role: 'customer',
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

  const handleGoogleLogin = () => {
    const redirectUrl = window.location.origin + '/dashboard';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div className="min-h-screen bg-background pt-16 flex items-center justify-center px-6" data-testid="login-page">
      <div className="w-full max-w-md">
        {/* Logo */}
        <Link to="/" className="flex items-center justify-center gap-2 mb-8">
          <Mountain className="w-7 h-7 text-primary" strokeWidth={2} />
          <span className="font-heading font-extrabold text-xl">Ladakh Moto</span>
        </Link>

        <div className="bg-card border border-border rounded-2xl shadow-lg p-8">
          <Tabs defaultValue="login" className="w-full">
            <TabsList className="grid grid-cols-2 mb-6 bg-secondary rounded-xl h-11">
              <TabsTrigger value="login" className="rounded-lg font-heading font-bold text-sm" data-testid="login-tab">
                Log in
              </TabsTrigger>
              <TabsTrigger value="register" className="rounded-lg font-heading font-bold text-sm" data-testid="register-tab">
                Sign up
              </TabsTrigger>
            </TabsList>

            <TabsContent value="login">
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <Label className="text-xs font-semibold text-muted-foreground">Email</Label>
                  <div className="relative mt-1">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input name="email" type="email" required placeholder="you@example.com"
                      className="pl-10 rounded-xl h-12 border-border" data-testid="login-email" />
                  </div>
                </div>
                <div>
                  <Label className="text-xs font-semibold text-muted-foreground">Password</Label>
                  <div className="relative mt-1">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input name="password" type="password" required placeholder="Your password"
                      className="pl-10 rounded-xl h-12 border-border" data-testid="login-password" />
                  </div>
                </div>
                <Button type="submit" disabled={loading}
                  className="w-full bg-primary text-white hover:bg-primary/90 font-bold rounded-xl h-12 text-sm"
                  data-testid="login-submit-btn">
                  {loading ? 'Signing in...' : 'Log in'}
                </Button>
              </form>

              <div className="flex items-center gap-4 my-5">
                <div className="flex-1 h-px bg-border" />
                <span className="text-xs text-muted-foreground">or</span>
                <div className="flex-1 h-px bg-border" />
              </div>

              <Button variant="outline" onClick={handleGoogleLogin}
                className="w-full border-border hover:bg-secondary rounded-xl h-12 font-semibold text-sm"
                data-testid="google-login-btn">
                <svg className="w-5 h-5 mr-2" viewBox="0 0 48 48"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>
                Continue with Google
              </Button>
            </TabsContent>

            <TabsContent value="register">
              <form onSubmit={handleRegister} className="space-y-4">
                <div>
                  <Label className="text-xs font-semibold text-muted-foreground">Full Name</Label>
                  <div className="relative mt-1">
                    <UserIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input name="name" required placeholder="Your name"
                      className="pl-10 rounded-xl h-12 border-border" data-testid="register-name" />
                  </div>
                </div>
                <div>
                  <Label className="text-xs font-semibold text-muted-foreground">Email</Label>
                  <div className="relative mt-1">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input name="email" type="email" required placeholder="you@example.com"
                      className="pl-10 rounded-xl h-12 border-border" data-testid="register-email" />
                  </div>
                </div>
                <div>
                  <Label className="text-xs font-semibold text-muted-foreground">Phone (optional)</Label>
                  <div className="relative mt-1">
                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input name="phone" placeholder="+91-9876543210"
                      className="pl-10 rounded-xl h-12 border-border" data-testid="register-phone" />
                  </div>
                </div>
                <div>
                  <Label className="text-xs font-semibold text-muted-foreground">Password</Label>
                  <div className="relative mt-1">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input name="password" type="password" required placeholder="Min 6 characters"
                      className="pl-10 rounded-xl h-12 border-border" data-testid="register-password" />
                  </div>
                </div>
                <Button type="submit" disabled={loading}
                  className="w-full bg-primary text-white hover:bg-primary/90 font-bold rounded-xl h-12 text-sm"
                  data-testid="register-submit-btn">
                  {loading ? 'Creating account...' : 'Create account'}
                </Button>
              </form>

              <p className="text-center text-xs text-muted-foreground mt-4">
                Shop owners & travel agents?{' '}
                <Link to="/apply?type=shop_owner" className="text-primary hover:underline font-medium">Apply here</Link>
              </p>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
