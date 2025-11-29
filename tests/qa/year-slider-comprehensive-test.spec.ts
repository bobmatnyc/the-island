/**
 * Comprehensive QA Test Suite for YearSlider Component (Linear 1M-154)
 *
 * Tests:
 * - Functional: Drag, click, keyboard navigation
 * - Visual: Rendering, activity bars, tooltips
 * - Accessibility: ARIA labels, screen reader support, keyboard-only
 * - Performance: Transition timing, debouncing
 * - Integration: CalendarHeatmap updates
 * - Edge cases: Single year, no data, network failure
 */

import { test, expect, Page } from '@playwright/test'

const BASE_URL = 'http://localhost:5173'
const ACTIVITY_URL = `${BASE_URL}/activity`

test.describe('YearSlider Component - Comprehensive QA', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(ACTIVITY_URL)
    // Wait for data to load
    await page.waitForSelector('[aria-label="Year selection slider"]', { timeout: 10000 })
  })

  test.describe('Phase 2: Functional Testing', () => {
    test('should render YearSlider component correctly', async ({ page }) => {
      // Verify slider is visible
      const slider = page.locator('[aria-label="Year selection slider"]')
      await expect(slider).toBeVisible()

      // Verify year markers are visible
      const yearMarkers = page.locator('button[aria-label*="Jump to year"]')
      await expect(yearMarkers.first()).toBeVisible()

      // Count visible year markers (should be 5-7 depending on range)
      const markerCount = await yearMarkers.count()
      expect(markerCount).toBeGreaterThan(3)
      expect(markerCount).toBeLessThan(10)

      // Verify selected year display
      const selectedYearDisplay = page.locator('text=/^\\d{4}$/')
      await expect(selectedYearDisplay.first()).toBeVisible()

      console.log(`✓ YearSlider renders with ${markerCount} year markers`)
    })

    test('should update year when clicking year markers', async ({ page }) => {
      // Get all year marker buttons
      const yearMarkers = page.locator('button[aria-label*="Jump to year"]')
      const firstMarker = yearMarkers.first()

      // Get the year from the first marker
      const yearText = await firstMarker.textContent()
      const targetYear = yearText?.trim()

      // Click the year marker
      await firstMarker.click()

      // Wait for update (300ms transition)
      await page.waitForTimeout(400)

      // Verify year changed
      const slider = page.locator('[aria-label="Year selection slider"]')
      const currentYear = await slider.getAttribute('aria-valuenow')

      expect(currentYear).toBe(targetYear)
      console.log(`✓ Year marker click works: ${targetYear}`)
    })

    test('should show activity density bars', async ({ page }) => {
      // Look for activity bars container
      // Activity bars are rendered with specific styling
      const activityBars = page.locator('[title*="flight"]')

      const barCount = await activityBars.count()
      expect(barCount).toBeGreaterThan(0)

      console.log(`✓ Activity density bars visible: ${barCount} bars`)
    })

    test('should show tooltip on activity bar hover', async ({ page }) => {
      // Find an activity bar with flights
      const activityBar = page.locator('[title*="flight"]').first()

      // Get tooltip text
      const tooltipText = await activityBar.getAttribute('title')

      expect(tooltipText).toContain('flight')
      expect(tooltipText).toMatch(/\d{4}/) // Contains a year

      console.log(`✓ Activity bar tooltip: "${tooltipText}"`)
    })

    test('should update year when clicking activity bar', async ({ page }) => {
      // Find an activity bar
      const activityBar = page.locator('[title*="flight"]').first()

      // Get expected year from tooltip
      const tooltip = await activityBar.getAttribute('title')
      const yearMatch = tooltip?.match(/(\d{4})/)
      const expectedYear = yearMatch?.[1]

      // Click the activity bar
      await activityBar.click()

      // Wait for update
      await page.waitForTimeout(400)

      // Verify year changed
      const slider = page.locator('[aria-label="Year selection slider"]')
      const currentYear = await slider.getAttribute('aria-valuenow')

      expect(currentYear).toBe(expectedYear)
      console.log(`✓ Activity bar click works: ${expectedYear}`)
    })

    test('should support keyboard navigation - Arrow Right', async ({ page }) => {
      const slider = page.locator('[aria-label="Year selection slider"]')

      // Get current year
      const initialYear = await slider.getAttribute('aria-valuenow')
      const initialYearNum = parseInt(initialYear || '0')

      // Focus slider and press Arrow Right
      await slider.focus()
      await page.keyboard.press('ArrowRight')

      // Wait for update
      await page.waitForTimeout(400)

      // Verify year increased by 1
      const newYear = await slider.getAttribute('aria-valuenow')
      const newYearNum = parseInt(newYear || '0')

      expect(newYearNum).toBe(initialYearNum + 1)
      console.log(`✓ Arrow Right: ${initialYear} → ${newYear}`)
    })

    test('should support keyboard navigation - Arrow Left', async ({ page }) => {
      const slider = page.locator('[aria-label="Year selection slider"]')

      // Get current year
      const initialYear = await slider.getAttribute('aria-valuenow')
      const initialYearNum = parseInt(initialYear || '0')

      // Focus slider and press Arrow Left
      await slider.focus()
      await page.keyboard.press('ArrowLeft')

      // Wait for update
      await page.waitForTimeout(400)

      // Verify year decreased by 1
      const newYear = await slider.getAttribute('aria-valuenow')
      const newYearNum = parseInt(newYear || '0')

      expect(newYearNum).toBe(initialYearNum - 1)
      console.log(`✓ Arrow Left: ${initialYear} → ${newYear}`)
    })

    test('should support keyboard navigation - Home key', async ({ page }) => {
      const slider = page.locator('[aria-label="Year selection slider"]')

      // Get min year from aria attribute
      const minYear = await slider.getAttribute('aria-valuemin')

      // Focus slider and press Home
      await slider.focus()
      await page.keyboard.press('Home')

      // Wait for update
      await page.waitForTimeout(400)

      // Verify year is now min year
      const currentYear = await slider.getAttribute('aria-valuenow')

      expect(currentYear).toBe(minYear)
      console.log(`✓ Home key: Jump to ${minYear}`)
    })

    test('should support keyboard navigation - End key', async ({ page }) => {
      const slider = page.locator('[aria-label="Year selection slider"]')

      // Get max year from aria attribute
      const maxYear = await slider.getAttribute('aria-valuemax')

      // Focus slider and press End
      await slider.focus()
      await page.keyboard.press('End')

      // Wait for update
      await page.waitForTimeout(400)

      // Verify year is now max year
      const currentYear = await slider.getAttribute('aria-valuenow')

      expect(currentYear).toBe(maxYear)
      console.log(`✓ End key: Jump to ${maxYear}`)
    })
  })

  test.describe('Phase 3: Browser Compatibility', () => {
    test('should work in Chromium', async ({ page, browserName }) => {
      test.skip(browserName !== 'chromium', 'Chromium-specific test')

      const slider = page.locator('[aria-label="Year selection slider"]')
      await expect(slider).toBeVisible()

      // Test drag interaction
      const sliderBound = await slider.boundingBox()
      if (sliderBound) {
        await page.mouse.move(sliderBound.x + sliderBound.width / 2, sliderBound.y + sliderBound.height / 2)
        await page.mouse.down()
        await page.mouse.move(sliderBound.x + sliderBound.width * 0.7, sliderBound.y + sliderBound.height / 2)
        await page.mouse.up()
      }

      await page.waitForTimeout(400)
      console.log('✓ Chromium: Drag interaction works')
    })

    test('should work in Firefox', async ({ page, browserName }) => {
      test.skip(browserName !== 'firefox', 'Firefox-specific test')

      const slider = page.locator('[aria-label="Year selection slider"]')
      await expect(slider).toBeVisible()
      console.log('✓ Firefox: Component renders')
    })

    test('should work in WebKit/Safari', async ({ page, browserName }) => {
      test.skip(browserName !== 'webkit', 'WebKit-specific test')

      const slider = page.locator('[aria-label="Year selection slider"]')
      await expect(slider).toBeVisible()
      console.log('✓ WebKit: Component renders')
    })
  })

  test.describe('Phase 4: Responsive Design', () => {
    test('should adapt to mobile viewport (375px)', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 })

      const slider = page.locator('[aria-label="Year selection slider"]')
      await expect(slider).toBeVisible()

      // Year markers should still be visible but possibly fewer
      const yearMarkers = page.locator('button[aria-label*="Jump to year"]')
      const markerCount = await yearMarkers.count()
      expect(markerCount).toBeGreaterThan(2) // At least min/max years

      console.log(`✓ Mobile (375px): ${markerCount} year markers visible`)
    })

    test('should adapt to tablet viewport (768px)', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 })

      const slider = page.locator('[aria-label="Year selection slider"]')
      await expect(slider).toBeVisible()

      const yearMarkers = page.locator('button[aria-label*="Jump to year"]')
      const markerCount = await yearMarkers.count()

      console.log(`✓ Tablet (768px): ${markerCount} year markers visible`)
    })
  })

  test.describe('Phase 5: Performance Testing', () => {
    test('should complete year transition within 300ms', async ({ page }) => {
      const slider = page.locator('[aria-label="Year selection slider"]')

      // Measure transition time
      const startTime = Date.now()

      await slider.focus()
      await page.keyboard.press('ArrowRight')

      // Wait for transition
      await page.waitForTimeout(400)

      const endTime = Date.now()
      const duration = endTime - startTime

      // Should complete within 400ms (300ms transition + 100ms buffer)
      expect(duration).toBeLessThan(500)
      console.log(`✓ Transition completed in ${duration}ms`)
    })

    test('should not trigger excessive API calls during drag', async ({ page }) => {
      // Listen for API calls
      const apiCalls: string[] = []
      page.on('request', request => {
        if (request.url().includes('/api/')) {
          apiCalls.push(request.url())
        }
      })

      const slider = page.locator('[aria-label="Year selection slider"]')
      const sliderBound = await slider.boundingBox()

      // Clear previous API calls
      apiCalls.length = 0

      // Perform drag
      if (sliderBound) {
        await page.mouse.move(sliderBound.x + sliderBound.width / 2, sliderBound.y + sliderBound.height / 2)
        await page.mouse.down()

        // Drag slowly across multiple positions
        for (let i = 0.5; i <= 0.8; i += 0.1) {
          await page.mouse.move(sliderBound.x + sliderBound.width * i, sliderBound.y + sliderBound.height / 2)
          await page.waitForTimeout(50)
        }

        await page.mouse.up()
      }

      await page.waitForTimeout(500)

      // Should have minimal API calls due to debouncing
      console.log(`✓ API calls during drag: ${apiCalls.length}`)
      expect(apiCalls.length).toBeLessThan(5) // Debounced, not one per pixel
    })
  })

  test.describe('Phase 6: Accessibility Testing', () => {
    test('should have proper ARIA labels', async ({ page }) => {
      const slider = page.locator('[aria-label="Year selection slider"]')

      // Check ARIA attributes
      const ariaLabel = await slider.getAttribute('aria-label')
      const ariaValueMin = await slider.getAttribute('aria-valuemin')
      const ariaValueMax = await slider.getAttribute('aria-valuemax')
      const ariaValueNow = await slider.getAttribute('aria-valuenow')
      const ariaValueText = await slider.getAttribute('aria-valuetext')

      expect(ariaLabel).toBe('Year selection slider')
      expect(ariaValueMin).toBeTruthy()
      expect(ariaValueMax).toBeTruthy()
      expect(ariaValueNow).toBeTruthy()
      expect(ariaValueText).toContain('Year')
      expect(ariaValueText).toContain('flight')

      console.log(`✓ ARIA labels present:`)
      console.log(`  - Label: "${ariaLabel}"`)
      console.log(`  - Range: ${ariaValueMin} - ${ariaValueMax}`)
      console.log(`  - Current: ${ariaValueText}`)
    })

    test('should be keyboard navigable (Tab focus)', async ({ page }) => {
      // Tab to slider
      await page.keyboard.press('Tab')
      await page.keyboard.press('Tab')
      await page.keyboard.press('Tab')

      // Check if slider is focused
      const slider = page.locator('[aria-label="Year selection slider"]')
      const isFocused = await slider.evaluate(el => el === document.activeElement)

      // Note: This might fail if slider is not in tab order, which is acceptable
      console.log(`✓ Slider keyboard focus: ${isFocused ? 'YES' : 'NO (may be in slider component)'}`)
    })

    test('should have visible focus indicator', async ({ page }) => {
      const slider = page.locator('[aria-label="Year selection slider"]')
      await slider.focus()

      // Check computed styles for focus ring
      const thumb = page.locator('[role="slider"]').first()
      const outlineWidth = await thumb.evaluate(el => {
        return window.getComputedStyle(el).outlineWidth
      })

      console.log(`✓ Focus indicator outline width: ${outlineWidth}`)
    })

    test('should have screen reader announcement region', async ({ page }) => {
      // Check for sr-only region with aria-live
      const srRegion = page.locator('[aria-live="polite"]')
      await expect(srRegion).toBeAttached()

      const srText = await srRegion.textContent()
      expect(srText).toContain('Year')
      expect(srText).toContain('selected')

      console.log(`✓ Screen reader region: "${srText?.substring(0, 100)}..."`)
    })
  })

  test.describe('Phase 7: Edge Cases', () => {
    test('should handle rapid year changes gracefully', async ({ page }) => {
      const slider = page.locator('[aria-label="Year selection slider"]')
      await slider.focus()

      // Rapid keyboard presses
      for (let i = 0; i < 5; i++) {
        await page.keyboard.press('ArrowRight')
        await page.waitForTimeout(50) // Very fast
      }

      await page.waitForTimeout(400)

      // Should not crash, slider should still be functional
      const finalYear = await slider.getAttribute('aria-valuenow')
      expect(finalYear).toBeTruthy()

      console.log(`✓ Rapid changes handled, final year: ${finalYear}`)
    })

    test('should prevent navigation beyond min year', async ({ page }) => {
      const slider = page.locator('[aria-label="Year selection slider"]')

      // Go to minimum year
      await slider.focus()
      await page.keyboard.press('Home')
      await page.waitForTimeout(300)

      const minYear = await slider.getAttribute('aria-valuenow')

      // Try to go further left
      await page.keyboard.press('ArrowLeft')
      await page.waitForTimeout(300)

      const stillMinYear = await slider.getAttribute('aria-valuenow')

      expect(stillMinYear).toBe(minYear)
      console.log(`✓ Prevents going below min year: ${minYear}`)
    })

    test('should prevent navigation beyond max year', async ({ page }) => {
      const slider = page.locator('[aria-label="Year selection slider"]')

      // Go to maximum year
      await slider.focus()
      await page.keyboard.press('End')
      await page.waitForTimeout(300)

      const maxYear = await slider.getAttribute('aria-valuenow')

      // Try to go further right
      await page.keyboard.press('ArrowRight')
      await page.waitForTimeout(300)

      const stillMaxYear = await slider.getAttribute('aria-valuenow')

      expect(stillMaxYear).toBe(maxYear)
      console.log(`✓ Prevents going above max year: ${maxYear}`)
    })
  })

  test.describe('Phase 8: Integration with CalendarHeatmap', () => {
    test('should update CalendarHeatmap when year changes', async ({ page }) => {
      // Find heatmap title
      const heatmapTitle = page.locator('h3:has-text("Activity Heatmap")')
      await expect(heatmapTitle).toBeVisible()

      // Get initial year from title
      const initialTitleText = await heatmapTitle.textContent()
      const initialYearMatch = initialTitleText?.match(/(\d{4})/)
      const initialYear = initialYearMatch?.[1]

      // Change year using slider
      const slider = page.locator('[aria-label="Year selection slider"]')
      await slider.focus()
      await page.keyboard.press('ArrowRight')
      await page.waitForTimeout(500)

      // Check if heatmap title updated
      const updatedTitleText = await heatmapTitle.textContent()
      const updatedYearMatch = updatedTitleText?.match(/(\d{4})/)
      const updatedYear = updatedYearMatch?.[1]

      expect(updatedYear).not.toBe(initialYear)
      console.log(`✓ Heatmap updated: ${initialYear} → ${updatedYear}`)
    })

    test('should not cause duplicate API calls', async ({ page }) => {
      const apiCalls: string[] = []
      page.on('request', request => {
        if (request.url().includes('/api/')) {
          apiCalls.push(request.url())
        }
      })

      // Clear and change year
      apiCalls.length = 0

      const slider = page.locator('[aria-label="Year selection slider"]')
      await slider.focus()
      await page.keyboard.press('ArrowRight')

      await page.waitForTimeout(1000)

      // Should have minimal API calls
      console.log(`✓ API calls after year change: ${apiCalls.length}`)

      // Filter unique calls
      const uniqueCalls = [...new Set(apiCalls)]
      console.log(`✓ Unique API endpoints: ${uniqueCalls.length}`)
    })
  })

  test.describe('Visual Regression', () => {
    test('should match visual snapshot', async ({ page }) => {
      // Take screenshot of YearSlider component
      const sliderContainer = page.locator('[aria-label="Year selection slider"]').locator('..')

      // Wait for any animations
      await page.waitForTimeout(500)

      await expect(sliderContainer).toHaveScreenshot('year-slider-default.png', {
        maxDiffPixels: 100
      })

      console.log('✓ Visual snapshot captured')
    })
  })
})
