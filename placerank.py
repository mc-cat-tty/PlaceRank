from placerank.tui.components import *
from placerank.tui.events import *
from urwid import MainLoop, ExitMainLoop
import signal

def sigint_handler(signum, frame):
    raise ExitMainLoop()

def main() -> None:
    o = Observer(lambda e, v: print(f'Searched: {v}'), [Events.SEARCH.value])
    signal.signal(signal.SIGINT, sigint_handler)
    loop = MainLoop(Window(), palette=PALETTE)
    loop.run()

if __name__ == "__main__":
    main()