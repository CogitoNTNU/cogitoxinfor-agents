import requests

url = "https://api.va.landing.ai/v1/tools/agentic-document-analysis"
files = {
  "image": open("{{path_to_file}}", "rb")
  # OR, for PDF
  # "pdf": open("{{path_to_file}}", "rb")
}
headers = {
  "Authorization": "Basic {{your_api_key}}",
}
response = requests.post(url, files=files, headers=headers)

print(response.json())
