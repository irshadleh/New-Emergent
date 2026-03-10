import { useState, useEffect } from 'react';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { Search, SlidersHorizontal, X } from 'lucide-react';
import BikeCard from '../components/BikeCard';
import api from '../lib/api';

export default function Marketplace() {
  const [bikes, setBikes] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [locationFilter, setLocationFilter] = useState('all');
  const [sortBy, setSortBy] = useState('default');
  const [page, setPage] = useState(1);

  useEffect(() => {
    const fetchBikes = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (search) params.set('search', search);
        if (typeFilter !== 'all') params.set('type', typeFilter);
        if (locationFilter !== 'all') params.set('location', locationFilter);
        params.set('page', page);
        params.set('limit', 12);

        const res = await api.get(`/bikes?${params.toString()}`);
        let bikeList = res.data.bikes || [];

        if (sortBy === 'price_low') bikeList.sort((a, b) => a.daily_rate - b.daily_rate);
        if (sortBy === 'price_high') bikeList.sort((a, b) => b.daily_rate - a.daily_rate);
        if (sortBy === 'rating') bikeList.sort((a, b) => b.rating - a.rating);

        setBikes(bikeList);
        setTotal(res.data.total || 0);
      } catch {}
      setLoading(false);
    };
    fetchBikes();
  }, [search, typeFilter, locationFilter, sortBy, page]);

  const clearFilters = () => {
    setSearch('');
    setTypeFilter('all');
    setLocationFilter('all');
    setSortBy('default');
    setPage(1);
  };

  const hasFilters = search || typeFilter !== 'all' || locationFilter !== 'all';

  return (
    <div className="min-h-screen bg-background pt-20" data-testid="marketplace-page">
      {/* Header */}
      <div className="px-6 md:px-12 lg:px-24 pt-8 pb-4 max-w-7xl mx-auto">
        <p className="uppercase tracking-widest text-xs font-bold text-accent mb-2">Marketplace</p>
        <div className="flex items-end justify-between">
          <h1 className="font-heading font-bold text-3xl sm:text-4xl uppercase tracking-tight text-foreground">
            Find Your Ride
          </h1>
          <span className="text-sm text-muted-foreground font-body">{total} bikes available</span>
        </div>
      </div>

      {/* Filters */}
      <div className="px-6 md:px-12 lg:px-24 py-6 max-w-7xl mx-auto" data-testid="marketplace-filters">
        <div className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" strokeWidth={1.5} />
            <Input
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              placeholder="Search bikes, brands..."
              className="pl-10 bg-background border-border rounded-none h-11"
              data-testid="marketplace-search"
            />
          </div>

          <Select value={typeFilter} onValueChange={(v) => { setTypeFilter(v); setPage(1); }}>
            <SelectTrigger className="w-full md:w-44 bg-background border-border rounded-none h-11" data-testid="filter-type">
              <SlidersHorizontal className="w-3.5 h-3.5 mr-2" strokeWidth={1.5} />
              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent className="bg-zinc-950 border-zinc-800 rounded-sm">
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="adventure">Adventure</SelectItem>
              <SelectItem value="cruiser">Cruiser</SelectItem>
              <SelectItem value="sport">Sport</SelectItem>
              <SelectItem value="scooter">Scooter</SelectItem>
            </SelectContent>
          </Select>

          <Select value={locationFilter} onValueChange={(v) => { setLocationFilter(v); setPage(1); }}>
            <SelectTrigger className="w-full md:w-44 bg-background border-border rounded-none h-11" data-testid="filter-location">
              <SelectValue placeholder="Location" />
            </SelectTrigger>
            <SelectContent className="bg-zinc-950 border-zinc-800 rounded-sm">
              <SelectItem value="all">All Locations</SelectItem>
              <SelectItem value="Leh">Leh</SelectItem>
              <SelectItem value="Nubra">Nubra Valley</SelectItem>
              <SelectItem value="Pangong">Pangong</SelectItem>
            </SelectContent>
          </Select>

          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-full md:w-44 bg-background border-border rounded-none h-11" data-testid="filter-sort">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent className="bg-zinc-950 border-zinc-800 rounded-sm">
              <SelectItem value="default">Default</SelectItem>
              <SelectItem value="price_low">Price: Low to High</SelectItem>
              <SelectItem value="price_high">Price: High to Low</SelectItem>
              <SelectItem value="rating">Highest Rated</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {hasFilters && (
          <div className="flex items-center gap-2 mt-3">
            <span className="text-xs text-muted-foreground">Active filters:</span>
            {search && <Badge variant="secondary" className="rounded-sm text-xs">{search} <X className="w-3 h-3 ml-1 cursor-pointer" onClick={() => setSearch('')} /></Badge>}
            {typeFilter !== 'all' && <Badge variant="secondary" className="rounded-sm text-xs capitalize">{typeFilter} <X className="w-3 h-3 ml-1 cursor-pointer" onClick={() => setTypeFilter('all')} /></Badge>}
            {locationFilter !== 'all' && <Badge variant="secondary" className="rounded-sm text-xs">{locationFilter} <X className="w-3 h-3 ml-1 cursor-pointer" onClick={() => setLocationFilter('all')} /></Badge>}
            <button onClick={clearFilters} className="text-xs text-destructive hover:text-destructive/80 ml-2">Clear all</button>
          </div>
        )}
      </div>

      {/* Grid */}
      <div className="px-6 md:px-12 lg:px-24 pb-24 max-w-7xl mx-auto">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="bg-card border border-border/50 rounded-sm animate-pulse">
                <div className="aspect-[4/3] bg-secondary" />
                <div className="p-4 space-y-3">
                  <div className="h-5 bg-secondary rounded w-3/4" />
                  <div className="h-3 bg-secondary rounded w-1/2" />
                  <div className="h-8 bg-secondary rounded w-1/3 mt-3" />
                </div>
              </div>
            ))}
          </div>
        ) : bikes.length === 0 ? (
          <div className="text-center py-24">
            <p className="text-muted-foreground font-body">No bikes found matching your criteria.</p>
            <button onClick={clearFilters} className="text-primary text-sm mt-2 hover:text-primary/80">Clear filters</button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6" data-testid="bikes-grid">
            {bikes.map((bike) => (
              <BikeCard key={bike.bike_id} bike={bike} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
