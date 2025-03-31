import base64
from langchain_core.runnables import chain as chain_decorator
from models import BBox
import asyncio

# Load the JavaScript code for annotating the page
with open("mark_page.js") as f:
    # Some JavaScript we will run on each step
    # to take a screenshot of the page, select the
    # elements to annotate, and add bounding boxes
    mark_page_script = f.read()

@chain_decorator
async def mark_page(page):
    """
    Annotates the current browser page with bounding boxes for interactive elements,
    including elements inside iframes.
    """
    try:
        # Wait for the page to load completely
        await page.wait_for_load_state("domcontentloaded")

        # Execute the JavaScript code to annotate the page
        await page.evaluate(mark_page_script)

        # Retry logic to ensure bounding boxes are captured
        for _ in range(10):  # Retry up to 10 times in case of loading delays
            try:
                bboxes = await page.evaluate("markPage()")  # Get bounding boxes
                print("Bounding boxes:", bboxes)  # Debugging: Log bounding boxes
                break
            except Exception as e:
                print(f"Error during markPage execution: {e}")
                await asyncio.sleep(3)  # Wait before retrying
        else:
            raise Exception("Failed to get bounding boxes after 10 retries")

        # Take a screenshot of the page
        screenshot = await page.screenshot()

        # Remove annotations after capturing
        await page.evaluate("unmarkPage()")

        return {
            "img": base64.b64encode(screenshot).decode(),  # Encode screenshot as base64
            "bboxes": bboxes,  # Return bounding boxes
        }
    except Exception as e:
        print(f"Error in mark_page: {e}")
        raise


async def annotate(state):
    """
    Annotates the current page and processes bounding boxes for both the main page and iframes.
    """
    try:
        # Annotate the page and get bounding boxes
        marked_page = await mark_page.with_retry().ainvoke(state.page)
        print("Annotated bounding boxes:", marked_page["bboxes"])  # Log the bounding boxes

        # Set the annotated image and bounding boxes in the state
        state.img = marked_page["img"]
        state.bboxes = [
            BBox(**bbox) for bbox in marked_page["bboxes"]
        ]  # Convert bounding boxes to BBox objects

        # Check if any bounding box is of type 'iframe'
        iframe_bboxes = [bbox for bbox in marked_page["bboxes"] if bbox["type"] == "iframe"]
        for iframe_bbox in iframe_bboxes:
            src = iframe_bbox.get("src")
            if not src:
                print(f"Skipping iframe with no src: {iframe_bbox}")
                continue

            print(f"Iframe detected with src: {src}. Processing iframe...")
            try:
                # Switch to the iframe and annotate its content
                iframe = await state.page.frame_locator(f"iframe[src='{src}']").frame()
                iframe_marked_page = await mark_page.with_retry().ainvoke(iframe)
                print("Annotated iframe bounding boxes:", iframe_marked_page["bboxes"])

                # Combine iframe bounding boxes with the main page bounding boxes
                state.bboxes.extend([
                    BBox(**bbox) for bbox in iframe_marked_page["bboxes"]
                ])
            except Exception as iframe_error:
                print(f"Error processing iframe with src {src}: {iframe_error}")

    except Exception as e:
        print(f"Error in annotate: {e}")
        raise

    return state