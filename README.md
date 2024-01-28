# PlaceRank

Search engine for AirBnB listings.

Final assignment of the "Gestione dell'informazione" course at University of Modena and Reggio Emilia. Academic year 2023-2024.

## Bringup
In order to enjoy our not-so-SOTA search engine, the average user needs to run the following commands in a shell where the Python interpreter is available:
```bash
python3 -m pip install -r requirements.txt
python3 -m placerank.preprocessing  # Downloads WordNet
# Download the dataset and build the index
python3 -m placerank.dataset -i index -r http://data.insideairbnb.com/united-states/ny/new-york-city/2024-01-05/data/listings.csv.gz -l datasets/ny_listings.csv
```

For experienced user, we suggest to firstly crate a virtual environment, where all packages will be installed; then follow the above procedure:
```bash
python3 -m venv venv
source venv/bin/activate
```

## Usage
### TUI
```bash
python3 -m placerank
```

### Benchmarks

## Contributors
 - Corradini Giulio
 - Mecatti Francesco
 - Stano Antonio