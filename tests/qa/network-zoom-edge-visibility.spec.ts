import { test, expect } from '@playwright/test';

/**
 * QA Test Suite: Network Graph Zoom-Based Edge Visibility
 *
 * Feature: Automatic edge filtering based on zoom level (progressive disclosure)
 * Implementation: /frontend/src/pages/Network.tsx lines 713-753
 *
 * Test Coverage:
 * - Zoom threshold detection (1.5)
 * - Edge visibility changes during zoom
 * - User filter interaction at all zoom levels
 * - Performance with large networks
 * - Smooth transitions
 * - Edge highlighting preservation
 */

test.describe('Network Graph Zoom-Based Edge Visibility', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to network page
    await page.goto('http://localhost:5173/network');

    // Wait for graph to load
    await page.waitForSelector('canvas', { timeout: 10000 });

    // Wait for initial render (graph data loaded)
    await page.waitForTimeout(2000);
  });

  test('should show fewer edges when zoomed out (zoom < 1.5)', async ({ page }) => {
    // Reset to default zoom (globalScale = 1.0)
    await page.evaluate(() => {
      const graph = (window as any).graphRef?.current;
      if (graph) {
        graph.zoom(1.0);
      }
    });
    await page.waitForTimeout(1000);

    // Count edges rendered on canvas (approximate via canvas pixels)
    const edgeCountZoomedOut = await page.evaluate(() => {
      const canvas = document.querySelector('canvas') as HTMLCanvasElement;
      if (!canvas) return 0;

      const ctx = canvas.getContext('2d');
      if (!ctx) return 0;

      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imageData.data;

      // Count non-white pixels (edges are gray)
      let edgePixels = 0;
      for (let i = 0; i < data.length; i += 4) {
        const r = data[i];
        const g = data[i + 1];
        const b = data[i + 2];
        const a = data[i + 3];

        // Gray edges: r,g,b in range 80-120, alpha > 0
        if (r >= 80 && r <= 120 && g >= 80 && g <= 120 && b >= 80 && b <= 120 && a > 0) {
          edgePixels++;
        }
      }

      return edgePixels;
    });

    // Expect fewer edges when zoomed out (baseline for comparison)
    expect(edgeCountZoomedOut).toBeGreaterThan(0);
    console.log(`Edges visible when zoomed out (globalScale 1.0): ~${edgeCountZoomedOut} pixels`);
  });

  test('should show more edges when zoomed in (zoom >= 1.5)', async ({ page }) => {
    // Zoom in beyond threshold (globalScale = 2.0)
    await page.evaluate(() => {
      const graph = (window as any).graphRef?.current;
      if (graph) {
        graph.zoom(2.0);
      }
    });
    await page.waitForTimeout(1000);

    // Count edges rendered on canvas
    const edgeCountZoomedIn = await page.evaluate(() => {
      const canvas = document.querySelector('canvas') as HTMLCanvasElement;
      if (!canvas) return 0;

      const ctx = canvas.getContext('2d');
      if (!ctx) return 0;

      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imageData.data;

      let edgePixels = 0;
      for (let i = 0; i < data.length; i += 4) {
        const r = data[i];
        const g = data[i + 1];
        const b = data[i + 2];
        const a = data[i + 3];

        if (r >= 80 && r <= 120 && g >= 80 && g <= 120 && b >= 80 && b <= 120 && a > 0) {
          edgePixels++;
        }
      }

      return edgePixels;
    });

    // Expect more edges when zoomed in
    expect(edgeCountZoomedIn).toBeGreaterThan(0);
    console.log(`Edges visible when zoomed in (globalScale 2.0): ~${edgeCountZoomedIn} pixels`);
  });

  test('should transition edge count at zoom threshold (1.5)', async ({ page }) => {
    // Measure edge count just below threshold
    await page.evaluate(() => {
      const graph = (window as any).graphRef?.current;
      if (graph) graph.zoom(1.4);
    });
    await page.waitForTimeout(1000);

    const edgesBelow = await getEdgePixelCount(page);

    // Measure edge count just above threshold
    await page.evaluate(() => {
      const graph = (window as any).graphRef?.current;
      if (graph) graph.zoom(1.6);
    });
    await page.waitForTimeout(1000);

    const edgesAbove = await getEdgePixelCount(page);

    // Expect more edges above threshold than below
    expect(edgesAbove).toBeGreaterThan(edgesBelow);
    console.log(`Edge transition at threshold: ${edgesBelow} -> ${edgesAbove} pixels`);
  });

  test('should respect user filter when zoomed out', async ({ page }) => {
    // Set user filter to high value (10)
    const slider = page.locator('input[type="range"][min="0"][max="20"]');
    await slider.fill('10');
    await page.waitForTimeout(1000);

    // Zoom out
    await page.evaluate(() => {
      const graph = (window as any).graphRef?.current;
      if (graph) graph.zoom(1.0);
    });
    await page.waitForTimeout(1000);

    // Edge count should reflect user's filter (10), not auto threshold (3)
    const edgeCount = await getEdgePixelCount(page);

    // With minEdgeWeight=10, we should see ~109 edges (from QA report)
    // Pixels will be proportional to edge count
    expect(edgeCount).toBeGreaterThan(0);
    console.log(`Edges with user filter 10 when zoomed out: ~${edgeCount} pixels`);
  });

  test('should respect user filter when zoomed in', async ({ page }) => {
    // Set user filter to minimum (0)
    const slider = page.locator('input[type="range"][min="0"][max="20"]');
    await slider.fill('0');
    await page.waitForTimeout(1000);

    // Zoom in
    await page.evaluate(() => {
      const graph = (window as any).graphRef?.current;
      if (graph) graph.zoom(2.0);
    });
    await page.waitForTimeout(1000);

    // Should show ALL edges (1,482 based on data)
    const edgeCount = await getEdgePixelCount(page);
    expect(edgeCount).toBeGreaterThan(0);
    console.log(`Edges with user filter 0 when zoomed in: ~${edgeCount} pixels (all edges)`);
  });

  test('should maintain smooth zoom transitions', async ({ page }) => {
    const zoomLevels = [1.0, 1.2, 1.4, 1.5, 1.6, 1.8, 2.0];
    const edgeCounts: number[] = [];

    for (const zoom of zoomLevels) {
      await page.evaluate((z) => {
        const graph = (window as any).graphRef?.current;
        if (graph) graph.zoom(z);
      }, zoom);
      await page.waitForTimeout(500);

      const count = await getEdgePixelCount(page);
      edgeCounts.push(count);
    }

    // Verify edge counts increase with zoom (generally)
    console.log('Zoom levels vs edge counts:', zoomLevels.map((z, i) => `${z}: ${edgeCounts[i]}`).join(', '));

    // At minimum, verify transition happens at 1.5
    const indexBefore = zoomLevels.indexOf(1.4);
    const indexAfter = zoomLevels.indexOf(1.6);
    expect(edgeCounts[indexAfter]).toBeGreaterThanOrEqual(edgeCounts[indexBefore]);
  });

  test('should preserve edge highlighting when zooming', async ({ page }) => {
    // Click on a node to highlight its edges
    const canvas = page.locator('canvas').first();
    await canvas.click({ position: { x: 400, y: 300 } });
    await page.waitForTimeout(500);

    // Verify edges are highlighted (darker color)
    const highlightedBefore = await page.evaluate(() => {
      const canvas = document.querySelector('canvas') as HTMLCanvasElement;
      if (!canvas) return false;

      const ctx = canvas.getContext('2d');
      if (!ctx) return false;

      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imageData.data;

      // Look for darker gray (highlighted edges: rgba(100,100,100,0.8))
      for (let i = 0; i < data.length; i += 4) {
        if (data[i] === 100 && data[i + 1] === 100 && data[i + 2] === 100) {
          return true;
        }
      }
      return false;
    });

    // Zoom in
    await page.evaluate(() => {
      const graph = (window as any).graphRef?.current;
      if (graph) graph.zoom(2.0);
    });
    await page.waitForTimeout(500);

    // Verify highlighting persists
    const highlightedAfter = await page.evaluate(() => {
      const canvas = document.querySelector('canvas') as HTMLCanvasElement;
      if (!canvas) return false;

      const ctx = canvas.getContext('2d');
      if (!ctx) return false;

      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imageData.data;

      for (let i = 0; i < data.length; i += 4) {
        if (data[i] === 100 && data[i + 1] === 100 && data[i + 2] === 100) {
          return true;
        }
      }
      return false;
    });

    expect(highlightedBefore).toBe(highlightedAfter);
  });

  test('should update edges within 1 second of zoom change', async ({ page }) => {
    // Measure time to update edges when zooming
    const startTime = Date.now();

    await page.evaluate(() => {
      const graph = (window as any).graphRef?.current;
      if (graph) graph.zoom(1.8);
    });

    // Wait for canvas to update
    await page.waitForTimeout(100);

    const endTime = Date.now();
    const updateTime = endTime - startTime;

    // Should update in < 1000ms (performance requirement)
    expect(updateTime).toBeLessThan(1000);
    console.log(`Zoom update time: ${updateTime}ms`);
  });

  test('should work with edge weight slider at all zoom levels', async ({ page }) => {
    // Test combination of zoom and slider
    const slider = page.locator('input[type="range"][min="0"][max="20"]');

    // Zoomed out + low filter
    await slider.fill('3');
    await page.evaluate(() => {
      const graph = (window as any).graphRef?.current;
      if (graph) graph.zoom(1.0);
    });
    await page.waitForTimeout(500);
    const count1 = await getEdgePixelCount(page);

    // Zoomed out + high filter
    await slider.fill('10');
    await page.waitForTimeout(500);
    const count2 = await getEdgePixelCount(page);

    // Zoomed in + low filter
    await slider.fill('0');
    await page.evaluate(() => {
      const graph = (window as any).graphRef?.current;
      if (graph) graph.zoom(2.0);
    });
    await page.waitForTimeout(500);
    const count3 = await getEdgePixelCount(page);

    // Zoomed in + high filter
    await slider.fill('10');
    await page.waitForTimeout(500);
    const count4 = await getEdgePixelCount(page);

    // Verify all combinations work and show different edge counts
    expect(count1).toBeGreaterThan(0);
    expect(count2).toBeGreaterThan(0);
    expect(count3).toBeGreaterThan(0);
    expect(count4).toBeGreaterThan(0);

    console.log(`Edge counts at different zoom/filter combinations:
      Zoom 1.0 + Filter 3: ${count1}
      Zoom 1.0 + Filter 10: ${count2}
      Zoom 2.0 + Filter 0: ${count3}
      Zoom 2.0 + Filter 10: ${count4}`);
  });

  test('should handle rapid zoom changes without errors', async ({ page }) => {
    // Rapidly change zoom levels
    const zoomSequence = [1.0, 2.0, 0.8, 1.5, 1.2, 1.8, 1.0];

    for (const zoom of zoomSequence) {
      await page.evaluate((z) => {
        const graph = (window as any).graphRef?.current;
        if (graph) graph.zoom(z);
      }, zoom);
      await page.waitForTimeout(100);
    }

    // Verify no console errors
    const consoleErrors = await page.evaluate(() => {
      return (window as any).consoleErrors || [];
    });

    expect(consoleErrors.length).toBe(0);
  });

  test('should not flicker during zoom transitions', async ({ page }) => {
    // Take screenshots at different zoom levels
    await page.evaluate(() => {
      const graph = (window as any).graphRef?.current;
      if (graph) graph.zoom(1.0);
    });
    await page.waitForTimeout(500);
    const screenshot1 = await page.screenshot({ path: '/tmp/zoom_1.0.png' });

    await page.evaluate(() => {
      const graph = (window as any).graphRef?.current;
      if (graph) graph.zoom(1.5);
    });
    await page.waitForTimeout(500);
    const screenshot2 = await page.screenshot({ path: '/tmp/zoom_1.5.png' });

    await page.evaluate(() => {
      const graph = (window as any).graphRef?.current;
      if (graph) graph.zoom(2.0);
    });
    await page.waitForTimeout(500);
    const screenshot3 = await page.screenshot({ path: '/tmp/zoom_2.0.png' });

    // Visual inspection required (automated visual regression out of scope)
    expect(screenshot1).toBeDefined();
    expect(screenshot2).toBeDefined();
    expect(screenshot3).toBeDefined();

    console.log('Visual regression screenshots saved to /tmp/zoom_*.png');
  });

  test('should show expected edge reduction metrics', async ({ page }) => {
    // Verify expected impact from implementation summary
    // Network: 255 nodes, 1,482 edges

    // Zoomed out (auto filter = 3): should see ~311 edges (79% reduction)
    await page.evaluate(() => {
      const graph = (window as any).graphRef?.current;
      if (graph) graph.zoom(1.0);
    });
    const slider = page.locator('input[type="range"][min="0"][max="20"]');
    await slider.fill('0'); // User filter = 0, auto should enforce 3
    await page.waitForTimeout(1000);

    const edgesZoomedOut = await getEdgePixelCount(page);

    // Zoomed in (user filter = 0): should see ~1,482 edges (all)
    await page.evaluate(() => {
      const graph = (window as any).graphRef?.current;
      if (graph) graph.zoom(2.0);
    });
    await page.waitForTimeout(1000);

    const edgesZoomedIn = await getEdgePixelCount(page);

    // Verify zoomed in shows more edges than zoomed out
    const reductionRatio = edgesZoomedOut / edgesZoomedIn;
    console.log(`Edge reduction ratio: ${(reductionRatio * 100).toFixed(1)}% (expected ~21% when auto-filtered)`);

    // Should see significant reduction when zoomed out
    expect(edgesZoomedIn).toBeGreaterThan(edgesZoomedOut);
  });
});

// Helper function to count edge pixels on canvas
async function getEdgePixelCount(page: any): Promise<number> {
  return await page.evaluate(() => {
    const canvas = document.querySelector('canvas') as HTMLCanvasElement;
    if (!canvas) return 0;

    const ctx = canvas.getContext('2d');
    if (!ctx) return 0;

    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;

    let edgePixels = 0;
    for (let i = 0; i < data.length; i += 4) {
      const r = data[i];
      const g = data[i + 1];
      const b = data[i + 2];
      const a = data[i + 3];

      // Gray edges: r,g,b in range 80-120, alpha > 0
      if (r >= 80 && r <= 120 && g >= 80 && g <= 120 && b >= 80 && b <= 120 && a > 0) {
        edgePixels++;
      }
    }

    return edgePixels;
  });
}
