import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Search, Star, MapPin, SlidersHorizontal } from 'lucide-react';
import api from '../lib/api';

function BikeCard({ bike }) {
  const mainImage = bike.images?.[0] || 'https://images.unsplash.com/photo-1630693147522-1169cad4986e?q=80&w=600&auto=format&fit=crop';
  return (
    <Link to={`/bikes/${bike.bike_id}`} className="group block" data-testid={`marketplace-bike-${bike.bike_id}`}>
      <div className="aspect-[4/3] rounded-xl overflow-hidden mb-3 bg-secondary">
        <img src={mainImage} alt={bike.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" loading="lazy" />
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
      <p className="mt-1 text-[15px]">
        <span className="font-bold">{bike.daily_rate?.toLocaleString()} INR</span>
        <span className="text-muted-foreground font-normal"> / day</span>
      </p>
    </Link>
  );
}

export default function Marketplace() {
  const [bikes, setBikes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [bikeType, setBikeType] = useState('all');
  const [sortBy, setSortBy] = useState('name');

  useEffect(() => {
    const fetchBikes = async () => {
      try {
        const params = {};
        if (search) params.search = search;
        if (bikeType !== 'all') params.bike_type = bikeType;
        if (sortBy) params.sort_by = sortBy;
        const res = await api.get('/bikes', { params });
        setBikes(res.data.bikes || []);
      } catch {}
      setLoading(false);
    };
    fetchBikes();
  }, [search, bikeType, sortBy]);

  return (
    <div className="min-h-screen bg-background pt-20" data-testid="marketplace-page">
      <div className="max-w-7xl mx-auto px-6 md:px-12 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="font-heading font-extrabold text-3xl text-foreground">
            Explore bikes in Ladakh
          </h1>
          <p className="text-muted-foreground mt-1 text-sm">Find the perfect ride for your Himalayan adventure</p>
        </div>

        {/* Filters */}
        <div className="flex flex-col md:flex-row gap-3 mb-8 p-4 bg-secondary/50 rounded-xl border border-border" data-testid="marketplace-filters">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name, type..."
              className="pl-10 rounded-xl h-11 border-border bg-background"
              data-testid="search-input"
            />
          </div>
          <Select value={bikeType} onValueChange={setBikeType}>
            <SelectTrigger className="w-full md:w-44 rounded-xl h-11 border-border bg-background" data-testid="type-filter">
              <SlidersHorizontal className="w-4 h-4 mr-2 text-muted-foreground" />
              <SelectValue placeholder="All Types" />
            </SelectTrigger>
            <SelectContent className="bg-background border-border rounded-xl shadow-lg">
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="cruiser">Cruiser</SelectItem>
              <SelectItem value="adventure">Adventure</SelectItem>
              <SelectItem value="sport">Sport</SelectItem>
              <SelectItem value="standard">Standard</SelectItem>
              <SelectItem value="scooter">Scooter</SelectItem>
            </SelectContent>
          </Select>
          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-full md:w-44 rounded-xl h-11 border-border bg-background" data-testid="sort-filter">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent className="bg-background border-border rounded-xl shadow-lg">
              <SelectItem value="name">Name</SelectItem>
              <SelectItem value="price_low">Price: Low to High</SelectItem>
              <SelectItem value="price_high">Price: High to Low</SelectItem>
              <SelectItem value="rating">Rating</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Grid */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="aspect-[4/3] rounded-xl bg-secondary mb-3" />
                <div className="h-4 bg-secondary rounded w-2/3 mb-2" />
                <div className="h-3 bg-secondary rounded w-1/2" />
              </div>
            ))}
          </div>
        ) : bikes.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-xl font-heading font-bold text-foreground">No bikes found</p>
            <p className="text-muted-foreground mt-2 text-sm">Try adjusting your search or filters</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6" data-testid="bike-grid">
            {bikes.map(bike => <BikeCard key={bike.bike_id} bike={bike} />)}
          </div>
        )}
      </div>
    </div>
  );
}
