import asyncio


async def ainput(prompt: str = '') -> str:
    return await asyncio.to_thread(input, f'{prompt}')