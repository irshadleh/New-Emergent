import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Lock, Shield } from 'lucide-react';
import { toast } from 'sonner';
import { changePassword } from '../lib/api';

export default function PasswordChangeDialog({ open, onComplete }) {
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password.length < 6) { toast.error('Password must be at least 6 characters'); return; }
    if (password !== confirm) { toast.error('Passwords do not match'); return; }

    setLoading(true);
    try {
      await changePassword(password);
      toast.success('Password changed successfully!');
      onComplete();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to change password');
    }
    setLoading(false);
  };

  return (
    <Dialog open={open} onOpenChange={() => {}}>
      <DialogContent className="bg-zinc-950 border-zinc-800 rounded-sm max-w-md [&>button]:hidden" onPointerDownOutside={e => e.preventDefault()} onEscapeKeyDown={e => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle className="font-heading font-bold uppercase tracking-tight flex items-center gap-2">
            <Shield className="w-5 h-5 text-primary" strokeWidth={1.5} />
            Change Your Password
          </DialogTitle>
        </DialogHeader>
        <div className="mt-2">
          <p className="text-sm text-muted-foreground mb-4">
            For your security, please set a new password for your account.
          </p>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">New Password</Label>
              <div className="relative mt-1">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" strokeWidth={1.5} />
                <Input type="password" value={password} onChange={e => setPassword(e.target.value)}
                  required minLength={6} placeholder="Min 6 characters"
                  className="pl-10 bg-background border-border rounded-none h-11" data-testid="new-password-input" />
              </div>
            </div>
            <div>
              <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Confirm Password</Label>
              <div className="relative mt-1">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" strokeWidth={1.5} />
                <Input type="password" value={confirm} onChange={e => setConfirm(e.target.value)}
                  required minLength={6} placeholder="Re-enter password"
                  className="pl-10 bg-background border-border rounded-none h-11" data-testid="confirm-password-input" />
              </div>
            </div>
            <Button type="submit" disabled={loading}
              className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-bold uppercase tracking-wider rounded-sm h-11"
              data-testid="change-password-btn">
              {loading ? 'Changing...' : 'Set New Password'}
            </Button>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  );
}
