"""
Text smartglass client
"""
import sys
import logging
import gevent.socket

LOGGER = logging.getLogger(__name__)


def on_text_config(payload):
    pass


def on_text_input(console, payload):
    print(
        "\n\nWAITING FOR TEXT INPUT - "
        "SHELL WILL KEEP SCROLLING\n"
        "Prompt: %s\n" % console.text.text_prompt
    )
    gevent.socket.wait_read(sys.stdin.fileno())
    text = input()
    console.send_systemtext_input(text)
    console.finish_text_input()


def on_text_done(payload):
    pass
