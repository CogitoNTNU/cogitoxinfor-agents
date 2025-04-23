import base64

async def capture_dom(page):
    """
    Capture the DOM of the current page.
    
    Args:
        page: Playwright page object
        
    Returns:
        dict: DOM structure with HTML, CSS and resources
    """
    if not page:
        return None
    
    # Get HTML content
    html = await page.content()
    
    # Get computed styles for all elements
    styles = await page.evaluate("""
        () => {
            const allElements = document.querySelectorAll('*');
            const styles = {};
            
            for (let i = 0; i < allElements.length; i++) {
                const element = allElements[i];
                if (!element.id) continue;
                
                const computedStyle = window.getComputedStyle(element);
                styles[element.id] = {
                    width: computedStyle.width,
                    height: computedStyle.height,
                    color: computedStyle.color,
                    backgroundColor: computedStyle.backgroundColor,
                    fontSize: computedStyle.fontSize,
                    fontFamily: computedStyle.fontFamily,
                    display: computedStyle.display,
                    position: computedStyle.position,
                    top: computedStyle.top,
                    left: computedStyle.left
                };
            }
            return styles;
        }
    """)
    
    # Take a screenshot as a fallback
    screenshot_base64 = await page.screenshot(type='jpeg', quality=80, full_page=False)
    screenshot = base64.b64encode(screenshot_base64).decode('utf-8')
    
    # Get the current URL
    url = page.url
    
    # Capture visible viewport dimensions
    viewport = await page.evaluate("""
        () => {
            return {
                width: window.innerWidth,
                height: window.innerHeight,
                scrollX: window.scrollX,
                scrollY: window.scrollY
            }
        }
    """)
    
    return {
        "html": html,
        "styles": styles,
        "screenshot": f"data:image/jpeg;base64,{screenshot}",
        "url": url,
        "viewport": viewport
    }