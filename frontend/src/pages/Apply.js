import { useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Mountain, Store, Compass, CheckCircle, Mail, Phone, User, MapPin, Bike } from 'lucide-react';
import { toast } from 'sonner';
import { submitApplication } from '../lib/api';

export default function Apply() {
  const [searchParams] = useSearchParams();
  const type = searchParams.get('type') || 'shop_owner';
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const isShop = type === 'shop_owner';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const fd = new FormData(e.target);

    const data = {
      application_type: type,
      name: fd.get('name'),
      email: fd.get('email'),
      phone: fd.get('phone'),
    };

    if (isShop) {
      data.shop_name = fd.get('shop_name');
      data.shop_address = fd.get('shop_address');
      data.total_bikes = parseInt(fd.get('total_bikes') || '0');
      data.bike_types = fd.get('bike_types');
      data.experience_years = parseInt(fd.get('experience_years') || '0');
      data.description = fd.get('description');
    } else {
      data.agency_name = fd.get('agency_name');
      data.agency_address = fd.get('agency_address');
      data.agency_type = fd.get('agency_type') || 'travel_agency';
      data.description = fd.get('description');
    }

    try {
      await submitApplication(data);
      setSubmitted(true);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Submission failed. Please try again.');
    }
    setLoading(false);
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-background pt-20 flex items-center justify-center px-6" data-testid="application-success">
        <div className="max-w-md text-center">
          <div className="w-16 h-16 bg-chart-3/10 border border-chart-3/30 rounded-sm flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-8 h-8 text-chart-3" strokeWidth={1.5} />
          </div>
          <h1 className="font-heading font-bold text-2xl uppercase tracking-tight text-foreground">Application Submitted</h1>
          <p className="text-muted-foreground font-body mt-3 leading-relaxed">
            Thank you for your interest! Our team will review your application and get back to you via email with your login credentials once approved.
          </p>
          <Button onClick={() => navigate('/')} className="mt-8 bg-primary text-primary-foreground hover:bg-primary/90 font-bold uppercase tracking-wider rounded-sm px-8" data-testid="back-home-btn">
            Back to Home
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pt-20" data-testid="apply-page">
      <div className="max-w-2xl mx-auto px-6 md:px-12 py-8">
        {/* Header */}
        <Link to="/" className="flex items-center gap-2 mb-8 text-muted-foreground hover:text-primary transition-colors">
          <Mountain className="w-5 h-5" strokeWidth={2} />
          <span className="font-heading font-bold text-sm">Ladakh Moto</span>
        </Link>

        <div className="flex items-center gap-3 mb-2">
          {isShop ? <Store className="w-6 h-6 text-primary" /> : <Compass className="w-6 h-6 text-primary" />}
        </div>
        <h1 className="font-heading font-extrabold text-2xl sm:text-3xl text-foreground mb-2">
          {isShop ? 'List Your Bikes on Ladakh Moto' : 'Partner with Ladakh Moto'}
        </h1>
        <p className="text-muted-foreground font-body text-sm mb-8">
          {isShop
            ? 'Fill in your shop details below. Our team will review and approve your account within 24 hours.'
            : 'Register as a travel agent or hotel partner. Earn commissions by referring customers to our platform.'
          }
        </p>

        <form onSubmit={handleSubmit} className="space-y-6 bg-card border border-border rounded-2xl shadow-sm p-6 md:p-8" data-testid="application-form">
          {/* Personal Info */}
          <div>
            <h3 className="font-heading font-bold text-sm uppercase tracking-wider mb-4">Contact Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Full Name *</Label>
                <div className="relative mt-1">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" strokeWidth={1.5} />
                  <Input name="name" required placeholder="Your full name" className="pl-10 bg-background border-border rounded-xl h-11" data-testid="apply-name" />
                </div>
              </div>
              <div>
                <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Email *</Label>
                <div className="relative mt-1">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" strokeWidth={1.5} />
                  <Input name="email" type="email" required placeholder="you@example.com" className="pl-10 bg-background border-border rounded-xl h-11" data-testid="apply-email" />
                </div>
              </div>
              <div className="md:col-span-2">
                <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Phone Number *</Label>
                <div className="relative mt-1">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" strokeWidth={1.5} />
                  <Input name="phone" required placeholder="+91-9876543210" className="pl-10 bg-background border-border rounded-xl h-11" data-testid="apply-phone" />
                </div>
              </div>
            </div>
          </div>

          {/* Shop-specific fields */}
          {isShop ? (
            <div>
              <h3 className="font-heading font-bold text-sm uppercase tracking-wider mb-4">Shop Details</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Shop Name *</Label>
                  <div className="relative mt-1">
                    <Store className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" strokeWidth={1.5} />
                    <Input name="shop_name" required placeholder="Himalayan Riders Leh" className="pl-10 bg-background border-border rounded-xl h-11" data-testid="apply-shop-name" />
                  </div>
                </div>
                <div className="md:col-span-2">
                  <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Shop Address *</Label>
                  <div className="relative mt-1">
                    <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" strokeWidth={1.5} />
                    <Input name="shop_address" required placeholder="Main Bazaar, Leh, Ladakh" className="pl-10 bg-background border-border rounded-xl h-11" data-testid="apply-shop-address" />
                  </div>
                </div>
                <div>
                  <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Total Bikes to List</Label>
                  <div className="relative mt-1">
                    <Bike className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" strokeWidth={1.5} />
                    <Input name="total_bikes" type="number" min="1" placeholder="10" className="pl-10 bg-background border-border rounded-xl h-11" data-testid="apply-total-bikes" />
                  </div>
                </div>
                <div>
                  <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Years of Experience</Label>
                  <Input name="experience_years" type="number" min="0" placeholder="5" className="bg-background border-border rounded-xl h-11 mt-1" data-testid="apply-experience" />
                </div>
                <div className="md:col-span-2">
                  <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Bike Types Available</Label>
                  <Input name="bike_types" placeholder="Royal Enfield, KTM, Honda..." className="bg-background border-border rounded-xl h-11 mt-1" data-testid="apply-bike-types" />
                </div>
              </div>
            </div>
          ) : (
            <div>
              <h3 className="font-heading font-bold text-sm uppercase tracking-wider mb-4">Agency / Hotel Details</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Agency / Hotel Name *</Label>
                  <Input name="agency_name" required placeholder="Ladakh Adventures Pvt Ltd" className="bg-background border-border rounded-xl h-11 mt-1" data-testid="apply-agency-name" />
                </div>
                <div>
                  <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Type</Label>
                  <Select name="agency_type" defaultValue="travel_agency">
                    <SelectTrigger className="bg-background border-border rounded-xl h-11 mt-1" data-testid="apply-agency-type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-950 border-zinc-800 rounded-sm">
                      <SelectItem value="travel_agency">Travel Agency</SelectItem>
                      <SelectItem value="hotel">Hotel / Guesthouse</SelectItem>
                      <SelectItem value="tour_operator">Tour Operator</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Address</Label>
                  <Input name="agency_address" placeholder="Location" className="bg-background border-border rounded-xl h-11 mt-1" data-testid="apply-agency-address" />
                </div>
              </div>
            </div>
          )}

          {/* Description */}
          <div>
            <Label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">
              {isShop ? 'Tell us about your shop' : 'Tell us about your business'}
            </Label>
            <Textarea name="description" placeholder={isShop ? 'What makes your shop unique? What services do you offer riders?' : 'Describe your agency/hotel and how you plan to refer customers...'} className="bg-background border-border rounded-xl mt-1" rows={3} data-testid="apply-description" />
          </div>

          <Button type="submit" disabled={loading} className="w-full bg-primary text-white hover:bg-primary/90 font-bold rounded-xl h-12 text-sm" data-testid="apply-submit-btn">
            {loading ? 'Submitting...' : 'Submit Application'}
          </Button>

          <p className="text-[10px] text-muted-foreground text-center">
            Already have an account? <Link to="/login" className="text-primary hover:text-primary/80">Sign In</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
