# Artnet Artist Scraper
This is a scraper built in Python. The script creates a list of all artists (including design/furniture companies) that have had works offered for sale (mainly auctions/galleries), as recorded by artnet. It creates a DataFrame for all artists recorded on artnet (approximately 400k), further splitting data into the artist's country of origin and active years.

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
