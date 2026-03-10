import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Switch } from '../components/ui/switch';
import { Separator } from '../components/ui/separator';
import {
  Store, Bike, Plus, Calendar, TrendingUp, Star, Trash2, Edit,
  IndianRupee, Users, CheckCircle, Clock, Package, Wallet, ArrowDownToLine
} from 'lucide-react';
import { toast } from 'sonner';
import { format, parseISO } from 'date-fns';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';
import api, { getPayoutSummary, getPayoutLedger, requestSettlement, getSettlements } from '../lib/api';

function CreateShopForm({ onCreated }) {
  const [loading, setLoading] = useState(false);
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const fd = new FormData(e.target);
    try {
      await api.post('/shops', {
        name: fd.get('name'), description: fd.get('description'),
        address: fd.get('address'), phone: fd.get('phone'),
      });
      toast.success('Shop created!');
      onCreated();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed');
    }
    setLoading(false);
  };

  return (
    <div className="max-w-lg mx-auto py-16" data-testid="create-shop-form">
      <div className="text-center mb-8">
        <Store className="w-12 h-12 text-primary mx-auto mb-4" strokeWidth={1.5} />
        <h2 className="font-heading font-bold text-2xl uppercase tracking-tight">Create Your Shop</h2>
        <p className="text-sm text-muted-foreground mt-2">Start listing bikes on Ladakh Moto Market</p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4 bg-card border border-border/50 rounded-sm p-6">
        <div>
          <Label className="text-xs uppercase tracking-widest font-bold text-muted-foreground">Shop Name</Label>
          <Input name="name" required placeholder="Himalayan Riders Leh" className="bg-background border-border rounded-none h-11 mt-1" data-testid="shop-name-input" />
        </div>
        <div>
          <Label className="text-xs uppercase tracking-widest font-bold text-muted-foreground">Description</Label>
          <Textarea name="description" placeholder="Tell riders about your shop..." className="bg-background border-border rounded-none mt-1" rows={3} data-testid="shop-desc-input" />
        </div>
        <div>
          <Label className="text-xs uppercase tracking-widest font-bold text-muted-foreground">Address</Label>
          <Input name="address" placeholder="Main Bazaar, Leh, Ladakh" className="bg-background border-border rounded-none h-11 mt-1" data-testid="shop-address-input" />
        </div>
        <div>
          <Label className="text-xs uppercase tracking-widest font-bold text-muted-foreground">Phone</Label>
          <Input name="phone" placeholder="+91-9876543210" className="bg-background border-border rounded-none h-11 mt-1" data-testid="shop-phone-input" />
        </div>
        <Button type="submit" disabled={loading} className="w-full bg-primary text-primary-foreground font-bold uppercase tracking-wider rounded-sm h-11" data-testid="create-shop-btn">
          {loading ? 'Creating...' : 'Create Shop'}
        </Button>
      </form>
    </div>
  );
}

function AddBikeDialog({ onAdded }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const fd = new FormData(e.target);
    try {
      await api.post('/bikes', {
        name: fd.get('name'), type: fd.get('type') || 'adventure',
        brand: fd.get('brand'), model: fd.get('model'),
        year: parseInt(fd.get('year') || '2024'),
        engine_cc: parseInt(fd.get('engine_cc') || '350'),
        daily_rate: parseFloat(fd.get('daily_rate') || '1000'),
        weekly_rate: parseFloat(fd.get('weekly_rate') || '0') || null,
        location: fd.get('location') || 'Leh',
        description: fd.get('description') || '',
        features: (fd.get('features') || '').split(',').map(f => f.trim()).filter(Boolean),
        images: (fd.get('images') || '').split(',').map(f => f.trim()).filter(Boolean),
      });
      toast.success('Bike added!');
      setOpen(false);
      onAdded();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed');
    }
    setLoading(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="bg-primary text-primary-foreground font-bold uppercase tracking-wider text-xs rounded-sm" data-testid="add-bike-trigger">
          <Plus className="w-4 h-4 mr-1" /> Add Bike
        </Button>
      </DialogTrigger>
      <DialogContent className="bg-zinc-950 border-zinc-800 rounded-sm max-w-lg max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="font-heading font-bold uppercase tracking-tight">Add New Bike</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-3 mt-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Bike Name</Label>
              <Input name="name" required placeholder="Royal Enfield Himalayan" className="bg-background border-border rounded-none h-10 mt-1 text-sm" data-testid="bike-name-input" />
            </div>
            <div>
              <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Type</Label>
              <Select name="type" defaultValue="adventure">
                <SelectTrigger className="bg-background border-border rounded-none h-10 mt-1" data-testid="bike-type-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-zinc-950 border-zinc-800 rounded-sm">
                  <SelectItem value="adventure">Adventure</SelectItem>
                  <SelectItem value="cruiser">Cruiser</SelectItem>
                  <SelectItem value="sport">Sport</SelectItem>
                  <SelectItem value="scooter">Scooter</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Brand</Label>
              <Input name="brand" required placeholder="Royal Enfield" className="bg-background border-border rounded-none h-10 mt-1 text-sm" data-testid="bike-brand-input" />
            </div>
            <div>
              <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Model</Label>
              <Input name="model" required placeholder="Himalayan 450" className="bg-background border-border rounded-none h-10 mt-1 text-sm" data-testid="bike-model-input" />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Year</Label>
              <Input name="year" type="number" defaultValue="2024" className="bg-background border-border rounded-none h-10 mt-1 text-sm" />
            </div>
            <div>
              <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Engine CC</Label>
              <Input name="engine_cc" type="number" required placeholder="350" className="bg-background border-border rounded-none h-10 mt-1 text-sm" data-testid="bike-cc-input" />
            </div>
            <div>
              <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Location</Label>
              <Input name="location" defaultValue="Leh" className="bg-background border-border rounded-none h-10 mt-1 text-sm" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Daily Rate (INR)</Label>
              <Input name="daily_rate" type="number" required placeholder="1500" className="bg-background border-border rounded-none h-10 mt-1 text-sm" data-testid="bike-rate-input" />
            </div>
            <div>
              <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Weekly Rate (INR)</Label>
              <Input name="weekly_rate" type="number" placeholder="9000" className="bg-background border-border rounded-none h-10 mt-1 text-sm" />
            </div>
          </div>
          <div>
            <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Description</Label>
            <Textarea name="description" placeholder="Describe the bike..." className="bg-background border-border rounded-none mt-1 text-sm" rows={2} />
          </div>
          <div>
            <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Features (comma separated)</Label>
            <Input name="features" placeholder="ABS, Helmet, GPS Mount" className="bg-background border-border rounded-none h-10 mt-1 text-sm" />
          </div>
          <div>
            <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Image URLs (comma separated)</Label>
            <Input name="images" placeholder="https://..." className="bg-background border-border rounded-none h-10 mt-1 text-sm" />
          </div>
          <Button type="submit" disabled={loading} className="w-full bg-primary text-primary-foreground font-bold uppercase tracking-wider rounded-sm h-10 mt-2" data-testid="add-bike-submit">
            {loading ? 'Adding...' : 'Add Bike'}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default function ShopDashboard() {
  const { user, refreshUser } = useAuth();
  const [shop, setShop] = useState(null);
  const [bikes, setBikes] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [payoutData, setPayoutData] = useState(null);
  const [payoutLedgerData, setPayoutLedgerData] = useState([]);
  const [settlements, setSettlements] = useState([]);
  const [settleLoading, setSettleLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [hasShop, setHasShop] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const shopRes = await api.get('/my-shop');
      if (shopRes.data.shop) {
        setShop(shopRes.data.shop);
        setBikes(shopRes.data.shop.bikes || []);
        setHasShop(true);
        const [bookRes, analyticsRes, payoutRes, payoutLedgerRes, settlementsRes] = await Promise.all([
          api.get('/bookings?role=owner'),
          api.get('/analytics/shop').catch(() => ({ data: null })),
          getPayoutSummary().catch(() => ({ data: null })),
          getPayoutLedger(null, 1).catch(() => ({ data: { entries: [] } })),
          getSettlements().catch(() => ({ data: { settlements: [] } }))
        ]);
        setBookings(bookRes.data.bookings || []);
        setAnalytics(analyticsRes.data);
        setPayoutData(payoutRes.data);
        setPayoutLedgerData(payoutLedgerRes.data.entries || []);
        setSettlements(settlementsRes.data.settlements || []);
      } else {
        setHasShop(false);
      }
    } catch {}
    setLoading(false);
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleShopCreated = async () => {
    await refreshUser();
    fetchData();
  };

  const handleDeleteBike = async (bikeId) => {
    try {
      await api.delete(`/bikes/${bikeId}`);
      toast.success('Bike deleted');
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed');
    }
  };

  const handleBookingAction = async (bookingId, action) => {
    try {
      if (action === 'activate') {
        await api.put(`/bookings/${bookingId}/status`, { status: 'active' });
        toast.success('Booking activated - bike is now with rider');
      } else if (action === 'complete') {
        await api.post(`/bookings/${bookingId}/return`);
        toast.success('Booking completed');
      }
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed');
    }
  };

  const handleSettlement = async () => {
    setSettleLoading(true);
    try {
      const res = await requestSettlement();
      toast.success(`Settlement processed: ${res.data.total_amount?.toLocaleString()} INR for ${res.data.payouts_processed} payouts`);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Settlement failed');
    }
    setSettleLoading(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background pt-20 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!hasShop) {
    return (
      <div className="min-h-screen bg-background pt-20 px-6">
        <CreateShopForm onCreated={handleShopCreated} />
      </div>
    );
  }

  const stats = analytics?.stats || {};
  const monthlyData = (analytics?.monthly_revenue || []).map(m => ({
    name: m.month, revenue: m.revenue, bookings: m.bookings
  }));
  const payoutTotals = payoutData?.totals || {};
  const pendingPayouts = payoutData?.by_status?.pending || {};

  return (
    <div className="min-h-screen bg-background pt-20" data-testid="shop-dashboard">
      <div className="max-w-6xl mx-auto px-6 md:px-12 py-8">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <p className="uppercase tracking-widest text-xs font-bold text-accent mb-1">Shop Dashboard</p>
            <h1 className="font-heading font-bold text-2xl sm:text-3xl uppercase tracking-tight text-foreground" data-testid="shop-name-heading">
              {shop?.name}
            </h1>
            <p className="text-xs text-muted-foreground mt-1">{shop?.address}</p>
          </div>
          <AddBikeDialog onAdded={fetchData} />
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Total Bikes', value: stats.total_bikes || bikes.length, icon: Bike },
            { label: 'Active Bookings', value: stats.active_bookings || 0, icon: Calendar },
            { label: 'Revenue', value: `${(stats.total_revenue || 0).toLocaleString()}`, icon: IndianRupee },
            { label: 'Rating', value: stats.average_rating || '0', icon: Star },
          ].map(({ label, value, icon: Icon }) => (
            <div key={label} className="bg-card border border-border/50 rounded-sm p-4">
              <Icon className="w-4 h-4 text-primary mb-2" strokeWidth={1.5} />
              <p className="font-heading font-bold text-xl text-foreground">{value}</p>
              <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">{label}</p>
            </div>
          ))}
        </div>

        <Tabs defaultValue="bikes" className="w-full">
          <TabsList className="bg-secondary rounded-sm mb-6">
            <TabsTrigger value="bikes" className="rounded-sm font-heading uppercase tracking-wider text-xs" data-testid="shop-tab-bikes">
              Bikes ({bikes.length})
            </TabsTrigger>
            <TabsTrigger value="bookings" className="rounded-sm font-heading uppercase tracking-wider text-xs" data-testid="shop-tab-bookings">
              Bookings ({bookings.length})
            </TabsTrigger>
            <TabsTrigger value="analytics" className="rounded-sm font-heading uppercase tracking-wider text-xs" data-testid="shop-tab-analytics">
              Analytics
            </TabsTrigger>
            <TabsTrigger value="payouts" className="rounded-sm font-heading uppercase tracking-wider text-xs" data-testid="shop-tab-payouts">
              Payouts
            </TabsTrigger>
          </TabsList>

          {/* Bikes Tab */}
          <TabsContent value="bikes">
            {bikes.length === 0 ? (
              <div className="text-center py-16">
                <Bike className="w-12 h-12 text-muted-foreground mx-auto mb-4" strokeWidth={1} />
                <p className="text-muted-foreground">No bikes listed yet. Add your first bike!</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {bikes.map(bike => (
                  <div key={bike.bike_id} className="bg-card border border-border/50 rounded-sm overflow-hidden group" data-testid={`shop-bike-${bike.bike_id}`}>
                    <div className="aspect-[4/3] overflow-hidden bg-muted">
                      <img src={bike.images?.[0] || 'https://images.unsplash.com/photo-1558618666-fcd25c85f82e?q=80&w=400&auto=format&fit=crop'} alt={bike.name} className="w-full h-full object-cover" />
                    </div>
                    <div className="p-4">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-heading font-bold text-sm uppercase tracking-tight">{bike.name}</h3>
                          <p className="text-xs text-muted-foreground">{bike.brand} &middot; {bike.engine_cc}cc</p>
                        </div>
                        <Badge variant={bike.is_available ? 'default' : 'destructive'} className="rounded-sm text-[9px]">
                          {bike.is_available ? 'Available' : 'Unavailable'}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between mt-3 pt-3 border-t border-border/30">
                        <span className="text-sm font-bold text-primary">{bike.daily_rate} INR/day</span>
                        <Button size="sm" variant="ghost" className="text-destructive h-7 px-2" onClick={() => handleDeleteBike(bike.bike_id)} data-testid={`delete-bike-${bike.bike_id}`}>
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Bookings Tab */}
          <TabsContent value="bookings">
            {bookings.length === 0 ? (
              <div className="text-center py-16">
                <Calendar className="w-12 h-12 text-muted-foreground mx-auto mb-4" strokeWidth={1} />
                <p className="text-muted-foreground">No bookings yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {bookings.map(b => (
                  <div key={b.booking_id} className="bg-card border border-border/50 rounded-sm p-4" data-testid={`shop-booking-${b.booking_id}`}>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-heading font-bold text-sm uppercase tracking-tight">{b.bike_name}</h3>
                          <span className={`inline-flex px-2 py-0.5 rounded-sm text-[9px] uppercase tracking-widest font-bold status-${b.status}`}>
                            {b.status}
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                          {b.customer_name && <span className="flex items-center gap-1"><Users className="w-3 h-3" /> {b.customer_name}</span>}
                          <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {format(parseISO(b.start_date), 'MMM d')} - {format(parseISO(b.end_date), 'MMM d')}</span>
                          <span className="font-bold text-primary">{b.total_amount?.toLocaleString()} INR</span>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {b.status === 'confirmed' && (
                          <Button size="sm" className="bg-accent text-accent-foreground text-xs h-7 px-3 rounded-sm" onClick={() => handleBookingAction(b.booking_id, 'activate')} data-testid={`activate-${b.booking_id}`}>
                            <CheckCircle className="w-3 h-3 mr-1" /> Activate
                          </Button>
                        )}
                        {b.status === 'active' && (
                          <Button size="sm" className="bg-green-600 text-white text-xs h-7 px-3 rounded-sm" onClick={() => handleBookingAction(b.booking_id, 'complete')} data-testid={`complete-${b.booking_id}`}>
                            <Package className="w-3 h-3 mr-1" /> Complete
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics">
            <div className="space-y-6">
              {/* Revenue Chart */}
              {monthlyData.length > 0 ? (
                <div className="bg-card border border-border/50 rounded-sm p-6" data-testid="revenue-chart">
                  <h3 className="font-heading font-bold text-sm uppercase tracking-wider mb-4">Monthly Revenue</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={monthlyData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis dataKey="name" tick={{ fill: '#a1a1aa', fontSize: 11 }} />
                      <YAxis tick={{ fill: '#a1a1aa', fontSize: 11 }} />
                      <RechartsTooltip
                        contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: '2px' }}
                        labelStyle={{ color: '#fafafa' }}
                      />
                      <Bar dataKey="revenue" fill="#eab308" radius={[2, 2, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="bg-card border border-border/50 rounded-sm p-6 text-center">
                  <TrendingUp className="w-12 h-12 text-muted-foreground mx-auto mb-4" strokeWidth={1} />
                  <p className="text-muted-foreground text-sm">Revenue chart will appear after your first completed booking</p>
                </div>
              )}

              {/* Top Performing Bike */}
              {analytics?.top_performing_bike && (
                <div className="bg-card border border-primary/20 rounded-sm p-5" data-testid="top-bike">
                  <h3 className="font-heading font-bold text-sm uppercase tracking-wider mb-3">Top Performing Bike</h3>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-heading font-bold text-base">{analytics.top_performing_bike.name}</p>
                      <p className="text-xs text-muted-foreground">{analytics.top_performing_bike.bookings} bookings</p>
                    </div>
                    <p className="font-heading font-bold text-xl text-primary">{analytics.top_performing_bike.revenue?.toLocaleString()} INR</p>
                  </div>
                </div>
              )}

              {/* Bike Utilization */}
              {analytics?.bike_utilization?.length > 0 && (
                <div className="bg-card border border-border/50 rounded-sm p-6" data-testid="utilization-table">
                  <h3 className="font-heading font-bold text-sm uppercase tracking-wider mb-4">Bike Utilization</h3>
                  <div className="space-y-2">
                    {analytics.bike_utilization.map(b => (
                      <div key={b.bike_id} className="flex items-center justify-between py-2 border-b border-border/30 last:border-0">
                        <span className="text-sm font-body">{b.name}</span>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span>{b.active_bookings} active</span>
                          <span>{b.completed_bookings} completed</span>
                          <span className="font-bold text-foreground">{b.total_bookings} total</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </TabsContent>

          {/* Payouts Tab */}
          <TabsContent value="payouts">
            <div className="space-y-6">
              {/* Payout Summary Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-card border border-border/50 rounded-sm p-4">
                  <IndianRupee className="w-4 h-4 text-primary mb-2" strokeWidth={1.5} />
                  <p className="font-heading font-bold text-xl text-foreground">{(payoutTotals.gross_revenue || 0).toLocaleString()}</p>
                  <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Gross Revenue</p>
                </div>
                <div className="bg-card border border-border/50 rounded-sm p-4">
                  <Wallet className="w-4 h-4 text-accent mb-2" strokeWidth={1.5} />
                  <p className="font-heading font-bold text-xl text-foreground">{(payoutTotals.net_payable || 0).toLocaleString()}</p>
                  <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Net Payable</p>
                </div>
                <div className="bg-card border border-border/50 rounded-sm p-4">
                  <TrendingUp className="w-4 h-4 text-destructive mb-2" strokeWidth={1.5} />
                  <p className="font-heading font-bold text-xl text-foreground">{(payoutTotals.commission_paid || 0).toLocaleString()}</p>
                  <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Platform Fee</p>
                </div>
                <div className="bg-card border border-border/50 rounded-sm p-4">
                  <Clock className="w-4 h-4 text-chart-3 mb-2" strokeWidth={1.5} />
                  <p className="font-heading font-bold text-xl text-foreground">{(pendingPayouts.net_amount || 0).toLocaleString()}</p>
                  <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Pending Payout</p>
                </div>
              </div>

              {/* Settlement Action */}
              {(pendingPayouts.count || 0) > 0 && (
                <div className="bg-card border border-primary/30 rounded-sm p-5 flex items-center justify-between" data-testid="settlement-action">
                  <div>
                    <p className="font-heading font-bold text-sm uppercase">Ready for Settlement</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {pendingPayouts.count} pending payout{pendingPayouts.count !== 1 ? 's' : ''} worth {(pendingPayouts.net_amount || 0).toLocaleString()} INR
                    </p>
                  </div>
                  <Button
                    onClick={handleSettlement}
                    disabled={settleLoading}
                    className="bg-primary text-primary-foreground font-bold uppercase tracking-wider text-xs rounded-sm"
                    data-testid="request-settlement-btn"
                  >
                    <ArrowDownToLine className="w-4 h-4 mr-1" />
                    {settleLoading ? 'Processing...' : 'Request Settlement'}
                  </Button>
                </div>
              )}

              {/* Payout Ledger */}
              <div className="bg-card border border-border/50 rounded-sm p-5" data-testid="payout-ledger">
                <h3 className="font-heading font-bold text-sm uppercase tracking-wider mb-4">Payout Ledger</h3>
                {payoutLedgerData.length === 0 ? (
                  <p className="text-center text-muted-foreground text-sm py-8">No payout entries yet. Complete bookings to see payouts here.</p>
                ) : (
                  <div className="space-y-2">
                    {payoutLedgerData.map(entry => (
                      <div key={entry.payout_id} className="flex flex-col sm:flex-row sm:items-center justify-between py-3 border-b border-border/30 last:border-0 gap-2" data-testid={`payout-entry-${entry.payout_id}`}>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-bold">{entry.bike_name || 'Booking'}</p>
                          <p className="text-xs text-muted-foreground">{entry.customer_name} {entry.booking_dates ? `| ${entry.booking_dates}` : ''}</p>
                        </div>
                        <div className="flex items-center gap-4 text-xs flex-shrink-0">
                          <span className={`inline-flex px-2 py-0.5 rounded-sm text-[9px] uppercase tracking-widest font-bold ${entry.status === 'processed' ? 'status-completed' : entry.status === 'pending' ? 'status-confirmed' : 'status-active'}`}>
                            {entry.status}
                          </span>
                          <span className="text-muted-foreground">-{(entry.commission_amount || 0).toLocaleString()} fee</span>
                          <span className="font-bold text-primary">{(entry.amount || 0).toLocaleString()} INR</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Past Settlements */}
              {settlements.length > 0 && (
                <div className="bg-card border border-border/50 rounded-sm p-5" data-testid="past-settlements">
                  <h3 className="font-heading font-bold text-sm uppercase tracking-wider mb-4">Past Settlements</h3>
                  <div className="space-y-2">
                    {settlements.map(s => (
                      <div key={s.settlement_id} className="flex items-center justify-between py-3 border-b border-border/30 last:border-0">
                        <div>
                          <p className="text-sm font-bold">{s.settlement_id}</p>
                          <p className="text-xs text-muted-foreground">{s.created_at?.slice(0, 10)} | {s.payout_ids?.length || 0} payouts</p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-primary">{(s.total_amount || 0).toLocaleString()} INR</p>
                          <p className="text-[10px] text-muted-foreground">Fee: {(s.total_commission || 0).toLocaleString()}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
