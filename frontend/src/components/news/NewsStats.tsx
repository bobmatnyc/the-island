import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { FileText, Calendar, Award, Users } from 'lucide-react';
import type { NewsStats } from '@/types/news';

interface NewsStatsProps {
  stats: NewsStats;
}

export function NewsStats({ stats }: NewsStatsProps) {
  // Format date
  const formatDate = (dateString: string) => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Prepare credibility chart data
  const credibilityData = [
    { name: 'High (≥90%)', value: stats.credibility_tiers.high, color: '#10b981' },
    { name: 'Medium (75-90%)', value: stats.credibility_tiers.medium, color: '#3b82f6' },
    { name: 'Low (<75%)', value: stats.credibility_tiers.low, color: '#6b7280' },
  ];

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Articles */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Articles</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_articles.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground mt-1">News articles indexed</p>
          </CardContent>
        </Card>

        {/* Date Range */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Date Range</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-sm font-bold">
              {formatDate(stats.date_range.earliest)}
            </div>
            <p className="text-xs text-muted-foreground">to</p>
            <div className="text-sm font-bold">
              {formatDate(stats.date_range.latest)}
            </div>
          </CardContent>
        </Card>

        {/* Top Publication */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Top Publication</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold">
              {stats.publications[0]?.name || 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats.publications[0]?.count.toLocaleString() || 0} articles
            </p>
          </CardContent>
        </Card>

        {/* Avg Credibility */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Credibility</CardTitle>
            <Award className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.total_articles > 0
                ? (
                    ((stats.credibility_tiers.high * 0.95 +
                      stats.credibility_tiers.medium * 0.825 +
                      stats.credibility_tiers.low * 0.5) /
                      stats.total_articles) *
                    100
                  ).toFixed(0)
                : 0}
              %
            </div>
            <p className="text-xs text-muted-foreground mt-1">Average score</p>
          </CardContent>
        </Card>
      </div>

      {/* Publications Chart */}
      {stats.publications.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Top Publications</CardTitle>
            <CardDescription>Articles by publication source</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stats.publications}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="name"
                  angle={-45}
                  textAnchor="end"
                  height={100}
                  interval={0}
                />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Credibility Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Credibility Distribution</CardTitle>
          <CardDescription>Articles by credibility tier</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Pie Chart */}
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={credibilityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry: any) => `${entry.name}: ${(entry.percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {credibilityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>

            {/* Legend */}
            <div className="space-y-3">
              {credibilityData.map((item) => (
                <div key={item.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-4 h-4 rounded"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-sm font-medium">{item.name}</span>
                  </div>
                  <Badge variant="secondary">{item.value.toLocaleString()}</Badge>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Most Mentioned Entities */}
      {stats.top_entities.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Most Mentioned Entities
            </CardTitle>
            <CardDescription>Top 10 entities by mention count</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {stats.top_entities.map((entity, index) => (
                <div
                  key={entity.name}
                  className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className="w-8 text-center">
                      {index + 1}
                    </Badge>
                    <span className="font-medium">{entity.name}</span>
                  </div>
                  <Badge variant="secondary">
                    {entity.mention_count.toLocaleString()} mentions
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
