from placerank.tui.components import *
from placerank.tui.events import *
from placerank.tui.presenter import *
from placerank.models import *
from placerank.preprocessing import get_default_analyzer
from whoosh.index import open_dir
from urwid import MainLoop, ExitMainLoop
import signal

HELP_FILENAME = "HELP.txt"

def sigint_handler(signum, frame):
    raise ExitMainLoop()

def main() -> None:
    signal.signal(signal.SIGINT, sigint_handler)

    with open(HELP_FILENAME, 'r') as readme:
        window = Window(readme.read())
    
    idx = open_dir("index")
    presenter = Presenter(IRModelDumb(get_default_analyzer(), None, RetrievalModelDumb(idx, None)))
    loop = MainLoop(window, palette=PALETTE)
    loop.run()

if __name__ == "__main__":
    main()