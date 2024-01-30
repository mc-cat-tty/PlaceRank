# PlaceRank

Search engine for AirBnB listings.

Final assignment of the "Gestione dell'informazione" course at University of Modena and Reggio Emilia. Academic year 2023-2024.

## Bringup
In order to enjoy our not-so-SOTA search engine, the average user needs to run the following commands in a shell where the Python interpreter is available:
```bash
# INSTALL DEPENDENCIES
python3 -m pip install -r requirements.txt

# DOWNLOAD DATASET, CREATE INDEX, DOWNLOAD WORDNET AND BERT MODEL
python3 -m setup
```

Please, be aware that `bert-large-uncased-whole-word-masking` can take up to 1.5 Gb of disk space and 30 min to download.

The model is by default stored in _hf\_cache_ folder.

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

In case of any doubt about the interface visit [help page](HELP.txt).

### Benchmarks

## Contributors
 - Corradini Giulio
 - Mecatti Francesco
 - Stano Antonio