import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Mountain, ChevronRight, Star, Shield, Clock, Map } from 'lucide-react';
import BikeCard from '../components/BikeCard';
import api from '../lib/api';

export default function Landing() {
  const [featuredBikes, setFeaturedBikes] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchBikes = async () => {
      try {
        const res = await api.get('/bikes?limit=4');
        setFeaturedBikes(res.data.bikes || []);
      } catch {}
    };
    fetchBikes();
  }, []);

  return (
    <div className="min-h-screen bg-background" data-testid="landing-page">
      {/* Hero Section */}
      <section className="relative h-[90vh] flex items-center overflow-hidden" data-testid="hero-section">
        <div className="absolute inset-0">
          <img
            src="https://images.unsplash.com/photo-1700891591563-5327de496cfd?q=80&w=2000&auto=format&fit=crop"
            alt="Ladakh mountain road"
            className="w-full h-full object-cover"
          />
          <div className="hero-gradient absolute inset-0" />
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-6 md:px-12 lg:px-24 w-full">
          <div className="max-w-2xl">
            <Badge variant="outline" className="border-primary/50 text-primary rounded-sm mb-6 uppercase tracking-widest text-[10px] font-bold px-3 py-1">
              Ladakh's #1 Bike Rental Platform
            </Badge>
            <h1 className="font-heading font-extrabold text-4xl sm:text-5xl lg:text-6xl uppercase tracking-tight leading-none text-foreground animate-fade-up">
              Ride The Roof
              <br />
              <span className="text-primary">Of The World</span>
            </h1>
            <p className="mt-6 text-base md:text-lg text-muted-foreground font-body leading-relaxed max-w-lg animate-fade-up stagger-2" style={{animationDelay: '0.2s'}}>
              Rent premium motorcycles from verified local shops. Explore Khardung La, Pangong Lake, and Nubra Valley on your terms.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row gap-4 animate-fade-up stagger-3" style={{animationDelay: '0.3s'}}>
              <Button
                onClick={() => navigate('/marketplace')}
                className="bg-primary text-primary-foreground hover:bg-primary/90 font-bold uppercase tracking-wider px-8 py-6 rounded-sm text-sm"
                data-testid="hero-explore-btn"
              >
                Explore Bikes <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
              <Button
                onClick={() => navigate('/shop')}
                variant="outline"
                className="border-white/20 text-white hover:bg-white/10 font-bold uppercase tracking-wider px-8 py-6 rounded-sm text-sm"
                data-testid="hero-list-btn"
              >
                List Your Bikes
              </Button>
            </div>
          </div>
        </div>

        {/* Stats bar */}
        <div className="absolute bottom-0 left-0 right-0 bg-black/50 backdrop-blur-md border-t border-white/10">
          <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24 py-4 flex flex-wrap gap-8 md:gap-16">
            {[
              { label: 'Bikes Available', value: '50+' },
              { label: 'Verified Shops', value: '12' },
              { label: 'Happy Riders', value: '2,500+' },
              { label: 'Routes Covered', value: '15+' },
            ].map((stat) => (
              <div key={stat.label} className="text-center sm:text-left">
                <p className="font-heading font-bold text-xl sm:text-2xl text-primary">{stat.value}</p>
                <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 md:py-32 px-6 md:px-12 lg:px-24 noise-bg relative" data-testid="features-section">
        <div className="relative z-10 max-w-7xl mx-auto">
          <p className="uppercase tracking-widest text-xs font-bold text-accent mb-3">Why Ladakh Moto</p>
          <h2 className="font-heading font-bold text-2xl sm:text-3xl uppercase tracking-tight text-foreground">
            Built for the mountains
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-12">
            {[
              { icon: Shield, title: 'Verified Shops', desc: 'Every shop is verified. Every bike inspected before handover.' },
              { icon: Clock, title: 'Instant Booking', desc: 'No waiting. Book online, pick up at the shop. Helmets included.' },
              { icon: Star, title: 'Rated by Riders', desc: 'Real reviews from real riders who conquered the same passes.' },
              { icon: Map, title: 'Route Ready', desc: 'Bikes prepped for Khardung La, Chang La, and beyond. GPS mounts standard.' },
            ].map(({ icon: Icon, title, desc }) => (
              <div
                key={title}
                className="bg-card border border-border/50 p-6 rounded-sm hover:border-primary/30 transition-colors group"
              >
                <div className="w-10 h-10 bg-primary/10 flex items-center justify-center rounded-sm mb-4 group-hover:bg-primary/20 transition-colors">
                  <Icon className="w-5 h-5 text-primary" strokeWidth={1.5} />
                </div>
                <h3 className="font-heading font-bold text-base uppercase tracking-tight text-foreground">{title}</h3>
                <p className="text-sm text-muted-foreground mt-2 leading-relaxed font-body">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Bikes */}
      {featuredBikes.length > 0 && (
        <section className="py-24 md:py-32 px-6 md:px-12 lg:px-24 bg-card/30" data-testid="featured-section">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-end justify-between mb-12">
              <div>
                <p className="uppercase tracking-widest text-xs font-bold text-accent mb-3">Featured Fleet</p>
                <h2 className="font-heading font-bold text-2xl sm:text-3xl uppercase tracking-tight text-foreground">
                  Popular rides
                </h2>
              </div>
              <Link
                to="/marketplace"
                className="text-sm font-bold uppercase tracking-wider text-primary hover:text-primary/80 transition-colors flex items-center gap-1"
                data-testid="view-all-bikes-link"
              >
                View All <ChevronRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {featuredBikes.map((bike) => (
                <BikeCard key={bike.bike_id} bike={bike} />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* CTA Section */}
      <section className="py-24 md:py-32 px-6 md:px-12 lg:px-24 relative overflow-hidden" data-testid="cta-section">
        <div className="absolute inset-0">
          <img
            src="https://images.unsplash.com/photo-1634635383310-5ba4ea9a1d33?q=80&w=2000&auto=format&fit=crop"
            alt="Ladakh landscape"
            className="w-full h-full object-cover opacity-20"
          />
        </div>
        <div className="relative z-10 max-w-3xl mx-auto text-center">
          <p className="uppercase tracking-widest text-xs font-bold text-accent mb-3">For Shop Owners</p>
          <h2 className="font-heading font-bold text-2xl sm:text-3xl lg:text-4xl uppercase tracking-tight text-foreground">
            Own a bike shop in Ladakh?
          </h2>
          <p className="mt-4 text-base text-muted-foreground font-body max-w-lg mx-auto">
            List your fleet, manage bookings, and track revenue. Join the marketplace that tourists trust.
          </p>
          <Button
            onClick={() => navigate('/shop')}
            className="mt-8 bg-primary text-primary-foreground hover:bg-primary/90 font-bold uppercase tracking-wider px-10 py-6 rounded-sm text-sm"
            data-testid="cta-list-bikes-btn"
          >
            Start Listing <ChevronRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/50 py-12 px-6 md:px-12 lg:px-24" data-testid="footer">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Mountain className="w-5 h-5 text-primary" strokeWidth={1.5} />
            <span className="font-heading font-bold uppercase tracking-wider text-sm">Ladakh Moto Market</span>
          </div>
          <p className="text-xs text-muted-foreground font-body">
            Leh, Ladakh, India &middot; Built for adventure
          </p>
        </div>
      </footer>
    </div>
  );
}
