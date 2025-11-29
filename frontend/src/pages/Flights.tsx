import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Plane, Users, MapPin, Calendar, Search, Filter, TrendingUp, Clock, Map } from 'lucide-react';
import { api, type FlightRecord, type FlightRoute } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { FlightMap } from '@/components/flights/FlightMap';
import { formatEntityName } from '@/utils/nameFormat';

interface FlightStats {
  total_flights: number;
  unique_routes: number;
  unique_locations: number;
  top_passengers: Array<{ name: string; flights: number }>;
  aircraft_usage: Record<string, number>;
  busiest_airports: Record<string, number>;
}

/**
 * Flights Page
 *
 * Design Enhancement: URL Parameter Support
 * Rationale: Support deep linking from entity detail pages with pre-applied filters.
 * URL params: ?passenger=<name> for entity-specific flight filtering.
 *
 * Navigation Flow:
 * EntityDetail → /flights?passenger=Jeffrey%20Epstein → Auto-apply filter
 */
export function Flights() {
  const [searchParams] = useSearchParams();
  const [flights, setFlights] = useState<FlightRecord[]>([]);
  const [routes, setRoutes] = useState<FlightRoute[]>([]);
  const [stats, setStats] = useState<FlightStats | null>(null);
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [airports, setAirports] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);

  // Filters
  const [passengerFilter, setPassengerFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [startDateFilter, setStartDateFilter] = useState('');
  const [endDateFilter, setEndDateFilter] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  // View mode
  const [viewMode, setViewMode] = useState<'timeline' | 'routes' | 'passengers' | 'map'>('timeline');

  // Read URL parameters on mount
  useEffect(() => {
    const passengerParam = searchParams.get('passenger');
    if (passengerParam) {
      setPassengerFilter(decodeURIComponent(passengerParam));
      setShowFilters(true); // Show filters section when pre-filtered
    }
  }, [searchParams]);

  useEffect(() => {
    loadFlightData();
  }, []);

  const loadFlightData = async () => {
    try {
      setLoading(true);

      // Load both flights and routes
      const [flightsData, routesData] = await Promise.all([
        api.getFlights(),
        api.getFlightRoutes()
      ]);

      setFlights(flightsData.flights);
      setStats(flightsData.statistics);
      setRoutes(routesData.routes);
      setDateRange(routesData.date_range);
      setAirports(routesData.airports || {});
    } catch (error) {
      console.error('Failed to load flight data:', error);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = async () => {
    try {
      setLoading(true);
      const params: any = {};

      if (passengerFilter) params.passenger = passengerFilter;
      if (startDateFilter) params.start_date = startDateFilter;
      if (endDateFilter) params.end_date = endDateFilter;

      const flightsData = await api.getFlights(params);
      setFlights(flightsData.flights);
      setStats(flightsData.statistics);
    } catch (error) {
      console.error('Failed to apply filters:', error);
    } finally {
      setLoading(false);
    }
  };

  const clearFilters = () => {
    setPassengerFilter('');
    setSearchQuery('');
    setStartDateFilter('');
    setEndDateFilter('');
    loadFlightData();
  };

  const filteredFlights = flights.filter(flight => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      flight.passengers.some(p => p.toLowerCase().includes(query)) ||
      flight.origin.code.toLowerCase().includes(query) ||
      flight.destination.code.toLowerCase().includes(query) ||
      flight.origin.city.toLowerCase().includes(query) ||
      flight.destination.city.toLowerCase().includes(query)
    );
  });

  const parseDate = (dateStr: string): Date => {
    const [month, day, year] = dateStr.split('/');
    return new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
  };

  const formatDate = (dateStr: string): string => {
    try {
      const date = parseDate(dateStr);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  if (loading && flights.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent mb-4" />
          <p className="text-muted-foreground">Loading flight data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">Flight Logs</h1>
        <p className="text-muted-foreground">
          Explore {stats?.total_flights?.toLocaleString() || flights.length.toLocaleString()} flight records
          {dateRange.start && dateRange.end && (
            <> from {formatDate(dateRange.start)} to {formatDate(dateRange.end)}</>
          )}
        </p>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Flights</CardTitle>
              <Plane className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(stats.total_flights ?? flights.length).toLocaleString()}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Unique Routes</CardTitle>
              <MapPin className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(stats.unique_routes ?? 0).toLocaleString()}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Unique Passengers</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(stats.top_passengers?.length ?? 0).toLocaleString()}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Airports</CardTitle>
              <MapPin className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(stats.unique_locations ?? 0).toLocaleString()}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* View Mode Tabs */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setViewMode('timeline')}
          className={`px-4 py-2 font-medium transition-colors border-b-2 ${
            viewMode === 'timeline'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Clock className="h-4 w-4 inline mr-2" />
          Timeline
        </button>
        <button
          onClick={() => setViewMode('routes')}
          className={`px-4 py-2 font-medium transition-colors border-b-2 ${
            viewMode === 'routes'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <MapPin className="h-4 w-4 inline mr-2" />
          Routes
        </button>
        <button
          onClick={() => setViewMode('passengers')}
          className={`px-4 py-2 font-medium transition-colors border-b-2 ${
            viewMode === 'passengers'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Users className="h-4 w-4 inline mr-2" />
          Passengers
        </button>
        <button
          onClick={() => setViewMode('map')}
          className={`px-4 py-2 font-medium transition-colors border-b-2 ${
            viewMode === 'map'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Map className="h-4 w-4 inline mr-2" />
          Map
        </button>
      </div>

      {/* Filters */}
      <div className="space-y-4">
        {/* Search Bar */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search flights by passenger, location, or airport code..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button
            variant={showFilters ? 'default' : 'outline'}
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
        </div>

        {/* Advanced Filters */}
        {showFilters && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Filter Flights</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Passenger Name</label>
                  <Input
                    type="text"
                    placeholder="Enter passenger name..."
                    value={passengerFilter}
                    onChange={(e) => setPassengerFilter(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Start Date</label>
                  <Input
                    type="date"
                    value={startDateFilter}
                    onChange={(e) => setStartDateFilter(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">End Date</label>
                  <Input
                    type="date"
                    value={endDateFilter}
                    onChange={(e) => setEndDateFilter(e.target.value)}
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <Button onClick={applyFilters} disabled={loading}>
                  Apply Filters
                </Button>
                <Button variant="outline" onClick={clearFilters}>
                  Clear All
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Results Count */}
      <div className="text-sm text-muted-foreground">
        Showing {filteredFlights.length.toLocaleString()} of {flights.length.toLocaleString()} flights
      </div>

      {/* Timeline View */}
      {viewMode === 'timeline' && (
        <div className="space-y-4">
          {filteredFlights.length === 0 ? (
            <Card className="text-center py-12">
              <CardContent>
                <Plane className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-lg font-medium mb-1">No flights found</p>
                <p className="text-muted-foreground">
                  Try adjusting your search or filter criteria
                </p>
              </CardContent>
            </Card>
          ) : (
            filteredFlights.map((flight) => (
              <Card key={flight.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="pt-6">
                  <div className="grid md:grid-cols-[auto_1fr_auto] gap-6 items-start">
                    {/* Date */}
                    <div className="text-center min-w-[100px]">
                      <Calendar className="h-5 w-5 text-muted-foreground mx-auto mb-1" />
                      <div className="font-medium">{formatDate(flight.date)}</div>
                      <div className="text-xs text-muted-foreground">{flight.aircraft}</div>
                    </div>

                    {/* Route */}
                    <div className="flex-1 space-y-3">
                      <div className="flex items-center gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <MapPin className="h-4 w-4 text-muted-foreground" />
                            <div>
                              <div className="font-semibold">{flight.origin.code}</div>
                              <div className="text-sm text-muted-foreground">
                                {flight.origin.city}
                              </div>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 text-muted-foreground">
                          <div className="h-px flex-1 w-12 bg-border" />
                          <Plane className="h-4 w-4" />
                          <div className="h-px flex-1 w-12 bg-border" />
                        </div>

                        <div className="flex-1 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <div>
                              <div className="font-semibold">{flight.destination.code}</div>
                              <div className="text-sm text-muted-foreground">
                                {flight.destination.city}
                              </div>
                            </div>
                            <MapPin className="h-4 w-4 text-muted-foreground" />
                          </div>
                        </div>
                      </div>

                      {/* Passengers */}
                      {flight.passengers.length > 0 && (
                        <div className="pt-3 border-t">
                          <div className="flex items-start gap-2">
                            <Users className="h-4 w-4 text-muted-foreground mt-0.5" />
                            <div className="flex-1">
                              <div className="text-sm font-medium mb-1">
                                Passengers ({flight.passenger_count})
                              </div>
                              <div className="flex flex-wrap gap-1.5">
                                {flight.passengers.map((passenger, idx) => (
                                  <Badge key={idx} variant="secondary" className="text-xs">
                                    {formatEntityName(passenger)}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}

      {/* Routes View */}
      {viewMode === 'routes' && stats && (
        <div className="space-y-6">
          {/* Most Frequent Routes */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Most Frequent Routes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {routes.slice(0, 10).map((route, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                    <div className="flex items-center gap-3 flex-1">
                      <div className="font-bold text-muted-foreground w-6">{idx + 1}</div>
                      <div className="flex items-center gap-2">
                        <div className="text-sm">
                          <span className="font-semibold">{route.origin.code}</span>
                          <span className="text-muted-foreground mx-1">→</span>
                          <span className="font-semibold">{route.destination.code}</span>
                        </div>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {route.origin.city} → {route.destination.city}
                      </div>
                    </div>
                    <Badge variant="default">
                      {route.frequency} flights
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Busiest Airports */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="h-5 w-5" />
                Busiest Airports
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-3">
                {Object.entries(stats.busiest_airports).slice(0, 10).map(([code, count], idx) => (
                  <div key={code} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                    <div className="flex items-center gap-3">
                      <div className="font-bold text-muted-foreground w-6">{idx + 1}</div>
                      <div>
                        <div className="font-semibold">{code}</div>
                      </div>
                    </div>
                    <Badge variant="secondary">
                      {count} flights
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Passengers View */}
      {viewMode === 'passengers' && stats && (
        <div className="space-y-6">
          {/* Top Passengers */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Most Frequent Passengers
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {stats.top_passengers.map((passenger, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                    <div className="flex items-center gap-3 flex-1">
                      <div className="font-bold text-muted-foreground w-6">{idx + 1}</div>
                      <div className="flex-1">
                        <div className="font-medium">{formatEntityName(passenger.name)}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <Badge variant="default">
                        {passenger.flights} flights
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Aircraft Usage */}
          {Object.keys(stats.aircraft_usage).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Plane className="h-5 w-5" />
                  Aircraft Usage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-3">
                  {Object.entries(stats.aircraft_usage).map(([aircraft, count]) => (
                    <div key={aircraft} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                      <div className="font-medium">{aircraft}</div>
                      <Badge variant="secondary">
                        {count} flights
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Map View */}
      {viewMode === 'map' && routes.length > 0 && (
        <FlightMap
          routes={routes}
          airports={airports}
          dateRange={dateRange}
        />
      )}
    </div>
  );
}
