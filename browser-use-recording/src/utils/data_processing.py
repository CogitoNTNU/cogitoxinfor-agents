def process_html_content(html_content):
    """Process and clean HTML content for storage."""
    from bs4 import BeautifulSoup

    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract text and remove unwanted tags
    text = soup.get_text()
    cleaned_text = ' '.join(text.split())

    return cleaned_text


def save_screenshot(screenshot, file_path):
    """Save the screenshot to the specified file path."""
    with open(file_path, 'wb') as file:
        file.write(screenshot)


def save_agent_history(data, file_path):
    """Save agent history data to a JSON file."""
    import json

    with open(file_path, 'w') as json_file:
        json.dump(data, json_file)