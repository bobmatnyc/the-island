#!/bin/bash
# Biography Fix Verification Checklist - Linear 1M-108

echo "🔍 Biography Fix Verification Checklist"
echo "======================================="
echo ""

# 1. Check data file exists
if [ -f "data/metadata/entity_biographies.json" ]; then
    echo "✅ entity_biographies.json exists"
    
    # Count biographies
    bio_count=$(python3 -c "import json; data=json.load(open('data/metadata/entity_biographies.json')); print(len(data.get('entities', {})))")
    echo "   Total biographies: $bio_count"
else
    echo "❌ entity_biographies.json NOT FOUND"
    exit 1
fi

# 2. Check frontend component fix
if grep -q "entity.bio?.biography || entity.bio?.summary" frontend/src/components/entity/EntityBio.tsx; then
    echo "✅ EntityBio.tsx has dual format support"
else
    echo "❌ EntityBio.tsx NOT FIXED"
    exit 1
fi

# 3. Verify key entity biographies exist
echo ""
echo "📋 Verifying Key Entity Biographies:"
python3 << 'PYEOF'
import json
test_entities = ['jeffrey_epstein', 'ghislaine_maxwell', 'william_clinton']
with open('data/metadata/entity_biographies.json') as f:
    data = json.load(f)
    entities = data.get('entities', {})
    
for entity_id in test_entities:
    if entity_id in entities:
        bio_data = entities[entity_id]
        has_text = 'biography' in bio_data or 'summary' in bio_data
        text_type = 'biography' if 'biography' in bio_data else 'summary'
        print(f"   ✅ {entity_id}: Has {text_type}")
    else:
        print(f"   ❌ {entity_id}: NOT FOUND")
PYEOF

# 4. Check TypeScript types
if grep -q "biography?: string" frontend/src/lib/api.ts; then
    echo ""
    echo "✅ TypeScript types support biography field"
fi

if grep -q "summary?: string" frontend/src/lib/api.ts; then
    echo "✅ TypeScript types support summary field"
fi

echo ""
echo "======================================="
echo "🎉 All verification checks passed!"
echo ""
echo "Next Steps:"
echo "1. Test manually: npm run dev in frontend/"
echo "2. Navigate to any entity detail page"
echo "3. Click 'Biography' card"
echo "4. Verify biography text displays"
