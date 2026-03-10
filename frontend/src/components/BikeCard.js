import { Link } from 'react-router-dom';
import { Star, MapPin, Fuel } from 'lucide-react';
import { Badge } from '../components/ui/badge';

export default function BikeCard({ bike }) {
  const mainImage = bike.images?.[0] || 'https://images.unsplash.com/photo-1558618666-fcd25c85f82e?q=80&w=800&auto=format&fit=crop';

  return (
    <Link
      to={`/bikes/${bike.bike_id}`}
      className="bg-card border border-border/50 hover:border-primary/50 transition-all duration-300 group relative overflow-hidden rounded-sm block card-shine"
      data-testid={`bike-card-${bike.bike_id}`}
    >
      {/* Image */}
      <div className="aspect-[4/3] overflow-hidden bg-muted relative">
        <img
          src={mainImage}
          alt={bike.name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          loading="lazy"
        />
        <div className="absolute top-3 left-3">
          <Badge variant="secondary" className="bg-black/70 text-white border-0 rounded-sm text-[10px] uppercase tracking-widest font-bold">
            {bike.type}
          </Badge>
        </div>
        {bike.rating > 0 && (
          <div className="absolute top-3 right-3 flex items-center gap-1 bg-black/70 px-2 py-1 rounded-sm">
            <Star className="w-3 h-3 fill-primary text-primary" />
            <span className="text-xs font-bold text-white">{bike.rating}</span>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        <h3 className="font-heading font-bold text-lg uppercase tracking-tight text-foreground group-hover:text-primary transition-colors leading-tight">
          {bike.name}
        </h3>
        <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <MapPin className="w-3 h-3" strokeWidth={1.5} />
            {bike.location}
          </span>
          <span className="flex items-center gap-1">
            <Fuel className="w-3 h-3" strokeWidth={1.5} />
            {bike.engine_cc}cc
          </span>
        </div>
        {bike.shop_name && (
          <p className="text-xs text-muted-foreground mt-1">{bike.shop_name}</p>
        )}

        {/* Price */}
        <div className="mt-3 pt-3 border-t border-border/50 flex items-end justify-between">
          <div>
            <span className="text-2xl font-heading font-bold text-primary">{bike.daily_rate}</span>
            <span className="text-xs text-muted-foreground ml-1">INR/day</span>
          </div>
          {bike.weekly_rate && (
            <span className="text-xs text-muted-foreground">
              {bike.weekly_rate} INR/week
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
