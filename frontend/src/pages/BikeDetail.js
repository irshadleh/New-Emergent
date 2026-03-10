import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Calendar } from '../components/ui/calendar';
import { Separator } from '../components/ui/separator';
import { Star, MapPin, Fuel, Shield, ChevronLeft, Clock, Zap, Calendar as CalIcon } from 'lucide-react';
import { toast } from 'sonner';
import { format, differenceInDays, isWithinInterval, parseISO, addDays } from 'date-fns';
import api from '../lib/api';

export default function BikeDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [bike, setBike] = useState(null);
  const [loading, setLoading] = useState(true);
  const [booking, setBooking] = useState(false);
  const [dateRange, setDateRange] = useState({ from: undefined, to: undefined });
  const [selectedImage, setSelectedImage] = useState(0);
  const [showConfirm, setShowConfirm] = useState(false);

  useEffect(() => {
    const fetchBike = async () => {
      try {
        const res = await api.get(`/bikes/${id}`);
        setBike(res.data);
      } catch {
        toast.error('Bike not found');
        navigate('/marketplace');
      }
      setLoading(false);
    };
    fetchBike();
  }, [id, navigate]);

  const isDateBooked = (date) => {
    if (!bike?.booked_dates) return false;
    return bike.booked_dates.some(slot => {
      try {
        const start = parseISO(slot.start_date);
        const end = parseISO(slot.end_date);
        return isWithinInterval(date, { start, end: addDays(end, -1) });
      } catch { return false; }
    });
  };

  const totalDays = dateRange.from && dateRange.to ? Math.max(1, differenceInDays(dateRange.to, dateRange.from)) : 0;

  const calculateTotal = () => {
    if (!totalDays || !bike) return 0;
    if (totalDays >= 7 && bike.weekly_rate) {
      const weeks = Math.floor(totalDays / 7);
      const remaining = totalDays % 7;
      return (weeks * bike.weekly_rate) + (remaining * bike.daily_rate);
    }
    return totalDays * bike.daily_rate;
  };

  const handleBooking = async () => {
    if (!user) { navigate('/login'); return; }
    if (!dateRange.from || !dateRange.to) { toast.error('Select dates'); return; }

    if (!showConfirm) {
      setShowConfirm(true);
      return;
    }

    setBooking(true);
    try {
      await api.post('/bookings', {
        bike_id: bike.bike_id,
        start_date: dateRange.from.toISOString(),
        end_date: dateRange.to.toISOString(),
      });
      toast.success('Booking confirmed! Check your dashboard.');
      navigate('/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Booking failed');
    }
    setBooking(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background pt-20 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!bike) return null;

  return (
    <div className="min-h-screen bg-background pt-20" data-testid="bike-detail-page">
      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24 py-8">
        {/* Back button */}
        <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-primary transition-colors mb-6" data-testid="back-btn">
          <ChevronLeft className="w-4 h-4" /> Back
        </button>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left: Images + Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Main image */}
            <div className="aspect-[16/9] overflow-hidden bg-card border border-border/50 rounded-sm">
              <img src={bike.images?.[selectedImage] || bike.images?.[0]} alt={bike.name} className="w-full h-full object-cover" />
            </div>
            {bike.images?.length > 1 && (
              <div className="flex gap-2">
                {bike.images.map((img, i) => (
                  <button key={i} onClick={() => setSelectedImage(i)}
                    className={`w-20 h-16 overflow-hidden border rounded-sm transition-colors ${i === selectedImage ? 'border-primary' : 'border-border/50 hover:border-white/30'}`}>
                    <img src={img} alt="" className="w-full h-full object-cover" />
                  </button>
                ))}
              </div>
            )}

            {/* Bike info */}
            <div>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <Badge variant="secondary" className="rounded-sm text-[10px] uppercase tracking-widest font-bold mb-2">{bike.type}</Badge>
                  <h1 className="font-heading font-bold text-2xl sm:text-3xl uppercase tracking-tight text-foreground" data-testid="bike-name">{bike.name}</h1>
                </div>
                {bike.rating > 0 && (
                  <div className="flex items-center gap-1 bg-card border border-border/50 px-3 py-1.5 rounded-sm">
                    <Star className="w-4 h-4 fill-primary text-primary" />
                    <span className="font-bold text-sm">{bike.rating}</span>
                    <span className="text-xs text-muted-foreground">({bike.total_reviews})</span>
                  </div>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-4 mt-3 text-sm text-muted-foreground">
                <span className="flex items-center gap-1"><MapPin className="w-4 h-4" strokeWidth={1.5} /> {bike.location}</span>
                <span className="flex items-center gap-1"><Fuel className="w-4 h-4" strokeWidth={1.5} /> {bike.engine_cc}cc</span>
                <span className="flex items-center gap-1"><Zap className="w-4 h-4" strokeWidth={1.5} /> {bike.brand} {bike.model}</span>
                <span className="flex items-center gap-1"><Clock className="w-4 h-4" strokeWidth={1.5} /> {bike.year}</span>
              </div>

              <p className="mt-4 text-muted-foreground font-body leading-relaxed">{bike.description}</p>

              {/* Features */}
              {bike.features?.length > 0 && (
                <div className="mt-6">
                  <h3 className="font-heading font-bold text-sm uppercase tracking-wider mb-3">Includes</h3>
                  <div className="flex flex-wrap gap-2">
                    {bike.features.map((f) => (
                      <Badge key={f} variant="outline" className="rounded-sm border-border text-xs">
                        <Shield className="w-3 h-3 mr-1" strokeWidth={1.5} /> {f}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Shop info */}
              {bike.shop_name && (
                <div className="mt-6 p-4 bg-card border border-border/50 rounded-sm">
                  <h3 className="font-heading font-bold text-sm uppercase tracking-wider mb-1">Listed by</h3>
                  <p className="text-foreground font-body">{bike.shop_name}</p>
                  {bike.shop_details?.address && <p className="text-xs text-muted-foreground mt-1">{bike.shop_details.address}</p>}
                </div>
              )}
            </div>

            {/* Reviews */}
            {bike.reviews?.length > 0 && (
              <div className="mt-8">
                <h3 className="font-heading font-bold text-lg uppercase tracking-tight mb-4">Rider Reviews</h3>
                <div className="space-y-4">
                  {bike.reviews.map((review) => (
                    <div key={review.review_id} className="p-4 bg-card border border-border/50 rounded-sm">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-8 h-8 bg-secondary rounded-full flex items-center justify-center text-xs font-bold">
                          {review.reviewer_name?.[0] || '?'}
                        </div>
                        <div>
                          <p className="text-sm font-bold">{review.reviewer_name}</p>
                          <div className="flex items-center gap-0.5">
                            {Array.from({ length: 5 }).map((_, i) => (
                              <Star key={i} className={`w-3 h-3 ${i < review.rating ? 'fill-primary text-primary' : 'text-muted-foreground'}`} />
                            ))}
                          </div>
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground">{review.comment}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right: Booking panel */}
          <div className="lg:col-span-1">
            <div className="sticky top-24 bg-card border border-border/50 rounded-sm p-6 space-y-6" data-testid="booking-panel">
              <div>
                <span className="text-3xl font-heading font-bold text-primary">{bike.daily_rate}</span>
                <span className="text-sm text-muted-foreground ml-1">INR / day</span>
                {bike.weekly_rate && (
                  <p className="text-xs text-muted-foreground mt-1">{bike.weekly_rate} INR / week</p>
                )}
              </div>

              <Separator className="bg-border/50" />

              <div>
                <h3 className="font-heading font-bold text-sm uppercase tracking-wider mb-3 flex items-center gap-2">
                  <CalIcon className="w-4 h-4 text-primary" strokeWidth={1.5} />
                  Select Dates
                </h3>
                <div className="flex justify-center" data-testid="booking-calendar">
                  <Calendar
                    mode="range"
                    selected={dateRange}
                    onSelect={(range) => setDateRange(range || { from: undefined, to: undefined })}
                    disabled={(date) => date < new Date() || isDateBooked(date)}
                    numberOfMonths={1}
                    className="rounded-sm border-0"
                  />
                </div>
              </div>

              {totalDays > 0 && (
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between text-muted-foreground">
                    <span>{format(dateRange.from, 'MMM d')} - {format(dateRange.to, 'MMM d')}</span>
                    <span>{totalDays} day{totalDays > 1 ? 's' : ''}</span>
                  </div>
                  <Separator className="bg-border/50" />
                  <div className="flex justify-between font-bold text-foreground">
                    <span>Total</span>
                    <span className="text-primary">{calculateTotal().toLocaleString()} INR</span>
                  </div>
                  {totalDays >= 7 && <p className="text-[10px] text-accent">Weekly discount applied!</p>}
                </div>
              )}

              {showConfirm && totalDays > 0 ? (
                <div className="space-y-4 p-4 bg-secondary/30 border border-primary/20 rounded-sm" data-testid="booking-confirmation">
                  <h4 className="font-heading font-bold text-sm uppercase tracking-wider text-primary">Confirm Booking</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span className="text-muted-foreground">Bike</span><span className="font-bold">{bike.name}</span></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">Pickup</span><span>{format(dateRange.from, 'MMM d, yyyy')}</span></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">Return</span><span>{format(dateRange.to, 'MMM d, yyyy')}</span></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">Duration</span><span>{totalDays} day{totalDays > 1 ? 's' : ''}</span></div>
                    <Separator className="bg-border/50" />
                    <div className="flex justify-between"><span className="text-muted-foreground">Rate</span><span>{bike.daily_rate} INR/day</span></div>
                    <div className="flex justify-between font-bold text-base"><span>Total</span><span className="text-primary">{calculateTotal().toLocaleString()} INR</span></div>
                  </div>
                  <p className="text-[10px] text-muted-foreground">Payment will be processed via our secure gateway (MOCK). Free cancellation up to 24h before pickup.</p>
                  <div className="flex gap-2">
                    <Button variant="ghost" className="flex-1 text-xs" onClick={() => setShowConfirm(false)} data-testid="cancel-confirm-btn">Back</Button>
                    <Button
                      onClick={handleBooking}
                      disabled={booking}
                      className="flex-1 bg-primary text-primary-foreground hover:bg-primary/90 font-bold uppercase tracking-wider rounded-sm"
                      data-testid="confirm-booking-btn"
                    >
                      {booking ? 'Processing...' : 'Confirm & Pay'}
                    </Button>
                  </div>
                </div>
              ) : (
                <Button
                  onClick={handleBooking}
                  disabled={!totalDays || booking}
                  className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-bold uppercase tracking-wider rounded-sm h-12"
                  data-testid="book-now-btn"
                >
                  {booking ? 'Booking...' : !user ? 'Sign In to Book' : totalDays ? `Book for ${calculateTotal().toLocaleString()} INR` : 'Select Dates'}
                </Button>
              )}

              <p className="text-[10px] text-muted-foreground text-center">
                Free cancellation up to 24h before pickup. Late return penalty: 1.5x daily rate.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
