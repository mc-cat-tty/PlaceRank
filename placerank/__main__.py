from placerank.tui.components import *
from placerank.tui.events import *
from placerank.tui.presenter import *
from placerank.query_expansion import *
from placerank.ir_model import *
from placerank.models import *
from placerank.dataset import ReviewsDatabase
from placerank.config import INDEX_DIR, HELP_FILENAME, DATASET_CACHE_FILE, HF_CACHE, REVIEWS_DB, REVIEWS_INDEX
from whoosh.index import open_dir
from urwid import MainLoop, ExitMainLoop
import signal


def sigint_handler(signum, frame):
    raise ExitMainLoop()

def main() -> None:
    signal.signal(signal.SIGINT, sigint_handler)

    with open(HELP_FILENAME, 'r') as readme:
        window = Window(readme.read())
    
    idx = open_dir(INDEX_DIR)
    model = IRModel(WhooshSpellCorrection, ThesaurusQueryExpansion(HF_CACHE), idx)
    model = SentimentAwareIRModel(WhooshSpellCorrection, ThesaurusQueryExpansion(HF_CACHE), idx, SentimentRanker(REVIEWS_INDEX))
    presenter = Presenter(model, DATASET_CACHE_FILE, ReviewsDatabase(REVIEWS_DB))
    loop = MainLoop(window, palette=PALETTE)
    loop.run()

if __name__ == "__main__":
    main()