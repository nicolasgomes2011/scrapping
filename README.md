# RgeScrapper

This project is a Python-based web scraper designed to retrieve the electricity bill document from an website. 

## Features

- **HTTP Request:** Retrieves website content using the `requests` library.
- **HTML Parsing:** Uses BeautifulSoup to find the link to the electricity bill.
- **File Download:** Downloads and saves the document as a PDF file.

## Prerequisites

- Python 3.6+
- [Requests](https://docs.python-requests.org/)
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

## Installation

1. **Clone the repository (if applicable):**

   ```bash
   git clone <REPOSITORY_URL>
   cd scrapping
   ```

2. **Create and activate a virtual environment (recommended):**

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install the necessary dependencies:**

   ```bash
   pip install requests beautifulsoup4
   ```

## Configuration

Ensure that you update the URL in the `rge_scrapping.py` file with the actual URL of the RGE website:

```python
url_inicial = "https://exemplo.com/rge"  # Replace with the actual URL.
```

## Usage

Execute the scraper by running:

```bash
python rge_scrapping.py
```

The script will:
- Request the webpage.
- Parse the HTML to locate the link for the electricity bill.
- Download the document and save it as `conta_luz.pdf` locally.

## Contributing

Feel free to fork the repository and submit pull requests if you'd like to improve the project.

## License

This project is licensed under the MIT License.
