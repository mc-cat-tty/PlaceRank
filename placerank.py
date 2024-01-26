from placerank.tui.components import *
from placerank.tui.events import *
from placerank.tui.presenter import *
from placerank.models import IRModel
from urwid import MainLoop, ExitMainLoop
import signal

def sigint_handler(signum, frame):
    raise ExitMainLoop()

def main() -> None:
    signal.signal(signal.SIGINT, sigint_handler)

    presenter = Presenter(IRModel())
    loop = MainLoop(Window(), palette=PALETTE)
    loop.run()

if __name__ == "__main__":
    main()