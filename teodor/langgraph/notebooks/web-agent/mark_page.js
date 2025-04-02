
const customCSS = `
::-webkit-scrollbar {
    width: 10px;
}
::-webkit-scrollbar-track {
    background: #27272a;
}
::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 0.375rem;
}
::-webkit-scrollbar-thumb:hover {
    background: #555;
}
`;

const styleTag = document.createElement("style");
styleTag.textContent = customCSS;
document.head.append(styleTag);

let labels = [];

function unmarkPage() {
// Unmark page logic
for (const label of labels) {
document.body.removeChild(label);
}
labels = [];
}



function markPage() {
    unmarkPage();

    var bodyRect = document.body.getBoundingClientRect();

    // Helper function to traverse shadow roots and collect elements
    function collectAllElements(root) {
        if (!root) return [];
        
        const allElems = Array.from(root.querySelectorAll("*") || []);
        const shadowElements = [];
        
        // For each element, also traverse any shadow root
        for (const el of allElems) {
            if (el.shadowRoot) {
                shadowElements.push(...collectAllElements(el.shadowRoot));
            }
        }
        return [...allElems, ...shadowElements];
    }

    // Function to process elements and return bounding boxes
    function processElements(documentContext) {
        if (!documentContext) return [];
        
        var vw = Math.max(
            documentContext.documentElement?.clientWidth || 0,
            window.innerWidth || 0
        );
        var vh = Math.max(
            documentContext.documentElement?.clientHeight || 0,
            window.innerHeight || 0
        );

        // Get all elements including those in shadow DOM
        var allElements = collectAllElements(documentContext);
        
        var items = allElements
            .filter(element => element) // Skip null elements
            .map(function (element) {
                try {
                    var textualContent = (element.textContent || "").trim().replace(/\s{2,}/g, " ");
                    var elementType = element.tagName.toLowerCase();
                    var ariaLabel = element.getAttribute?.("aria-label") || "";
                    var elementId = element.getAttribute?.("id") || "";

                    var rects = [];
                    try {
                        rects = Array.from(element.getClientRects() || [])
                            .filter((bb) => {
                                if (!bb || typeof bb.left !== 'number') return false;
                                var center_x = bb.left + bb.width / 2;
                                var center_y = bb.top + bb.height / 2;
                                var elAtCenter = documentContext.elementFromPoint?.(center_x, center_y);
                                return elAtCenter === element || element.contains?.(elAtCenter);
                            })
                            .map((bb) => {
                                const rect = {
                                    left: Math.max(0, bb.left || 0),
                                    top: Math.max(0, bb.top || 0),
                                    right: Math.min(vw, bb.right || 0),
                                    bottom: Math.min(vh, bb.bottom || 0),
                                };
                                return {
                                    ...rect,
                                    width: rect.right - rect.left,
                                    height: rect.bottom - rect.top,
                                };
                            });
                    } catch (e) {
                        console.warn("Error getting client rects:", e);
                    }

                    var area = rects.reduce((acc, rect) => acc + rect.width * rect.height, 0);

                    return {
                        element: element,
                        include:
                            element.tagName === "INPUT" ||
                            element.tagName === "TEXTAREA" ||
                            element.tagName === "SELECT" ||
                            element.tagName === "BUTTON" ||
                            element.tagName === "A" ||
                            element.onclick != null ||
                            (window.getComputedStyle(element).cursor === "pointer") ||
                            element.tagName === "IFRAME" ||
                            element.tagName === "VIDEO" ||
                            elementType === "search-newfrontier-podlet-isolated", // Special case for finn.no
                        area,
                        rects,
                        text: textualContent,
                        type: elementType,
                        ariaLabel: ariaLabel,
                        id: elementId,
                    };
                } catch (e) {
                    console.warn("Error processing element:", e);
                    return {
                        element: element,
                        include: false,
                        area: 0,
                        rects: [],
                        text: "",
                        type: "unknown",
                        ariaLabel: "",
                        id: "",
                    };
                }
            })
            .filter((item) => item && item.include && item.area >= 20 && item.rects.length > 0);

        // Only keep inner clickable items
        items = items.filter(
            (x) => !items.some((y) => x.element !== y.element && x.element.contains?.(y.element))
        );

        return items || []; // Always return an array
    }

    // Process the main page
    var items = processElements(document) || [];

    // Process iframes
    var iframes = Array.from(document.querySelectorAll("iframe") || []);
    iframes.forEach((iframe, iframeIndex) => {
        try {
            if (!iframe.src) {
                // For empty iframes, create a placeholder box
                var iframeRect = iframe.getBoundingClientRect();
                if (iframeRect.width > 0 && iframeRect.height > 0) {
                    items.push({
                        element: iframe,
                        include: true,
                        area: iframeRect.width * iframeRect.height,
                        rects: [{
                            left: iframeRect.left,
                            top: iframeRect.top,
                            right: iframeRect.right,
                            bottom: iframeRect.bottom,
                            width: iframeRect.width,
                            height: iframeRect.height
                        }],
                        text: "",
                        type: "iframe",
                        ariaLabel: iframe.getAttribute("aria-label") || "Advertisement",
                        id: iframe.id || null
                    });
                }
            } else {
                var iframeDocument = iframe.contentDocument || iframe.contentWindow?.document;
                var iframeItems = processElements(iframeDocument);

                // Adjust iframe element positions relative to the main page
                if (iframeItems && iframeItems.length) {
                    var iframeRect = iframe.getBoundingClientRect();
                    iframeItems.forEach((item) => {
                        item.rects = item.rects.map((rect) => ({
                            left: rect.left + iframeRect.left,
                            top: rect.top + iframeRect.top,
                            right: rect.right + iframeRect.left,
                            bottom: rect.bottom + iframeRect.top,
                            width: rect.width,
                            height: rect.height,
                        }));
                    });
                    items = items.concat(iframeItems);
                }
            }
        } catch (e) {
            console.warn(`Could not access iframe content: ${e}`);
        }
    });

    // Function to generate random colors
    function getRandomColor() {
        var letters = "0123456789ABCDEF";
        var color = "#";
        for (var i = 0; i < 6; i++) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    }

    // Make sure items is always an array
    items = items || [];

    items.forEach(function (item, index) {
        item.rects.forEach((bbox) => {
            var adjustedLeft = bbox.left - bodyRect.left;
            var adjustedTop = bbox.top - bodyRect.top;
    
            var newElement = document.createElement("div");
            var borderColor = getRandomColor();
            newElement.style.outline = `2px dashed ${borderColor}`;
            newElement.style.position = "fixed";
            newElement.style.left = adjustedLeft + "px";
            newElement.style.top = adjustedTop + "px";
            newElement.style.width = bbox.width + "px";
            newElement.style.height = bbox.height + "px";
            newElement.style.pointerEvents = "none";
            newElement.style.boxSizing = "border-box";
            newElement.style.zIndex = 2147483647;
    
            // Add floating label at the corner
            var label = document.createElement("span");
            label.textContent = index;
            label.style.position = "absolute";
            label.style.top = "-19px";
            label.style.left = "0px";
            label.style.background = borderColor;
            label.style.color = "white";
            label.style.padding = "2px 4px";
            label.style.fontSize = "12px";
            label.style.borderRadius = "2px";
            newElement.appendChild(label);

            document.body.appendChild(newElement);
            labels.push(newElement);
        });
    });

    // Ensure coordinates is always an array
    const coordinates = items.length ? items.flatMap((item) =>
        item.rects.map(({ left, top, width, height }) => ({
            x: (left + left + width) / 2,
            y: (top + top + height) / 2,
            type: item.type,
            text: item.text,
            ariaLabel: item.ariaLabel,
            id: item.id,
        }))
    ) : [];
    
    return coordinates;
}