import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Mountain, Star, MapPin, ChevronRight, Search, Shield, Clock, Users } from 'lucide-react';
import api from '../lib/api';

function BikeCard({ bike }) {
  const mainImage = bike.images?.[0] || 'https://images.unsplash.com/photo-1630693147522-1169cad4986e?q=80&w=600&auto=format&fit=crop';
  return (
    <Link to={`/bikes/${bike.bike_id}`} className="group block" data-testid={`bike-card-${bike.bike_id}`}>
      <div className="aspect-[4/3] rounded-xl overflow-hidden mb-3">
        <img src={mainImage} alt={bike.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
      </div>
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <h3 className="font-heading font-bold text-[15px] text-foreground truncate">{bike.name}</h3>
          <p className="text-sm text-muted-foreground flex items-center gap-1 mt-0.5">
            <MapPin className="w-3.5 h-3.5 flex-shrink-0" /> {bike.shop_name || 'Leh, Ladakh'}
          </p>
        </div>
        {bike.average_rating > 0 && (
          <div className="flex items-center gap-1 flex-shrink-0 ml-2">
            <Star className="w-3.5 h-3.5 fill-foreground text-foreground" />
            <span className="text-sm font-medium">{bike.average_rating?.toFixed(1)}</span>
          </div>
        )}
      </div>
      <p className="mt-1 text-[15px]"><span className="font-bold">{bike.daily_rate?.toLocaleString()} INR</span> <span className="text-muted-foreground font-normal">/ day</span></p>
    </Link>
  );
}

export default function Landing() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [featuredBikes, setFeaturedBikes] = useState([]);
  const [stats, setStats] = useState({});

  useEffect(() => {
    api.get('/bikes?limit=8').then(res => setFeaturedBikes(res.data.bikes || [])).catch(() => {});
    api.get('/analytics/platform').then(res => setStats(res.data.overview || {})).catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-background" data-testid="landing-page">
      {/* Hero */}
      <section className="relative h-[85vh] min-h-[600px] overflow-hidden" data-testid="hero-section">
        <img
          src="https://images.unsplash.com/photo-1768410318044-8a43bf8fdb2c?q=80&w=2400&auto=format&fit=crop"
          alt="Bikers by Pangong lake with mountains"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="hero-gradient absolute inset-0" />
        <div className="relative z-10 h-full flex flex-col items-center justify-end pb-20 px-6 text-center text-white">
          <h1 className="font-heading font-extrabold text-4xl sm:text-5xl lg:text-6xl leading-tight max-w-3xl">
            Ride the highest roads on earth
          </h1>
          <p className="mt-4 text-base sm:text-lg text-white/80 font-body max-w-xl">
            Rent verified motorcycles from local shops in Ladakh. Khardung La, Pangong Lake, Nubra Valley — your adventure starts here.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 mt-8">
            <Button
              onClick={() => navigate('/marketplace')}
              className="bg-primary text-white hover:bg-primary/90 font-bold px-8 py-6 rounded-xl text-base shadow-lg"
              data-testid="hero-explore-btn"
            >
              <Search className="w-4 h-4 mr-2" /> Explore Bikes
            </Button>
            <Button
              onClick={() => navigate('/marketplace')}
              variant="outline"
              className="border-white/30 text-white hover:bg-white/10 font-medium px-8 py-6 rounded-xl text-base backdrop-blur"
              data-testid="hero-browse-btn"
            >
              See all bikes
            </Button>
          </div>
        </div>
      </section>

      {/* Trust Bar */}
      <section className="py-8 border-b border-border" data-testid="stats-section">
        <div className="max-w-6xl mx-auto px-6 flex flex-wrap justify-center gap-10 md:gap-16">
          {[
            { val: `${stats.total_bikes || 50}+`, label: 'Bikes Available' },
            { val: `${stats.total_shops || 12}`, label: 'Verified Shops' },
            { val: '2,500+', label: 'Happy Riders' },
            { val: '15+', label: 'Routes Covered' },
          ].map(s => (
            <div key={s.label} className="text-center">
              <p className="font-heading font-extrabold text-2xl text-foreground">{s.val}</p>
              <p className="text-xs text-muted-foreground font-medium mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Why Ladakh Moto */}
      <section className="py-16 md:py-20 px-6 md:px-12 bg-secondary/50">
        <div className="max-w-6xl mx-auto">
          <h2 className="font-heading font-bold text-2xl text-center text-foreground mb-10">Why riders choose us</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { icon: Shield, title: 'Verified Shops', desc: 'Every shop is personally vetted. Bikes are serviced and insured for high-altitude rides.' },
              { icon: Clock, title: 'Instant Booking', desc: 'Real-time availability, transparent pricing, and instant booking confirmation.' },
              { icon: Users, title: 'Local Experts', desc: 'Shop owners are local riders who know every pass, every turn, every chai stop.' },
            ].map(f => (
              <div key={f.title} className="text-center px-4">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                  <f.icon className="w-5 h-5 text-primary" />
                </div>
                <h3 className="font-heading font-bold text-base text-foreground mb-2">{f.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Bikes */}
      {featuredBikes.length > 0 && (
        <section className="py-16 md:py-20 px-6 md:px-12 lg:px-24" data-testid="featured-section">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between mb-8">
              <h2 className="font-heading font-bold text-2xl text-foreground">Popular bikes in Ladakh</h2>
              <Link
                to="/marketplace"
                className="text-sm font-semibold text-primary hover:text-primary/80 transition-colors flex items-center gap-1"
                data-testid="view-all-bikes-link"
              >
                View all <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {featuredBikes.map(bike => <BikeCard key={bike.bike_id} bike={bike} />)}
            </div>
          </div>
        </section>
      )}

      {/* Destination Gallery */}
      <section className="py-16 md:py-20 px-6 md:px-12 lg:px-24 bg-secondary/50">
        <div className="max-w-7xl mx-auto">
          <h2 className="font-heading font-bold text-2xl text-foreground mb-8 text-center">Where will you ride?</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { name: 'Khardung La', img: 'https://images.unsplash.com/photo-1770614956862-a143fb5e4921?q=80&w=600&auto=format&fit=crop' },
              { name: 'Pangong Lake', img: 'https://images.unsplash.com/photo-1762701254454-889d0cb98c30?q=80&w=600&auto=format&fit=crop' },
              { name: 'Nubra Valley', img: 'https://images.unsplash.com/photo-1768410318326-0b8a4db813f1?q=80&w=600&auto=format&fit=crop' },
              { name: 'Magnetic Hill', img: 'https://images.unsplash.com/photo-1630693147522-1169cad4986e?q=80&w=600&auto=format&fit=crop' },
            ].map(d => (
              <div key={d.name} className="relative aspect-[3/4] rounded-xl overflow-hidden group cursor-pointer" onClick={() => navigate('/marketplace')}>
                <img src={d.img} alt={d.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
                <p className="absolute bottom-4 left-4 font-heading font-bold text-white text-base">{d.name}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA — Shop Owners */}
      <section className="py-20 md:py-28 px-6 md:px-12 lg:px-24 relative overflow-hidden" data-testid="cta-section">
        <div className="absolute inset-0">
          <img
            src="https://images.unsplash.com/photo-1762696782497-2b39df0f4523?q=80&w=2000&auto=format&fit=crop"
            alt="Motorcyclists with stupas and mountains"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-black/50" />
        </div>
        <div className="relative z-10 max-w-2xl mx-auto text-center text-white">
          <h2 className="font-heading font-extrabold text-3xl sm:text-4xl leading-tight">
            Own a bike shop in Ladakh?
          </h2>
          <p className="mt-4 text-base text-white/80 font-body max-w-lg mx-auto">
            List your fleet, manage bookings, and grow your revenue. Join the marketplace that 2,500+ riders trust.
          </p>
          <Button
            onClick={() => navigate('/apply?type=shop_owner')}
            className="mt-8 bg-white text-foreground hover:bg-white/90 font-bold px-10 py-6 rounded-xl text-base shadow-lg"
            data-testid="cta-list-bikes-btn"
          >
            Start Listing <ChevronRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </section>

      {/* CTA — Travel Agents */}
      <section className="py-16 md:py-20 px-6 md:px-12 lg:px-24 bg-secondary/50" data-testid="cta-agent-section">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="font-heading font-bold text-2xl text-foreground">
            Travel agents & hotels — earn by referring riders
          </h2>
          <p className="mt-3 text-sm text-muted-foreground font-body max-w-md mx-auto">
            Partner with Ladakh Moto and earn commission on every booking you refer.
          </p>
          <Button
            onClick={() => navigate('/apply?type=travel_agent')}
            variant="outline"
            className="mt-6 border-foreground/20 hover:bg-foreground/5 font-bold px-8 py-5 rounded-xl text-sm"
            data-testid="cta-agent-register-btn"
          >
            Register as Partner <ChevronRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-12 px-6 md:px-12 lg:px-24" data-testid="footer">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Mountain className="w-5 h-5 text-primary" strokeWidth={2} />
            <span className="font-heading font-bold text-base">Ladakh Moto</span>
          </div>
          <p className="text-xs text-muted-foreground font-body">
            Leh, Ladakh, India &middot; Built for adventure
          </p>
        </div>
      </footer>
    </div>
  );
}
