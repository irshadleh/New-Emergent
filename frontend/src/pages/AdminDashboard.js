import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Separator } from '../components/ui/separator';
import {
  LayoutDashboard, Users, Wallet, Shield, Search, TrendingUp,
  IndianRupee, Bike, Store, Calendar, ArrowDownToLine, CheckCircle,
  XCircle, ChevronLeft, ChevronRight, Eye
} from 'lucide-react';
import { toast } from 'sonner';
import { format, parseISO } from 'date-fns';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line
} from 'recharts';
import {
  getAdminDashboard, getAdminUsers, updateAdminUser,
  getAdminPayouts, adminSettleShop, getAdminKyc, reviewKyc
} from '../lib/api';

const CHART_COLORS = ['#eab308', '#0ea5e9', '#22c55e', '#ef4444', '#a855f7'];

function StatCard({ icon: Icon, label, value, accent = false }) {
  return (
    <div className="bg-card border border-border/50 rounded-sm p-4">
      <Icon className={`w-4 h-4 mb-2 ${accent ? 'text-accent' : 'text-primary'}`} strokeWidth={1.5} />
      <p className="font-heading font-bold text-xl text-foreground">{value}</p>
      <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">{label}</p>
    </div>
  );
}

function Pagination({ page, total, limit, onPageChange }) {
  const totalPages = Math.ceil(total / limit);
  if (totalPages <= 1) return null;
  return (
    <div className="flex items-center justify-between mt-4 text-sm text-muted-foreground">
      <span>{total} total</span>
      <div className="flex items-center gap-2">
        <Button size="sm" variant="ghost" disabled={page <= 1} onClick={() => onPageChange(page - 1)} data-testid="pagination-prev">
          <ChevronLeft className="w-4 h-4" />
        </Button>
        <span className="text-xs">{page} / {totalPages}</span>
        <Button size="sm" variant="ghost" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)} data-testid="pagination-next">
          <ChevronRight className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}

function OverviewTab({ data }) {
  if (!data) return null;
  const overview = data.overview || {};
  const adminMetrics = data.admin_metrics || {};
  const monthly = (data.monthly_trends || []).map(m => ({ name: m.month, revenue: m.revenue, bookings: m.bookings }));
  const bookingStatuses = data.booking_statuses || {};
  const pieData = Object.entries(bookingStatuses).map(([name, value]) => ({ name, value }));
  const topShops = data.top_shops || [];
  const recentBookings = data.recent_bookings || [];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard icon={Users} label="Total Users" value={overview.total_users || 0} />
        <StatCard icon={Store} label="Shops" value={overview.total_shops || 0} />
        <StatCard icon={Bike} label="Bikes" value={overview.total_bikes || 0} />
        <StatCard icon={Calendar} label="Bookings" value={overview.total_bookings || 0} />
        <StatCard icon={IndianRupee} label="Revenue" value={`${(overview.total_revenue || 0).toLocaleString()}`} />
        <StatCard icon={TrendingUp} label="Commission" value={`${(overview.total_commission || 0).toLocaleString()}`} accent />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card border border-primary/20 rounded-sm p-4">
          <Shield className="w-4 h-4 text-primary mb-2" strokeWidth={1.5} />
          <p className="font-heading font-bold text-xl text-primary">{adminMetrics.pending_kyc || 0}</p>
          <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Pending KYC</p>
        </div>
        <div className="bg-card border border-accent/20 rounded-sm p-4">
          <Wallet className="w-4 h-4 text-accent mb-2" strokeWidth={1.5} />
          <p className="font-heading font-bold text-xl text-accent">{adminMetrics.pending_payouts || 0}</p>
          <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Pending Payouts</p>
        </div>
        <div className="bg-card border border-border/50 rounded-sm p-4">
          <ArrowDownToLine className="w-4 h-4 text-chart-3 mb-2" strokeWidth={1.5} />
          <p className="font-heading font-bold text-xl text-foreground">{adminMetrics.total_settlements || 0}</p>
          <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Settlements</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {monthly.length > 0 && (
          <div className="lg:col-span-2 bg-card border border-border/50 rounded-sm p-6" data-testid="admin-revenue-chart">
            <h3 className="font-heading font-bold text-sm uppercase tracking-wider mb-4">Revenue Trends</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={monthly}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="name" tick={{ fill: '#a1a1aa', fontSize: 11 }} />
                <YAxis tick={{ fill: '#a1a1aa', fontSize: 11 }} />
                <RechartsTooltip contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: '2px' }} />
                <Line type="monotone" dataKey="revenue" stroke="#eab308" strokeWidth={2} dot={{ fill: '#eab308' }} />
                <Line type="monotone" dataKey="bookings" stroke="#0ea5e9" strokeWidth={2} dot={{ fill: '#0ea5e9' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {pieData.length > 0 && (
          <div className="bg-card border border-border/50 rounded-sm p-6" data-testid="admin-status-chart">
            <h3 className="font-heading font-bold text-sm uppercase tracking-wider mb-4">Booking Status</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, value }) => `${name}: ${value}`}>
                  {pieData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                </Pie>
                <RechartsTooltip contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: '2px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {topShops.length > 0 && (
        <div className="bg-card border border-border/50 rounded-sm p-6" data-testid="admin-top-shops">
          <h3 className="font-heading font-bold text-sm uppercase tracking-wider mb-4">Top Shops by Revenue</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={topShops}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis dataKey="name" tick={{ fill: '#a1a1aa', fontSize: 10 }} />
              <YAxis tick={{ fill: '#a1a1aa', fontSize: 11 }} />
              <RechartsTooltip contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: '2px' }} />
              <Bar dataKey="revenue" fill="#eab308" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {recentBookings.length > 0 && (
        <div className="bg-card border border-border/50 rounded-sm p-5" data-testid="admin-recent-bookings">
          <h3 className="font-heading font-bold text-sm uppercase tracking-wider mb-4">Recent Bookings</h3>
          <div className="space-y-2">
            {recentBookings.map(b => (
              <div key={b.booking_id} className="flex items-center justify-between py-2 border-b border-border/30 last:border-0">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-bold truncate">{b.bike_name}</p>
                  <p className="text-xs text-muted-foreground">{b.customer_name} | {b.created_at?.slice(0, 10)}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`inline-flex px-2 py-0.5 rounded-sm text-[9px] uppercase tracking-widest font-bold status-${b.status}`}>{b.status}</span>
                  <span className="text-sm font-bold text-primary">{(b.total_amount || 0).toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function UsersTab() {
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [editUser, setEditUser] = useState(null);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, limit: 20 };
      if (roleFilter !== 'all') params.role = roleFilter;
      if (search) params.search = search;
      const res = await getAdminUsers(params);
      setUsers(res.data.users || []);
      setTotal(res.data.total || 0);
    } catch {}
    setLoading(false);
  }, [page, roleFilter, search]);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  const handleUpdate = async (userId, data) => {
    try {
      await updateAdminUser(userId, data);
      toast.success('User updated');
      setEditUser(null);
      fetchUsers();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Update failed');
    }
  };

  const roleBadge = (role) => {
    const colors = { admin: 'bg-primary/20 text-primary', shop_owner: 'bg-accent/20 text-accent', travel_agent: 'bg-chart-3/20 text-chart-3', customer: 'bg-secondary text-muted-foreground' };
    return <span className={`inline-flex px-2 py-0.5 rounded-sm text-[9px] uppercase tracking-widest font-bold ${colors[role] || colors.customer}`}>{role}</span>;
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col md:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" strokeWidth={1.5} />
          <Input value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} placeholder="Search users..."
            className="pl-10 bg-background border-border rounded-none h-11" data-testid="admin-user-search" />
        </div>
        <Select value={roleFilter} onValueChange={v => { setRoleFilter(v); setPage(1); }}>
          <SelectTrigger className="w-full md:w-44 bg-background border-border rounded-none h-11" data-testid="admin-role-filter">
            <SelectValue placeholder="All Roles" />
          </SelectTrigger>
          <SelectContent className="bg-zinc-950 border-zinc-800 rounded-sm">
            <SelectItem value="all">All Roles</SelectItem>
            <SelectItem value="customer">Customer</SelectItem>
            <SelectItem value="shop_owner">Shop Owner</SelectItem>
            <SelectItem value="travel_agent">Travel Agent</SelectItem>
            <SelectItem value="admin">Admin</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="bg-card border border-border/50 rounded-sm p-4 animate-pulse">
              <div className="h-4 bg-secondary rounded w-1/3 mb-2" />
              <div className="h-3 bg-secondary rounded w-1/4" />
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-card border border-border/50 rounded-sm overflow-hidden" data-testid="admin-users-table">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/50 bg-secondary/30">
                  <th className="px-4 py-3 text-left text-[10px] uppercase tracking-widest font-bold text-muted-foreground">User</th>
                  <th className="px-4 py-3 text-left text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Role</th>
                  <th className="px-4 py-3 text-left text-[10px] uppercase tracking-widest font-bold text-muted-foreground">KYC</th>
                  <th className="px-4 py-3 text-left text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Joined</th>
                  <th className="px-4 py-3 text-right text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.user_id} className="border-b border-border/30 hover:bg-secondary/10 transition-colors" data-testid={`user-row-${u.user_id}`}>
                    <td className="px-4 py-3">
                      <p className="font-bold text-foreground">{u.name || 'N/A'}</p>
                      <p className="text-xs text-muted-foreground">{u.email}</p>
                    </td>
                    <td className="px-4 py-3">{roleBadge(u.role)}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex px-2 py-0.5 rounded-sm text-[9px] uppercase tracking-widest font-bold ${u.kyc_status === 'approved' ? 'status-completed' : u.kyc_status === 'rejected' ? 'status-cancelled' : 'status-confirmed'}`}>
                        {u.kyc_status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{u.created_at?.slice(0, 10)}</td>
                    <td className="px-4 py-3 text-right">
                      <Button size="sm" variant="ghost" className="text-xs h-7 px-2" onClick={() => setEditUser(u)} data-testid={`edit-user-${u.user_id}`}>
                        <Eye className="w-3.5 h-3.5 mr-1" /> Manage
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} total={total} limit={20} onPageChange={setPage} />
        </div>
      )}

      <Dialog open={!!editUser} onOpenChange={(open) => !open && setEditUser(null)}>
        <DialogContent className="bg-zinc-950 border-zinc-800 rounded-sm max-w-md">
          <DialogHeader>
            <DialogTitle className="font-heading font-bold uppercase tracking-tight">Manage User</DialogTitle>
          </DialogHeader>
          {editUser && (
            <div className="space-y-4 mt-2">
              <div>
                <p className="font-bold">{editUser.name}</p>
                <p className="text-xs text-muted-foreground">{editUser.email}</p>
                <p className="text-xs text-muted-foreground">ID: {editUser.user_id}</p>
              </div>
              <Separator className="bg-border/50" />
              <div>
                <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground block mb-1">Role</label>
                <Select defaultValue={editUser.role} onValueChange={v => handleUpdate(editUser.user_id, { role: v })}>
                  <SelectTrigger className="bg-background border-border rounded-none h-10" data-testid="edit-user-role">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-950 border-zinc-800 rounded-sm">
                    <SelectItem value="customer">Customer</SelectItem>
                    <SelectItem value="shop_owner">Shop Owner</SelectItem>
                    <SelectItem value="travel_agent">Travel Agent</SelectItem>
                    <SelectItem value="admin">Admin</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground block mb-1">KYC Status</label>
                <Select defaultValue={editUser.kyc_status || 'pending'} onValueChange={v => handleUpdate(editUser.user_id, { kyc_status: v })}>
                  <SelectTrigger className="bg-background border-border rounded-none h-10" data-testid="edit-user-kyc">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-950 border-zinc-800 rounded-sm">
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="approved">Approved</SelectItem>
                    <SelectItem value="rejected">Rejected</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex gap-2">
                <Button variant="ghost" className="flex-1 text-xs" onClick={() => setEditUser(null)}>Close</Button>
                <Button
                  className={`flex-1 text-xs ${editUser.is_suspended ? 'bg-chart-3 text-white' : 'bg-destructive text-white'}`}
                  onClick={() => handleUpdate(editUser.user_id, { is_suspended: !editUser.is_suspended })}
                  data-testid="toggle-suspend-btn"
                >
                  {editUser.is_suspended ? 'Unsuspend' : 'Suspend User'}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function PayoutsTab() {
  const [entries, setEntries] = useState([]);
  const [total, setTotal] = useState(0);
  const [summary, setSummary] = useState({});
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  const fetchPayouts = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, limit: 20 };
      if (statusFilter !== 'all') params.status = statusFilter;
      const res = await getAdminPayouts(params);
      setEntries(res.data.entries || []);
      setTotal(res.data.total || 0);
      setSummary(res.data.summary || {});
    } catch {}
    setLoading(false);
  }, [page, statusFilter]);

  useEffect(() => { fetchPayouts(); }, [fetchPayouts]);

  const handleSettle = async (shopId, shopName) => {
    try {
      const res = await adminSettleShop(shopId);
      toast.success(`Settled ${res.data.payouts_processed} payouts for ${shopName}: ${res.data.total_amount?.toLocaleString()} INR`);
      fetchPayouts();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Settlement failed');
    }
  };

  const pendingSummary = summary.pending || {};
  const processedSummary = summary.processed || {};

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon={Wallet} label="Pending Amount" value={`${(pendingSummary.amount || 0).toLocaleString()}`} />
        <StatCard icon={IndianRupee} label="Processed" value={`${(processedSummary.amount || 0).toLocaleString()}`} accent />
        <StatCard icon={TrendingUp} label="Total Commission" value={`${((pendingSummary.commission || 0) + (processedSummary.commission || 0)).toLocaleString()}`} />
        <StatCard icon={Calendar} label="Pending Count" value={pendingSummary.count || 0} />
      </div>

      <div className="flex items-center gap-3">
        <Select value={statusFilter} onValueChange={v => { setStatusFilter(v); setPage(1); }}>
          <SelectTrigger className="w-44 bg-background border-border rounded-none h-11" data-testid="admin-payout-filter">
            <SelectValue placeholder="All" />
          </SelectTrigger>
          <SelectContent className="bg-zinc-950 border-zinc-800 rounded-sm">
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="processed">Processed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="bg-card border border-border/50 rounded-sm p-5" data-testid="admin-payouts-table">
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-12 bg-secondary rounded animate-pulse" />)}
          </div>
        ) : entries.length === 0 ? (
          <p className="text-center text-muted-foreground py-8">No payout entries found</p>
        ) : (
          <div className="space-y-2">
            {entries.map(entry => (
              <div key={entry.payout_id} className="flex flex-col sm:flex-row sm:items-center justify-between py-3 border-b border-border/30 last:border-0 gap-2" data-testid={`admin-payout-${entry.payout_id}`}>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-bold">{entry.shop_name} - {entry.bike_name || 'Booking'}</p>
                  <p className="text-xs text-muted-foreground">{entry.customer_name} | {entry.created_at?.slice(0, 10)}</p>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <span className={`inline-flex px-2 py-0.5 rounded-sm text-[9px] uppercase tracking-widest font-bold ${entry.status === 'processed' ? 'status-completed' : 'status-confirmed'}`}>
                    {entry.status}
                  </span>
                  <span className="text-xs text-muted-foreground">-{(entry.commission_amount || 0).toLocaleString()} fee</span>
                  <span className="text-sm font-bold text-primary">{(entry.amount || 0).toLocaleString()} INR</span>
                  {entry.status === 'pending' && (
                    <Button size="sm" className="bg-accent text-white text-xs h-7 px-2 rounded-sm"
                      onClick={() => handleSettle(entry.shop_id, entry.shop_name)}
                      data-testid={`settle-${entry.payout_id}`}>
                      <ArrowDownToLine className="w-3 h-3 mr-1" /> Settle
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
        <Pagination page={page} total={total} limit={20} onPageChange={setPage} />
      </div>
    </div>
  );
}

function KycTab() {
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [loading, setLoading] = useState(true);
  const [reviewDialog, setReviewDialog] = useState(null);
  const [notes, setNotes] = useState('');

  const fetchKyc = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, limit: 20 };
      if (statusFilter !== 'all') params.status = statusFilter;
      const res = await getAdminKyc(params);
      setUsers(res.data.users || []);
      setTotal(res.data.total || 0);
    } catch {}
    setLoading(false);
  }, [page, statusFilter]);

  useEffect(() => { fetchKyc(); }, [fetchKyc]);

  const handleReview = async (userId, status) => {
    try {
      await reviewKyc(userId, status, notes);
      toast.success(`KYC ${status}`);
      setReviewDialog(null);
      setNotes('');
      fetchKyc();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Review failed');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Select value={statusFilter} onValueChange={v => { setStatusFilter(v); setPage(1); }}>
          <SelectTrigger className="w-44 bg-background border-border rounded-none h-11" data-testid="admin-kyc-filter">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent className="bg-zinc-950 border-zinc-800 rounded-sm">
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
          </SelectContent>
        </Select>
        <span className="text-sm text-muted-foreground">{total} users</span>
      </div>

      <div className="bg-card border border-border/50 rounded-sm" data-testid="admin-kyc-table">
        {loading ? (
          <div className="p-5 space-y-3">
            {Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-12 bg-secondary rounded animate-pulse" />)}
          </div>
        ) : users.length === 0 ? (
          <p className="text-center text-muted-foreground py-8">No KYC submissions found</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/50 bg-secondary/30">
                  <th className="px-4 py-3 text-left text-[10px] uppercase tracking-widest font-bold text-muted-foreground">User</th>
                  <th className="px-4 py-3 text-left text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Role</th>
                  <th className="px-4 py-3 text-left text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Status</th>
                  <th className="px-4 py-3 text-left text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Joined</th>
                  <th className="px-4 py-3 text-right text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.user_id} className="border-b border-border/30 hover:bg-secondary/10" data-testid={`kyc-row-${u.user_id}`}>
                    <td className="px-4 py-3">
                      <p className="font-bold">{u.name || 'N/A'}</p>
                      <p className="text-xs text-muted-foreground">{u.email}</p>
                    </td>
                    <td className="px-4 py-3 text-xs">{u.role}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex px-2 py-0.5 rounded-sm text-[9px] uppercase tracking-widest font-bold ${u.kyc_status === 'approved' ? 'status-completed' : u.kyc_status === 'rejected' ? 'status-cancelled' : 'status-confirmed'}`}>
                        {u.kyc_status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{u.created_at?.slice(0, 10)}</td>
                    <td className="px-4 py-3 text-right">
                      {u.kyc_status === 'pending' ? (
                        <div className="flex items-center justify-end gap-1">
                          <Button size="sm" className="bg-chart-3 text-white text-xs h-7 px-2 rounded-sm"
                            onClick={() => handleReview(u.user_id, 'approved')}
                            data-testid={`kyc-approve-${u.user_id}`}>
                            <CheckCircle className="w-3 h-3 mr-1" /> Approve
                          </Button>
                          <Button size="sm" variant="ghost" className="text-destructive text-xs h-7 px-2"
                            onClick={() => setReviewDialog(u)}
                            data-testid={`kyc-reject-btn-${u.user_id}`}>
                            <XCircle className="w-3 h-3 mr-1" /> Reject
                          </Button>
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">{u.kyc_reviewed_at?.slice(0, 10) || '-'}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <Pagination page={page} total={total} limit={20} onPageChange={setPage} />
      </div>

      <Dialog open={!!reviewDialog} onOpenChange={(open) => !open && setReviewDialog(null)}>
        <DialogContent className="bg-zinc-950 border-zinc-800 rounded-sm max-w-md">
          <DialogHeader>
            <DialogTitle className="font-heading font-bold uppercase tracking-tight">Reject KYC</DialogTitle>
          </DialogHeader>
          {reviewDialog && (
            <div className="space-y-4 mt-2">
              <p className="text-sm"><strong>{reviewDialog.name}</strong> ({reviewDialog.email})</p>
              <div>
                <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground block mb-1">Rejection Reason</label>
                <Textarea value={notes} onChange={e => setNotes(e.target.value)} placeholder="Provide a reason..."
                  className="bg-background border-border rounded-none" rows={3} data-testid="kyc-reject-notes" />
              </div>
              <div className="flex gap-2">
                <Button variant="ghost" className="flex-1 text-xs" onClick={() => setReviewDialog(null)}>Cancel</Button>
                <Button className="flex-1 bg-destructive text-white text-xs" onClick={() => handleReview(reviewDialog.user_id, 'rejected')} data-testid="kyc-reject-confirm">
                  Reject KYC
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function AdminDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user && user.role !== 'admin') {
      navigate('/');
      return;
    }
    const fetchDashboard = async () => {
      try {
        const res = await getAdminDashboard();
        setDashboardData(res.data);
      } catch {
        toast.error('Failed to load admin dashboard');
      }
      setLoading(false);
    };
    fetchDashboard();
  }, [user, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background pt-20 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pt-20" data-testid="admin-dashboard">
      <div className="max-w-7xl mx-auto px-6 md:px-12 py-8">
        <div className="mb-8">
          <p className="uppercase tracking-widest text-xs font-bold text-destructive mb-1">Admin Panel</p>
          <h1 className="font-heading font-bold text-2xl sm:text-3xl uppercase tracking-tight text-foreground">
            Platform Management
          </h1>
        </div>

        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="bg-secondary rounded-sm mb-6">
            <TabsTrigger value="overview" className="rounded-sm font-heading uppercase tracking-wider text-xs" data-testid="admin-tab-overview">
              <LayoutDashboard className="w-3.5 h-3.5 mr-1.5" /> Overview
            </TabsTrigger>
            <TabsTrigger value="users" className="rounded-sm font-heading uppercase tracking-wider text-xs" data-testid="admin-tab-users">
              <Users className="w-3.5 h-3.5 mr-1.5" /> Users
            </TabsTrigger>
            <TabsTrigger value="payouts" className="rounded-sm font-heading uppercase tracking-wider text-xs" data-testid="admin-tab-payouts">
              <Wallet className="w-3.5 h-3.5 mr-1.5" /> Payouts
            </TabsTrigger>
            <TabsTrigger value="kyc" className="rounded-sm font-heading uppercase tracking-wider text-xs" data-testid="admin-tab-kyc">
              <Shield className="w-3.5 h-3.5 mr-1.5" /> KYC
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <OverviewTab data={dashboardData} />
          </TabsContent>
          <TabsContent value="users">
            <UsersTab />
          </TabsContent>
          <TabsContent value="payouts">
            <PayoutsTab />
          </TabsContent>
          <TabsContent value="kyc">
            <KycTab />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
