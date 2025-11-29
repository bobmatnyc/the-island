-- Safari Automation Script for Entity Detail Page Testing
-- Tests navigation cards, bio toggle, and deep linking

on run argv
    set baseURL to "http://localhost:5173"
    set entityName to "Maxwell, Ghislaine"

    tell application "Safari"
        activate

        -- Close existing windows and start fresh
        if (count of windows) > 0 then
            close every window
        end if
        delay 0.5

        -- Create new window and navigate to entity detail page
        make new document
        set URL of document 1 to baseURL & "/entities/" & my urlEncode(entityName)
        delay 3

        -- Wait for page to load
        repeat 10 times
            if (do JavaScript "document.readyState" in document 1) is "complete" then
                exit repeat
            end if
            delay 0.5
        end repeat

        delay 2

        -- Test 1: Check if navigation cards are visible
        set cardCount to do JavaScript "document.querySelectorAll('[class*=\"cursor-pointer\"][class*=\"hover:border-primary\"]').length" in document 1
        log "TEST 1: Navigation cards found: " & cardCount

        -- Test 2: Check if counts are displayed
        set bioCardText to do JavaScript "Array.from(document.querySelectorAll('.font-semibold.text-lg')).find(el => el.textContent === 'Bio') ? 'PASS' : 'FAIL'" in document 1
        log "TEST 2: Bio card visible: " & bioCardText

        set docsCardText to do JavaScript "Array.from(document.querySelectorAll('.font-semibold.text-lg')).find(el => el.textContent === 'Docs')?.parentElement?.parentElement?.textContent || 'NOT FOUND'" in document 1
        log "TEST 2: Docs card content: " & docsCardText

        set flightsCardText to do JavaScript "Array.from(document.querySelectorAll('.font-semibold.text-lg')).find(el => el.textContent === 'Flights')?.parentElement?.parentElement?.textContent || 'NOT FOUND'" in document 1
        log "TEST 2: Flights card content: " & flightsCardText

        set networkCardText to do JavaScript "Array.from(document.querySelectorAll('.font-semibold.text-lg')).find(el => el.textContent === 'Network')?.parentElement?.parentElement?.textContent || 'NOT FOUND'" in document 1
        log "TEST 2: Network card content: " & networkCardText

        delay 1

        -- Test 3: Click Bio card and verify expanded view
        do JavaScript "Array.from(document.querySelectorAll('.font-semibold.text-lg')).find(el => el.textContent === 'Bio')?.closest('[class*=\"cursor-pointer\"]')?.click()" in document 1
        delay 2

        set bioExpanded to do JavaScript "document.querySelector('h3')?.textContent?.includes('Biography') ? 'PASS' : 'FAIL'" in document 1
        log "TEST 3: Bio expanded view: " & bioExpanded

        set backButton to do JavaScript "Array.from(document.querySelectorAll('button')).find(el => el.textContent.includes('Back')) ? 'PASS' : 'FAIL'" in document 1
        log "TEST 3: Back button present: " & backButton

        delay 1

        -- Test 4: Click back button
        do JavaScript "Array.from(document.querySelectorAll('button')).find(el => el.textContent.includes('Back'))?.click()" in document 1
        delay 1

        set backToLinks to do JavaScript "Array.from(document.querySelectorAll('.font-semibold.text-lg')).some(el => ['Bio', 'Docs', 'Flights', 'Network'].includes(el.textContent)) ? 'PASS' : 'FAIL'" in document 1
        log "TEST 4: Back to links view: " & backToLinks

        delay 1

        -- Test 5: Click Docs card and verify navigation
        do JavaScript "Array.from(document.querySelectorAll('.font-semibold.text-lg')).find(el => el.textContent === 'Docs')?.closest('[class*=\"cursor-pointer\"]')?.click()" in document 1
        delay 3

        set currentURL to URL of document 1
        log "TEST 5: Navigated to: " & currentURL

        set hasEntityParam to do JavaScript "window.location.search.includes('entity=') ? 'PASS' : 'FAIL'" in document 1
        log "TEST 5: Entity parameter in URL: " & hasEntityParam

        delay 1

        -- Navigate back to entity detail for next test
        set URL of document 1 to baseURL & "/entities/" & my urlEncode(entityName)
        delay 3

        -- Test 6: Click Flights card and verify navigation
        do JavaScript "Array.from(document.querySelectorAll('.font-semibold.text-lg')).find(el => el.textContent === 'Flights')?.closest('[class*=\"cursor-pointer\"]')?.click()" in document 1
        delay 3

        set currentURL to URL of document 1
        log "TEST 6: Navigated to: " & currentURL

        set hasPassengerParam to do JavaScript "window.location.search.includes('passenger=') ? 'PASS' : 'FAIL'" in document 1
        log "TEST 6: Passenger parameter in URL: " & hasPassengerParam

        delay 1

        -- Navigate back to entity detail for next test
        set URL of document 1 to baseURL & "/entities/" & my urlEncode(entityName)
        delay 3

        -- Test 7: Click Network card and verify navigation
        do JavaScript "Array.from(document.querySelectorAll('.font-semibold.text-lg')).find(el => el.textContent === 'Network')?.closest('[class*=\"cursor-pointer\"]')?.click()" in document 1
        delay 3

        set currentURL to URL of document 1
        log "TEST 7: Navigated to: " & currentURL

        set hasFocusParam to do JavaScript "window.location.search.includes('focus=') ? 'PASS' : 'FAIL'" in document 1
        log "TEST 7: Focus parameter in URL: " & hasFocusParam

        -- Take screenshot for documentation
        log "Tests completed. Check console for results."

    end tell
end run

-- URL encoding helper
on urlEncode(inputString)
    set outputString to ""
    repeat with currentChar in characters of inputString
        set charID to id of currentChar
        if (charID ≥ 48 and charID ≤ 57) or (charID ≥ 65 and charID ≤ 90) or (charID ≥ 97 and charID ≤ 122) or currentChar is in "-_.~" then
            set outputString to outputString & currentChar
        else if currentChar is " " then
            set outputString to outputString & "%20"
        else if currentChar is "," then
            set outputString to outputString & "%2C"
        else
            set outputString to outputString & "%" & my decimalToHex(charID)
        end if
    end repeat
    return outputString
end urlEncode

on decimalToHex(decimalNumber)
    set hexChars to "0123456789ABCDEF"
    set hexString to ""
    repeat while decimalNumber > 0
        set remainder to decimalNumber mod 16
        set hexString to (character (remainder + 1) of hexChars) & hexString
        set decimalNumber to decimalNumber div 16
    end repeat
    if length of hexString is 1 then set hexString to "0" & hexString
    return hexString
end decimalToHex
