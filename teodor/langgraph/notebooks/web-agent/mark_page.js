
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

    // Function to process elements and return bounding boxes
    function processElements(documentContext) {
        var vw = Math.max(
            documentContext.documentElement.clientWidth || 0,
            window.innerWidth || 0
        );
        var vh = Math.max(
            documentContext.documentElement.clientHeight || 0,
            window.innerHeight || 0
        );

        var items = Array.prototype.slice
            .call(documentContext.querySelectorAll("*"))
            .map(function (element) {

                //element.scrollIntoView({ block: "center", inline: "center" });

                var textualContent = element.textContent.trim().replace(/\s{2,}/g, " ");
                var elementType = element.tagName.toLowerCase();
                var ariaLabel = element.getAttribute("aria-label") || "";
                var elementId = element.getAttribute("id") || "";

                var rects = [...element.getClientRects()]
                    .filter((bb) => {
                        var center_x = bb.left + bb.width / 2;
                        var center_y = bb.top + bb.height / 2;
                        var elAtCenter = documentContext.elementFromPoint(center_x, center_y);

                        return elAtCenter === element || element.contains(elAtCenter);
                    })
                    .map((bb) => {
                        const rect = {
                            left: Math.max(0, bb.left),
                            top: Math.max(0, bb.top),
                            right: Math.min(vw, bb.right),
                            bottom: Math.min(vh, bb.bottom),
                        };
                        return {
                            ...rect,
                            width: rect.right - rect.left,
                            height: rect.bottom - rect.top,
                        };
                    });

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
                        window.getComputedStyle(element).cursor == "pointer" ||
                        element.tagName === "IFRAME" ||
                        element.tagName === "VIDEO",
                    area,
                    rects,
                    text: textualContent,
                    type: elementType,
                    ariaLabel: ariaLabel,
                    id: elementId,
                };
            })
            .filter((item) => item.include && item.area >= 10);

        // Only keep inner clickable items
        items = items.filter(
            (x) => !items.some((y) => x.element.contains(y.element) && !(x == y))
        );

        return items;
    }

    // Process the main page
    var items = processElements(document);

    // Process iframes
    var iframes = Array.from(document.querySelectorAll("iframe"));
    iframes.forEach((iframe, iframeIndex) => {
        try {
            var iframeDocument = iframe.contentDocument || iframe.contentWindow.document;
            var iframeItems = processElements(iframeDocument);

            // Adjust iframe element positions relative to the main page
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

    var bodyRect = document.body.getBoundingClientRect();

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

    const coordinates = items.flatMap((item) =>
        item.rects.map(({ left, top, width, height }) => ({
            x: (left + left + width) / 2,
            y: (top + top + height) / 2,
            type: item.type,
            text: item.text,
            ariaLabel: item.ariaLabel,
            id: item.id,
        }))
    );
    return coordinates;
}