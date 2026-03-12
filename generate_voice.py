import sys
import json
import subprocess

VOICE = 'en-US-ChristopherNeural'

def generate_voice(script_text, output_path):
    clean = script_text.replace('"', '').replace("'", '').replace('—', ' ')

    result = subprocess.run([
        '/home/shreyanshpandey/shorts-automation/venv/bin/edge-tts',
        '--voice', VOICE,
        '--text', clean,
        '--write-media', output_path
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print('ERROR:', result.stderr)
        sys.exit(1)

    print(json.dumps({'voice_path': output_path, 'status': 'ok'}))

if __name__ == '__main__':
    script = sys.argv[1]
    output = sys.argv[2]
    generate_voice(script, output)
