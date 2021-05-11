# Artnet Artist Scraper
Scraper built in Python creating DataFrame for all artists (approximately 400k) on artnet, separating data into country of origin and active years.

## Set Up

1. Clone the project using:

```bash
git clone https://github.com/kevinbennet/artnet-artist-scraper.git
```

2. Set up a virtual environment (Optional):

```bash
python -m venv venv
```

3. Activate the virtual environment (Optional):

- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`

4. Install required packages:

```bash
cd artnet-artist-scraper
pip install -r requirements.txt
```

## Usage
To run scrape:
```python
python artnet_scraper.py
```
This will create both a csv and pickle file in the fork directory.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
