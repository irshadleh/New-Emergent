import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Link2, Users, IndianRupee, TrendingUp, Copy, Calendar,
  CheckCircle, Clock, ArrowUpRight, Wallet, BarChart3, UserCheck
} from 'lucide-react';
import { toast } from 'sonner';
import { format, parseISO } from 'date-fns';
import api, { getAgentDashboard, getCommissionLedger, generateReferralLink } from '../lib/api';

function StatCard({ label, value, icon: Icon, prefix = '' }) {
  return (
    <div className="bg-card border border-border/50 rounded-sm p-4">
      <Icon className="w-4 h-4 text-primary mb-2" strokeWidth={1.5} />
      <p className="font-heading font-bold text-xl text-foreground">{prefix}{typeof value === 'number' ? value.toLocaleString() : value}</p>
      <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">{label}</p>
    </div>
  );
}

function StatusBadge({ status }) {
  const styles = {
    confirmed: 'status-confirmed', active: 'status-active',
    completed: 'status-completed', cancelled: 'status-cancelled',
    overdue: 'status-overdue', pending: 'status-confirmed',
  };
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-sm text-[9px] uppercase tracking-widest font-bold ${styles[status] || 'status-confirmed'}`} data-testid={`agent-status-${status}`}>
      {status}
    </span>
  );
}

export default function TravelAgentDashboard() {
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [ledger, setLedger] = useState([]);
  const [ledgerPage, setLedgerPage] = useState(1);
  const [ledgerTotal, setLedgerTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [dashRes, ledgerRes] = await Promise.all([
        getAgentDashboard(),
        getCommissionLedger(1)
      ]);
      setDashboard(dashRes.data);
      setLedger(ledgerRes.data.entries || []);
      setLedgerTotal(ledgerRes.data.total || 0);
    } catch (err) {
      if (err.response?.status === 401) {
        toast.error('Please log in to access the travel agent dashboard');
      }
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const loadMoreLedger = async () => {
    const nextPage = ledgerPage + 1;
    try {
      const res = await getCommissionLedger(nextPage);
      setLedger(prev => [...prev, ...(res.data.entries || [])]);
      setLedgerPage(nextPage);
    } catch {}
  };

  const copyReferralCode = () => {
    if (dashboard?.referral_code) {
      navigator.clipboard.writeText(dashboard.referral_code);
      toast.success('Referral code copied!');
    }
  };

  const handleGenerateLink = async (bikeId) => {
    try {
      const res = await generateReferralLink(bikeId);
      const fullLink = window.location.origin + res.data.referral_link;
      navigator.clipboard.writeText(fullLink);
      toast.success('Referral link copied to clipboard!');
    } catch {
      toast.error('Failed to generate link');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background pt-20 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const stats = dashboard?.stats || {};
  const referrals = dashboard?.recent_referrals || [];

  // Derived data for customer management
  const uniqueCustomers = {};
  referrals.forEach(r => {
    const cid = r.customer_id;
    if (!uniqueCustomers[cid]) {
      uniqueCustomers[cid] = { name: r.customer_name || 'Unknown', bookings: 0, totalValue: 0, commission: 0, lastBooking: r.created_at };
    }
    uniqueCustomers[cid].bookings += 1;
    uniqueCustomers[cid].totalValue += r.total_amount || 0;
    uniqueCustomers[cid].commission += r.commission || 0;
    if (r.created_at > uniqueCustomers[cid].lastBooking) uniqueCustomers[cid].lastBooking = r.created_at;
  });
  const customerList = Object.entries(uniqueCustomers).map(([id, data]) => ({ customer_id: id, ...data }));

  // Earnings breakdown
  const pendingCommission = referrals.filter(r => r.status !== 'completed' && r.status !== 'cancelled').reduce((sum, r) => sum + (r.commission || 0), 0);
  const earnedCommission = stats.total_commission || 0;

  return (
    <div className="min-h-screen bg-background pt-20" data-testid="agent-dashboard">
      <div className="max-w-6xl mx-auto px-6 md:px-12 py-8">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <p className="uppercase tracking-widest text-xs font-bold text-accent mb-1">Travel Agent Portal</p>
            <h1 className="font-heading font-bold text-2xl sm:text-3xl uppercase tracking-tight text-foreground" data-testid="agent-dashboard-title">
              Welcome, {user?.name?.split(' ')[0]}
            </h1>
          </div>
          <Button onClick={() => handleGenerateLink()} className="bg-primary text-primary-foreground font-bold uppercase tracking-wider text-xs rounded-sm" data-testid="generate-link-btn">
            <Link2 className="w-4 h-4 mr-1" /> Generate Link
          </Button>
        </div>

        {/* Referral Code Banner */}
        <div className="bg-card border border-primary/30 rounded-sm p-5 mb-8" data-testid="referral-code-banner">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold mb-1">Your Referral Code</p>
              <div className="flex items-center gap-3">
                <p className="font-mono text-2xl font-bold text-primary" data-testid="referral-code">{dashboard?.referral_code || '...'}</p>
                <Button variant="ghost" size="sm" onClick={copyReferralCode} className="text-primary hover:text-primary/80" data-testid="copy-code-btn">
                  <Copy className="w-4 h-4" />
                </Button>
              </div>
            </div>
            <div className="text-right hidden sm:block">
              <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Commission Rate</p>
              <p className="text-lg font-bold text-accent">{stats.commission_rate || '5%'}</p>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard label="Total Referrals" value={stats.total_referrals || 0} icon={Users} />
          <StatCard label="Completed" value={stats.completed_referrals || 0} icon={CheckCircle} />
          <StatCard label="Booking Value" value={stats.total_booking_value || 0} icon={IndianRupee} prefix="" />
          <StatCard label="Commission Earned" value={earnedCommission} icon={Wallet} prefix="" />
        </div>

        {/* Tabs */}
        <Tabs defaultValue="bookings" className="w-full">
          <TabsList className="bg-secondary rounded-sm mb-6 flex-wrap h-auto p-1 gap-1">
            <TabsTrigger value="bookings" className="rounded-sm font-heading uppercase tracking-wider text-xs" data-testid="tab-bookings">
              Booking Tracking
            </TabsTrigger>
            <TabsTrigger value="customers" className="rounded-sm font-heading uppercase tracking-wider text-xs" data-testid="tab-customers">
              Customers ({customerList.length})
            </TabsTrigger>
            <TabsTrigger value="earnings" className="rounded-sm font-heading uppercase tracking-wider text-xs" data-testid="tab-earnings">
              Earnings
            </TabsTrigger>
            <TabsTrigger value="commission" className="rounded-sm font-heading uppercase tracking-wider text-xs" data-testid="tab-commission">
              Commission Ledger
            </TabsTrigger>
          </TabsList>

          {/* Booking Tracking Tab */}
          <TabsContent value="bookings">
            {referrals.length === 0 ? (
              <div className="text-center py-16" data-testid="no-referrals">
                <Link2 className="w-12 h-12 text-muted-foreground mx-auto mb-4" strokeWidth={1} />
                <p className="text-muted-foreground">No referral bookings yet. Share your referral link to start earning!</p>
                <Button onClick={() => handleGenerateLink()} variant="link" className="text-primary mt-2">
                  Generate a referral link
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {referrals.map(r => (
                  <div key={r.booking_id} className="bg-card border border-border/50 rounded-sm p-4" data-testid={`referral-booking-${r.booking_id}`}>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-heading font-bold text-sm uppercase tracking-tight">{r.bike_name || 'Bike'}</h3>
                          <StatusBadge status={r.status} />
                        </div>
                        <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1"><Users className="w-3 h-3" /> {r.customer_name || 'Customer'}</span>
                          {r.shop_name && <span className="flex items-center gap-1">@ {r.shop_name}</span>}
                          {r.start_date && (
                            <span className="flex items-center gap-1">
                              <Calendar className="w-3 h-3" />
                              {r.start_date?.slice(0, 10)} {r.end_date ? `- ${r.end_date?.slice(0, 10)}` : ''}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <p className="text-xs text-muted-foreground">Booking Value</p>
                        <p className="text-sm font-bold text-foreground">{(r.total_amount || 0).toLocaleString()} INR</p>
                        <p className="text-xs text-primary font-bold mt-0.5">Commission: {(r.commission || 0).toLocaleString()} INR</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Customer Management Tab */}
          <TabsContent value="customers">
            {customerList.length === 0 ? (
              <div className="text-center py-16">
                <UserCheck className="w-12 h-12 text-muted-foreground mx-auto mb-4" strokeWidth={1} />
                <p className="text-muted-foreground">No referred customers yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="bg-card/50 border border-border/30 rounded-sm p-3 mb-2">
                  <p className="text-xs text-muted-foreground"><span className="font-bold text-foreground">{customerList.length}</span> referred customers with <span className="font-bold text-foreground">{referrals.length}</span> total bookings</p>
                </div>
                {customerList.map(c => (
                  <div key={c.customer_id} className="bg-card border border-border/50 rounded-sm p-4" data-testid={`customer-${c.customer_id}`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                            <Users className="w-4 h-4 text-primary" strokeWidth={1.5} />
                          </div>
                          <div>
                            <h3 className="font-heading font-bold text-sm uppercase tracking-tight">{c.name}</h3>
                            <p className="text-xs text-muted-foreground">{c.bookings} booking{c.bookings !== 1 ? 's' : ''}</p>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-bold text-foreground">{c.totalValue.toLocaleString()} INR</p>
                        <p className="text-xs text-primary font-bold">{c.commission.toLocaleString()} INR earned</p>
                        {c.lastBooking && <p className="text-[10px] text-muted-foreground mt-0.5">Last: {c.lastBooking.slice(0, 10)}</p>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Earnings Analytics Tab */}
          <TabsContent value="earnings">
            <div className="space-y-6">
              {/* Earnings Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-card border border-border/50 rounded-sm p-5" data-testid="total-earnings-card">
                  <Wallet className="w-5 h-5 text-primary mb-3" strokeWidth={1.5} />
                  <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Total Earned</p>
                  <p className="font-heading font-bold text-2xl text-foreground mt-1">{earnedCommission.toLocaleString()} INR</p>
                  <p className="text-xs text-muted-foreground mt-1">From {stats.total_referrals || 0} referrals</p>
                </div>
                <div className="bg-card border border-border/50 rounded-sm p-5" data-testid="pending-earnings-card">
                  <Clock className="w-5 h-5 text-accent mb-3" strokeWidth={1.5} />
                  <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Pending Commission</p>
                  <p className="font-heading font-bold text-2xl text-accent mt-1">{pendingCommission.toLocaleString()} INR</p>
                  <p className="text-xs text-muted-foreground mt-1">From active/confirmed bookings</p>
                </div>
                <div className="bg-card border border-border/50 rounded-sm p-5" data-testid="avg-earnings-card">
                  <BarChart3 className="w-5 h-5 text-chart-3 mb-3" strokeWidth={1.5} />
                  <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Avg. Commission / Booking</p>
                  <p className="font-heading font-bold text-2xl text-foreground mt-1">
                    {stats.total_referrals > 0 ? Math.round(earnedCommission / stats.total_referrals).toLocaleString() : 0} INR
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">Rate: {stats.commission_rate || '5%'}</p>
                </div>
              </div>

              {/* Booking Performance Breakdown */}
              <div className="bg-card border border-border/50 rounded-sm p-5" data-testid="performance-breakdown">
                <h3 className="font-heading font-bold text-sm uppercase tracking-wider mb-4">Booking Performance</h3>
                <div className="space-y-3">
                  {[
                    { label: 'Completed Bookings', value: stats.completed_referrals || 0, total: stats.total_referrals || 0, color: 'bg-green-500' },
                    { label: 'Active Bookings', value: referrals.filter(r => ['active', 'confirmed'].includes(r.status)).length, total: stats.total_referrals || 0, color: 'bg-accent' },
                    { label: 'Cancelled', value: referrals.filter(r => r.status === 'cancelled').length, total: stats.total_referrals || 0, color: 'bg-destructive' },
                  ].map(({ label, value, total, color }) => (
                    <div key={label}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-muted-foreground">{label}</span>
                        <span className="font-bold text-foreground">{value} / {total}</span>
                      </div>
                      <div className="w-full h-1.5 bg-secondary rounded-full overflow-hidden">
                        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: total > 0 ? `${(value / total) * 100}%` : '0%' }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Commission Rate Info */}
              <div className="bg-card/50 border border-primary/20 rounded-sm p-4">
                <div className="flex items-center gap-2 mb-2">
                  <ArrowUpRight className="w-4 h-4 text-primary" strokeWidth={1.5} />
                  <p className="text-sm font-bold text-foreground">How Commission Works</p>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  You earn <span className="text-primary font-bold">{stats.commission_rate || '5%'}</span> on every paid booking made through your referral link.
                  Commission is calculated on the total booking value and tracked in your commission ledger.
                  Share your referral code or generate bike-specific links for higher conversion.
                </p>
              </div>
            </div>
          </TabsContent>

          {/* Commission Ledger Tab */}
          <TabsContent value="commission">
            {ledger.length === 0 ? (
              <div className="text-center py-16" data-testid="no-commission">
                <IndianRupee className="w-12 h-12 text-muted-foreground mx-auto mb-4" strokeWidth={1} />
                <p className="text-muted-foreground">No commission entries yet. Start referring to earn!</p>
              </div>
            ) : (
              <div>
                {/* Ledger Header */}
                <div className="hidden sm:grid grid-cols-5 gap-4 px-4 py-2 text-[10px] uppercase tracking-widest text-muted-foreground font-bold border-b border-border/30 mb-2">
                  <span>Bike</span>
                  <span>Shop</span>
                  <span>Date</span>
                  <span>Booking Value</span>
                  <span className="text-right">Commission</span>
                </div>
                <div className="space-y-1">
                  {ledger.map(e => (
                    <div key={e.booking_id} className="bg-card border border-border/50 rounded-sm p-3 grid grid-cols-1 sm:grid-cols-5 gap-2 sm:gap-4 items-center text-sm" data-testid={`ledger-entry-${e.booking_id}`}>
                      <span className="font-heading font-bold text-xs uppercase">{e.bike_name || '-'}</span>
                      <span className="text-xs text-muted-foreground">{e.shop_name || '-'}</span>
                      <span className="text-xs text-muted-foreground">{e.created_at?.slice(0, 10)}</span>
                      <span className="text-xs">{(e.total_amount || 0).toLocaleString()} INR</span>
                      <span className="text-sm font-bold text-primary sm:text-right">{(e.commission || 0).toLocaleString()} INR</span>
                    </div>
                  ))}
                </div>
                {ledger.length < ledgerTotal && (
                  <div className="text-center mt-4">
                    <Button variant="ghost" onClick={loadMoreLedger} className="text-primary text-xs uppercase tracking-wider" data-testid="load-more-ledger">
                      Load More ({ledgerTotal - ledger.length} remaining)
                    </Button>
                  </div>
                )}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
