import sys
import json
import asyncio
import os
import random
import edge_tts

VOICES = [
    'en-US-ChristopherNeural',
    'en-US-GuyNeural',
    'en-US-EricNeural',
    'en-GB-RyanNeural',
    'en-AU-WilliamNeural',
]

VOICE = random.choice(VOICES)

async def generate_voice_async(script, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    communicate = edge_tts.Communicate(script, VOICE)
    await communicate.save(output_path)

def generate_voice(script, output_path):
    asyncio.run(generate_voice_async(script, output_path))
    return {'voice_path': output_path, 'status': 'ok'}

if __name__ == '__main__':
    script = sys.argv[1]
    output_path = sys.argv[2]
    result = generate_voice(script, output_path)
    print(json.dumps(result))
