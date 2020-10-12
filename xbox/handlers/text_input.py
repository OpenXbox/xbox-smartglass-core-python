"""
Text smartglass client
"""
import logging
import asyncio
import aioconsole

LOGGER = logging.getLogger(__name__)


async def userinput_callback(console, prompt):
    print('WAITING FOR TEXT INPUT...')
    text = await aioconsole.ainput(prompt)

    await console.send_systemtext_input(text)
    await console.finish_text_input()


def on_text_config(payload):
    pass


def on_text_input(console, payload):
    asyncio.create_task(userinput_callback(console, console.text.text_prompt))


def on_text_done(payload):
    pass
