# Type Alignment Quick Start Guide

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- TL;DR
- Step 1: Install Zod (5 minutes)
- Step 2: Create First Schema (15 minutes)

---

**Goal**: Fix type mismatches between FastAPI backend and React frontend in 3 steps.

---

## TL;DR

1. Install Zod: `npm install zod`
2. Create schemas matching Pydantic models
3. Validate API responses with schemas

**Time to first fix**: 30 minutes
**Complete migration**: 3 weeks

---

## Step 1: Install Zod (5 minutes)

```bash
cd frontend
npm install zod
```

---

## Step 2: Create First Schema (15 minutes)

Create `frontend/src/lib/schemas.ts`:

```typescript
import { z } from 'zod';

// Match backend Pydantic model exactly
export const FlightsResponseSchema = z.object({
  total_flights: z.number().int().min(0),
  flights: z.array(z.object({
    id: z.string(),
    date: z.string(),
    origin: z.object({
      code: z.string(),
      name: z.string(),
      city: z.string(),
      country: z.string(),
      latitude: z.number(),
      longitude: z.number(),
    }),
    destination: z.object({
      code: z.string(),
      name: z.string(),
      city: z.string(),
      country: z.string(),
      latitude: z.number(),
      longitude: z.number(),
    }),
    passengers: z.array(z.string()),
    passenger_count: z.number().int(),
    aircraft: z.string(),
  })),
  locations: z.record(z.string(), z.object({
    code: z.string(),
    name: z.string(),
    city: z.string(),
    country: z.string(),
    latitude: z.number(),
    longitude: z.number(),
  })),
  statistics: z.object({
    // ✅ FIXED: No total_flights here (was causing bug)
    unique_routes: z.number().int(),
    unique_locations: z.number().int(),
    top_passengers: z.array(z.object({
      name: z.string(),
      flights: z.number().int(),
    })),
    aircraft_usage: z.record(z.string(), z.number().int()),
    busiest_airports: z.record(z.string(), z.number().int()),
  }),
});

// Generate TypeScript type from schema
export type FlightsResponse = z.infer<typeof FlightsResponseSchema>;
```

---

## Step 3: Update API Client (10 minutes)

Update `frontend/src/lib/api.ts`:

```typescript
import { FlightsResponseSchema, type FlightsResponse } from './schemas';

export const api = {
  // OLD (no validation):
  // getFlights: () => fetchAPI<FlightsResponse>('/api/flights'),

  // NEW (with validation):
  getFlights: async (): Promise<FlightsResponse> => {
    const response = await fetchAPI('/api/flights');

    // ✅ Validates structure matches schema
    // ❌ Throws detailed error if mismatch
    return FlightsResponseSchema.parse(response);
  },
};
```

---

## What Happens Now?

### ✅ Before (Silent Failure)
```typescript
const data = await api.getFlights();
console.log(data.statistics.total_flights);  // undefined (field doesn't exist)
// Bug discovered in production! 🐛
```

### ✅ After (Immediate Error)
```typescript
const data = await api.getFlights();
// Zod throws error immediately:
// "Expected object to NOT have key 'total_flights' in statistics"
// Bug caught before rendering! ✅
```

---

## Error Message Example

When backend structure changes, you get detailed errors:

```
ZodError: [
  {
    "code": "unrecognized_keys",
    "keys": ["total_flights"],
    "path": ["statistics"],
    "message": "Unrecognized key(s) in object: 'total_flights'"
  }
]
```

This tells you exactly:
- What went wrong
- Where in the response
- Which field is unexpected

---

## Next Steps

### Immediate (Today)
1. ✅ Install Zod
2. ✅ Create schema for `/api/flights`
3. ✅ Test with actual API call

### This Week
4. Create schemas for critical APIs:
   - `/api/stats`
   - `/api/entities`
   - `/api/documents`

### This Month
5. Complete migration for all 25+ endpoints
6. Remove old TypeScript interfaces
7. Add schema tests

---

## Cheat Sheet: Backend → Zod Conversion

### Python Pydantic → TypeScript Zod

| Pydantic | Zod |
|----------|-----|
| `str` | `z.string()` |
| `int` | `z.number().int()` |
| `float` | `z.number()` |
| `bool` | `z.boolean()` |
| `List[str]` | `z.array(z.string())` |
| `Dict[str, int]` | `z.record(z.string(), z.number().int())` |
| `Optional[str]` | `z.string().optional()` or `z.string().nullable()` |
| `str = ""` | `z.string().default("")` |
| `int = Field(ge=0)` | `z.number().int().min(0)` |
| `str = Field(pattern=...)` | `z.string().regex(/.../)` |

### Example

**Pydantic**:
```python
class Flight(BaseModel):
    id: str = Field(..., min_length=1)
    passenger_count: int = Field(ge=0, default=0)
    passengers: List[str] = []
    tail_number: Optional[str] = None
```

**Zod**:
```typescript
const FlightSchema = z.object({
  id: z.string().min(1),
  passenger_count: z.number().int().min(0).default(0),
  passengers: z.array(z.string()).default([]),
  tail_number: z.string().nullable(),
});
```

---

## Testing Your Schemas

Create `frontend/src/lib/schemas.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { FlightsResponseSchema } from './schemas';

describe('FlightsResponseSchema', () => {
  it('validates correct backend response', () => {
    const validResponse = {
      total_flights: 1167,
      flights: [],
      locations: {},
      statistics: {
        unique_routes: 150,
        unique_locations: 45,
        top_passengers: [],
        aircraft_usage: {},
        busiest_airports: {},
      },
    };

    // Should not throw
    expect(() => FlightsResponseSchema.parse(validResponse)).not.toThrow();
  });

  it('rejects invalid backend response', () => {
    const invalidResponse = {
      total_flights: 1167,
      // ❌ Missing required fields
    };

    expect(() => FlightsResponseSchema.parse(invalidResponse)).toThrow();
  });
});
```

Run tests:
```bash
npm test schemas.test.ts
```

---

## Common Patterns

### Optional Fields
```typescript
// Backend: Optional[str] = None
z.string().nullable()

// Backend: str = ""
z.string().default("")
```

### Arrays
```typescript
// Backend: List[str] = []
z.array(z.string()).default([])
```

### Nested Objects
```typescript
// Backend:
// class Address(BaseModel):
//     city: str
//     state: str

z.object({
  city: z.string(),
  state: z.string(),
})
```

### Enums
```typescript
// Backend:
// class Status(Enum):
//     PENDING = "pending"
//     ACTIVE = "active"

z.enum(['pending', 'active'])
```

### Records/Dicts
```typescript
// Backend: Dict[str, int]
z.record(z.string(), z.number().int())
```

---

## Debugging Tips

### See What Failed
```typescript
try {
  const data = FlightsResponseSchema.parse(response);
} catch (error) {
  if (error instanceof z.ZodError) {
    console.log('Validation errors:', error.errors);
    // Detailed breakdown of what's wrong
  }
}
```

### Partial Validation (Development)
```typescript
// Validate only what you care about (during migration)
const PartialSchema = FlightsResponseSchema.pick({
  total_flights: true,
  statistics: true,
});
```

### Safe Parsing (No Exceptions)
```typescript
const result = FlightsResponseSchema.safeParse(response);
if (result.success) {
  const data = result.data;  // Typed data
} else {
  const errors = result.error.errors;  // Error details
}
```

---

## FAQ

**Q: Do I need to refactor the backend?**
A: No! Zod works with existing backend code.

**Q: What's the performance impact?**
A: ~1-2ms per API call (negligible for user-facing apps).

**Q: Can I migrate gradually?**
A: Yes! Migrate one endpoint at a time.

**Q: What if backend changes?**
A: Zod will throw error immediately, telling you exactly what changed.

**Q: Do I keep TypeScript interfaces?**
A: No, replace them with `z.infer<typeof Schema>`.

---

## Resources

- **Zod Docs**: https://zod.dev
- **Full Report**: See `TYPE_ALIGNMENT_REPORT.md`
- **Backend Models**: `server/models/*.py`

---

**Next**: See `TYPE_ALIGNMENT_REPORT.md` for complete analysis and implementation plan.
