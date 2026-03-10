import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Separator } from '../components/ui/separator';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../components/ui/tooltip';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Bike, Calendar, Bell, Star, Clock, MapPin, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';
import { format, parseISO } from 'date-fns';
import api, { submitReview } from '../lib/api';

function StatusBadge({ status }) {
  const styles = {
    confirmed: 'status-confirmed',
    active: 'status-active',
    completed: 'status-completed',
    cancelled: 'status-cancelled',
    overdue: 'status-overdue',
  };
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-sm text-[10px] uppercase tracking-widest font-bold ${styles[status] || 'status-confirmed'}`} data-testid={`status-${status}`}>
      {status}
    </span>
  );
}

function BookingCard({ booking, onAction, onReview }) {
  const mainImage = booking.bike_images?.[0] || 'https://images.unsplash.com/photo-1558618666-fcd25c85f82e?q=80&w=400&auto=format&fit=crop';
  const canCancel = ['confirmed', 'pending'].includes(booking.status);
  const canReturn = ['active', 'confirmed'].includes(booking.status);
  const canReview = booking.status === 'completed' && !booking.has_review;

  return (
    <div className="bg-card border border-border/50 rounded-sm overflow-hidden" data-testid={`booking-${booking.booking_id}`}>
      <div className="flex flex-col sm:flex-row">
        <div className="w-full sm:w-40 h-32 sm:h-auto overflow-hidden bg-muted flex-shrink-0">
          <img src={mainImage} alt={booking.bike_name} className="w-full h-full object-cover" />
        </div>
        <div className="p-4 flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="font-heading font-bold text-base uppercase tracking-tight">{booking.bike_name}</h3>
              <p className="text-xs text-muted-foreground mt-0.5">{booking.shop_name}</p>
            </div>
            <StatusBadge status={booking.status} />
          </div>
          <div className="flex flex-wrap gap-4 mt-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" strokeWidth={1.5} />
              {format(parseISO(booking.start_date), 'MMM d')} - {format(parseISO(booking.end_date), 'MMM d, yyyy')}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" strokeWidth={1.5} />
              {booking.total_days} day{booking.total_days > 1 ? 's' : ''}
            </span>
          </div>
          <div className="flex items-center justify-between mt-3 pt-3 border-t border-border/30">
            <span className="text-sm font-bold text-primary">{booking.total_amount?.toLocaleString()} INR</span>
            <div className="flex gap-2">
              {canReview && (
                <Button size="sm" className="bg-primary text-primary-foreground text-xs h-7 px-3 rounded-sm" onClick={() => onReview(booking)} data-testid={`review-booking-${booking.booking_id}`}>
                  <Star className="w-3 h-3 mr-1" /> Rate Ride
                </Button>
              )}
              {canCancel && (
                <Button size="sm" variant="ghost" className="text-destructive text-xs h-7 px-2 rounded-sm" onClick={() => onAction(booking.booking_id, 'cancel')} data-testid={`cancel-booking-${booking.booking_id}`}>
                  <XCircle className="w-3 h-3 mr-1" /> Cancel
                </Button>
              )}
              {canReturn && (
                <Button size="sm" className="bg-accent text-accent-foreground text-xs h-7 px-3 rounded-sm" onClick={() => onAction(booking.booking_id, 'return')} data-testid={`return-booking-${booking.booking_id}`}>
                  <CheckCircle className="w-3 h-3 mr-1" /> Return Bike
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function CustomerDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [bookings, setBookings] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [reviewBooking, setReviewBooking] = useState(null);
  const [reviewRating, setReviewRating] = useState(0);
  const [reviewComment, setReviewComment] = useState('');
  const [reviewSubmitting, setReviewSubmitting] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [bookRes, notifRes] = await Promise.all([
        api.get('/bookings'),
        api.get('/notifications')
      ]);
      const bookingsList = bookRes.data.bookings || [];
      // Check which completed bookings already have reviews
      const reviewChecks = await Promise.all(
        bookingsList.filter(b => b.status === 'completed').map(b =>
          api.get(`/reviews/bike/${b.bike_id}`).then(r => {
            const myReview = (r.data.reviews || []).find(rev => rev.booking_id === b.booking_id);
            return { booking_id: b.booking_id, has_review: !!myReview };
          }).catch(() => ({ booking_id: b.booking_id, has_review: false }))
        )
      );
      const reviewMap = {};
      reviewChecks.forEach(r => { reviewMap[r.booking_id] = r.has_review; });
      bookingsList.forEach(b => { b.has_review = reviewMap[b.booking_id] || false; });

      setBookings(bookingsList);
      setNotifications(notifRes.data.notifications || []);
      setUnreadCount(notifRes.data.unread_count || 0);
    } catch {}
    setLoading(false);
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleAction = async (bookingId, action) => {
    try {
      if (action === 'cancel') {
        await api.put(`/bookings/${bookingId}/status`, { status: 'cancelled' });
        toast.success('Booking cancelled');
      } else if (action === 'return') {
        const res = await api.post(`/bookings/${bookingId}/return`);
        if (res.data.penalty > 0) {
          toast.warning(`Bike returned. Late penalty: ${res.data.penalty} INR`);
        } else {
          toast.success('Bike returned successfully!');
        }
      }
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Action failed');
    }
  };

  const markRead = async (notifId) => {
    await api.put(`/notifications/${notifId}/read`);
    fetchData();
  };

  const markAllRead = async () => {
    await api.put('/notifications/read-all');
    fetchData();
  };

  const handleReviewSubmit = async () => {
    if (!reviewBooking || reviewRating < 1) { toast.error('Please select a rating'); return; }
    setReviewSubmitting(true);
    try {
      await submitReview(reviewBooking.booking_id, reviewRating, reviewComment);
      toast.success('Review submitted! Thanks for your feedback.');
      setReviewBooking(null);
      setReviewRating(0);
      setReviewComment('');
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit review');
    }
    setReviewSubmitting(false);
  };

  const active = bookings.filter(b => ['confirmed', 'active', 'overdue'].includes(b.status));
  const past = bookings.filter(b => ['completed', 'cancelled'].includes(b.status));

  if (loading) {
    return (
      <div className="min-h-screen bg-background pt-20 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pt-20" data-testid="customer-dashboard">
      <div className="max-w-5xl mx-auto px-6 md:px-12 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <p className="uppercase tracking-widest text-xs font-bold text-accent mb-1">Dashboard</p>
            <h1 className="font-heading font-bold text-2xl sm:text-3xl uppercase tracking-tight text-foreground">
              Welcome, {user?.name?.split(' ')[0]}
            </h1>
          </div>
          <Button onClick={() => navigate('/marketplace')} className="bg-primary text-primary-foreground hover:bg-primary/90 font-bold uppercase tracking-wider text-xs px-6 rounded-sm" data-testid="browse-bikes-btn">
            <Bike className="w-4 h-4 mr-2" /> Browse Bikes
          </Button>
        </div>

        {/* Quick stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Active Rides', value: active.length, icon: Bike },
            { label: 'Total Bookings', value: bookings.length, icon: Calendar },
            { label: 'Notifications', value: unreadCount, icon: Bell },
            { label: 'Reviews Given', value: past.filter(b => b.status === 'completed').length, icon: Star },
          ].map(({ label, value, icon: Icon }) => (
            <div key={label} className="bg-card border border-border/50 rounded-sm p-4">
              <Icon className="w-4 h-4 text-primary mb-2" strokeWidth={1.5} />
              <p className="font-heading font-bold text-xl text-foreground">{value}</p>
              <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">{label}</p>
            </div>
          ))}
        </div>

        <Tabs defaultValue="active" className="w-full">
          <TabsList className="bg-secondary rounded-sm mb-6">
            <TabsTrigger value="active" className="rounded-sm font-heading uppercase tracking-wider text-xs" data-testid="tab-active">
              Active ({active.length})
            </TabsTrigger>
            <TabsTrigger value="history" className="rounded-sm font-heading uppercase tracking-wider text-xs" data-testid="tab-history">
              History ({past.length})
            </TabsTrigger>
            <TabsTrigger value="notifications" className="rounded-sm font-heading uppercase tracking-wider text-xs" data-testid="tab-notifications">
              Notifications {unreadCount > 0 && `(${unreadCount})`}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="active">
            {active.length === 0 ? (
              <div className="text-center py-16">
                <Bike className="w-12 h-12 text-muted-foreground mx-auto mb-4" strokeWidth={1} />
                <p className="text-muted-foreground font-body">No active rides</p>
                <Button onClick={() => navigate('/marketplace')} variant="link" className="text-primary mt-2">
                  Find your next ride
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {active.map(b => <BookingCard key={b.booking_id} booking={b} onAction={handleAction} onReview={setReviewBooking} />)}
              </div>
            )}
          </TabsContent>

          <TabsContent value="history">
            {past.length === 0 ? (
              <div className="text-center py-16">
                <Clock className="w-12 h-12 text-muted-foreground mx-auto mb-4" strokeWidth={1} />
                <p className="text-muted-foreground font-body">No past rides yet</p>
              </div>
            ) : (
              <div className="space-y-4">
                {past.map(b => <BookingCard key={b.booking_id} booking={b} onAction={handleAction} onReview={setReviewBooking} />)}
              </div>
            )}
          </TabsContent>

          <TabsContent value="notifications">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-muted-foreground">{unreadCount} unread</p>
              {unreadCount > 0 && (
                <Button size="sm" variant="ghost" className="text-xs text-primary" onClick={markAllRead} data-testid="mark-all-read-btn">
                  Mark all as read
                </Button>
              )}
            </div>
            {notifications.length === 0 ? (
              <div className="text-center py-16">
                <Bell className="w-12 h-12 text-muted-foreground mx-auto mb-4" strokeWidth={1} />
                <p className="text-muted-foreground font-body">No notifications</p>
              </div>
            ) : (
              <div className="space-y-2">
                {notifications.map(n => (
                  <div
                    key={n.notification_id}
                    className={`p-4 bg-card border rounded-sm cursor-pointer transition-colors ${n.is_read ? 'border-border/30 opacity-70' : 'border-primary/30'}`}
                    onClick={() => !n.is_read && markRead(n.notification_id)}
                    data-testid={`notification-${n.notification_id}`}
                  >
                    <div className="flex items-start gap-3">
                      {!n.is_read && <div className="w-2 h-2 rounded-full bg-primary mt-1.5 flex-shrink-0" />}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-bold">{n.title}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">{n.message}</p>
                        <p className="text-[10px] text-muted-foreground mt-1">
                          {format(parseISO(n.created_at), 'MMM d, h:mm a')}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Review Dialog */}
        <Dialog open={!!reviewBooking} onOpenChange={(open) => { if (!open) { setReviewBooking(null); setReviewRating(0); setReviewComment(''); } }}>
          <DialogContent className="bg-zinc-950 border-zinc-800 rounded-sm max-w-md">
            <DialogHeader>
              <DialogTitle className="font-heading font-bold uppercase tracking-tight">Rate Your Ride</DialogTitle>
            </DialogHeader>
            {reviewBooking && (
              <div className="space-y-4 mt-2">
                <div>
                  <p className="font-bold text-foreground">{reviewBooking.bike_name}</p>
                  <p className="text-xs text-muted-foreground">{reviewBooking.shop_name} | {format(parseISO(reviewBooking.start_date), 'MMM d')} - {format(parseISO(reviewBooking.end_date), 'MMM d')}</p>
                </div>
                <Separator className="bg-border/50" />
                <div>
                  <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground block mb-2">Rating</label>
                  <div className="flex gap-1" data-testid="review-stars">
                    {[1, 2, 3, 4, 5].map(star => (
                      <button key={star} onClick={() => setReviewRating(star)} className="p-1 transition-transform hover:scale-110" data-testid={`review-star-${star}`}>
                        <Star className={`w-7 h-7 ${star <= reviewRating ? 'fill-primary text-primary' : 'text-muted-foreground'}`} />
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground block mb-1">Comment (optional)</label>
                  <Textarea value={reviewComment} onChange={e => setReviewComment(e.target.value)}
                    placeholder="Share your experience..."
                    className="bg-background border-border rounded-none" rows={3} data-testid="review-comment" />
                </div>
                <div className="flex gap-2">
                  <Button variant="ghost" className="flex-1 text-xs" onClick={() => { setReviewBooking(null); setReviewRating(0); setReviewComment(''); }}>
                    Cancel
                  </Button>
                  <Button
                    className="flex-1 bg-primary text-primary-foreground font-bold uppercase tracking-wider text-xs rounded-sm"
                    disabled={reviewRating < 1 || reviewSubmitting}
                    onClick={handleReviewSubmit}
                    data-testid="submit-review-btn"
                  >
                    {reviewSubmitting ? 'Submitting...' : 'Submit Review'}
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
