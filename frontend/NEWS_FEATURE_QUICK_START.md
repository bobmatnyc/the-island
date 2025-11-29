# News Feature - Quick Start Guide

## 🚀 Getting Started (5 Minutes)

### 1. Prerequisites
Ensure backend API is running on `http://localhost:8000`:
```bash
# In project root
cd server
python app.py  # or your backend start command
```

### 2. Start Frontend
```bash
cd frontend
npm install  # if not already installed
npm run dev  # starts on http://localhost:5173
```

### 3. Access News Feature
Navigate to: `http://localhost:5173/news`

## 📋 Quick Feature Tour

### Main News Page (`/news`)
1. **Search**: Type in search box (e.g., "arrest", "investigation")
2. **Filter by Entity**: Enter entity name (e.g., "Jeffrey Epstein", "Prince Andrew")
3. **Filter by Publication**: Click publications in left sidebar
4. **Filter by Credibility**: Drag slider to set minimum score
5. **View Statistics**: Click "Show Statistics" button
6. **Click Article**: Opens detail view with full content

### Article Detail (`/news/:articleId`)
1. View full article content
2. See entity mentions (clickable to entity pages)
3. Read similar articles
4. Access original source or archive link
5. Share article via link or Twitter/X

### Entity Pages (`/entities/:name`)
1. Scroll to "News Coverage" section
2. View articles mentioning this entity
3. Click "View All News" to see filtered news page

## 🔧 Common Tasks

### Add News to Timeline
Already integrated! The Timeline page uses `useTimelineNews` hook:
```typescript
import { useTimelineNews } from '@/hooks/useTimelineNews';

const { articlesByDate, loading, totalArticles } = useTimelineNews(
  { start: '2000-01-01', end: '2024-12-31' },
  true // enabled
);
```

### Filter Articles by Entity
```typescript
import { filterArticlesByEntity } from '@/utils/entityNewsFilter';
import { newsApi } from '@/services/newsApi';

const articles = await newsApi.searchNews({ limit: 100 });
const filtered = filterArticlesByEntity(articles, 'Entity Name');
```

### Get Similar Articles
```typescript
import { newsApi } from '@/services/newsApi';

const similarArticles = await newsApi.getSimilarArticles(articleId, 5);
```

### Create Custom News Widget
```typescript
import { ArticleCard } from '@/components/news/ArticleCard';
import { newsApi } from '@/services/newsApi';

function CustomWidget() {
  const [articles, setArticles] = useState([]);

  useEffect(() => {
    newsApi.searchNews({ limit: 5 }).then(setArticles);
  }, []);

  return (
    <div>
      {articles.map(article => (
        <ArticleCard key={article.id} article={article} compact />
      ))}
    </div>
  );
}
```

## 🎨 Component Reference

### ArticleCard
```typescript
import { ArticleCard } from '@/components/news/ArticleCard';

<ArticleCard
  article={newsArticle}
  onEntityClick={(entity) => console.log(entity)}
  compact={false}  // or true for smaller variant
/>
```

### FilterPanel
```typescript
import { FilterPanel } from '@/components/news/FilterPanel';

<FilterPanel
  onFilterChange={(params) => console.log(params)}
  availablePublications={['NPR', 'BBC', 'NYT']}
  availableTags={['investigation', 'arrest']}
/>
```

### NewsStats
```typescript
import { NewsStats } from '@/components/news/NewsStats';

<NewsStats stats={newsStatsObject} />
```

## 📊 API Examples

### Basic Search
```typescript
const articles = await newsApi.searchNews({
  query: 'arrest',
  limit: 20
});
```

### Advanced Search
```typescript
const articles = await newsApi.searchNews({
  query: 'investigation',
  entity: 'Jeffrey Epstein',
  publication: 'NPR',
  min_credibility: 0.8,
  start_date: '2019-01-01',
  end_date: '2019-12-31',
  limit: 50
});
```

### Entity-Based Retrieval
```typescript
const articles = await newsApi.getArticlesByEntity('Prince Andrew', 10);
```

### Date Range Search
```typescript
const articles = await newsApi.getArticlesByDateRange(
  '2019-07-01',
  '2019-08-31',
  100
);
```

### Similar Articles
```typescript
const similar = await newsApi.getSimilarArticles('article-id-123', 5);
```

## 🐛 Troubleshooting

### Backend Not Running
**Error**: "Failed to fetch"
**Solution**: Ensure backend is running on port 8000

### No Articles Returned
**Error**: Empty results
**Solution**: Check backend has news data ingested

### Slow Performance
**Issue**: Search takes >3 seconds
**Solution**: Backend may need to index news articles in ChromaDB

### TypeScript Errors
**Issue**: Type errors in IDE
**Solution**: Run `npm run build` to verify types

## 🔍 Testing

### Manual Test Checklist
```bash
# 1. Test main page
✓ Navigate to /news
✓ Page loads without errors
✓ Search box works
✓ Filters apply

# 2. Test article detail
✓ Click article card
✓ Detail page loads
✓ Back button works
✓ External links work

# 3. Test entity integration
✓ Navigate to /entities/:name
✓ News Coverage section shows
✓ Articles display correctly
✓ "View All" button works
```

### Browser Testing
```bash
# Test in:
✓ Chrome/Edge (latest)
✓ Firefox (latest)
✓ Safari (latest)
✓ Mobile Safari (iOS)
✓ Chrome Mobile (Android)
```

## 📦 Build for Production

```bash
cd frontend
npm run build

# Output: dist/ directory
# Deploy dist/ to your hosting service
```

## 🚨 Common Pitfalls

### 1. Wrong API Base URL
**Issue**: API calls fail in production
**Fix**: Update `API_BASE_URL` in `frontend/src/services/newsApi.ts`

### 2. Missing Environment Variables
**Issue**: Backend endpoints not found
**Fix**: Ensure backend environment variables are set

### 3. CORS Issues
**Issue**: Browser blocks requests
**Fix**: Configure CORS in backend (already configured at http://localhost:5173)

## 🎯 Performance Tips

### 1. Limit Initial Load
```typescript
// Instead of:
const articles = await newsApi.searchNews({ limit: 1000 }); // Slow!

// Do this:
const articles = await newsApi.searchNews({ limit: 20 }); // Fast!
```

### 2. Debounce Search Input
Already implemented in FilterPanel (300ms delay)

### 3. Use Pagination
Already implemented (20 articles per page)

### 4. Lazy Load Statistics
Already implemented (toggle to show/hide)

## 📚 Further Reading

- **Full Documentation**: See `NEWS_FEATURE_COMPLETE.md`
- **API Reference**: See backend API documentation
- **Component Library**: ShadCN UI documentation
- **Icons**: Lucide React documentation

## 🆘 Need Help?

### Check These First
1. Is backend running?
2. Are news articles ingested?
3. Is ChromaDB initialized?
4. Console errors present?

### Debug Mode
```typescript
// In browser console:
localStorage.setItem('debug', 'newsApi');
// Then reload page
```

## ✅ Success Checklist

Before deploying:
- [ ] All pages load without errors
- [ ] Search returns results
- [ ] Filters work correctly
- [ ] Entity integration works
- [ ] Mobile responsive
- [ ] Build succeeds
- [ ] Backend endpoints configured
- [ ] CORS configured for production domain

---

**Ready to code?** Start exploring the news feature! 🎉
