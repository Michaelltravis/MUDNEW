#!/usr/bin/env python3
"""Build the 3D client's sounds and music from the CC0 sources in manifest.json.

    tools/audio/fetch.sh            # download into tools/audio/.cache
    python3 tools/audio/build.py    # convert into src/web_isometric/world3d/audio/

Sound effects become short mono mp3s (k_1.mp3 .. k_n.mp3 for a key with n sources); music
becomes stereo mp3 at an even loudness, trimmed where the manifest says so (with a fade, the
player crossfades the loop). Also writes audio/files.json (every file, for the tests) and
audio/CREDITS.md. Needs ffmpeg: on PATH, or `pip install imageio-ffmpeg`.
"""
import json
import os
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'src', 'web_isometric', 'world3d', 'audio')


def ffmpeg():
    exe = shutil.which('ffmpeg')
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit('ffmpeg not found: install it, or `pip install imageio-ffmpeg`')


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ffmpeg failed: {' '.join(cmd)}\n{r.stderr[-800:]}")


def main():
    cache = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '.cache')
    man = json.load(open(os.path.join(HERE, 'manifest.json')))
    ff = ffmpeg()
    sfx_dir, music_dir = os.path.join(OUT, 'sfx'), os.path.join(OUT, 'music')
    for d in (sfx_dir, music_dir):
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)

    # the packs' files, by name
    found = {}
    for name in man['packs']:
        zp = os.path.join(cache, 'packs', name + '.zip')
        if not os.path.exists(zp):
            sys.exit(f'missing {zp}: run tools/audio/fetch.sh first')
        z = zipfile.ZipFile(zp)
        for info in z.infolist():
            base, ext = os.path.splitext(os.path.basename(info.filename))
            if ext.lower() == '.ogg':
                found[f'{name}:{base}'] = (z, info)

    files = {'sfx': {}, 'music': {}}
    tmp = os.path.join(cache, 'tmp')
    os.makedirs(tmp, exist_ok=True)
    for key, sources in man['sfx'].items():
        for i, src in enumerate(sources, 1):
            if src not in found:
                sys.exit(f'{key}: no file {src} in the packs')
            z, info = found[src]
            raw = os.path.join(tmp, 'in.ogg')
            with z.open(info) as fi, open(raw, 'wb') as fo:
                fo.write(fi.read())
            out = os.path.join(sfx_dir, f'{key}_{i}.mp3')
            run([ff, '-y', '-loglevel', 'error', '-i', raw, '-ac', '1', '-ar', '44100',
                 '-codec:a', 'libmp3lame', '-q:a', '5', out])
        files['sfx'][key] = len(sources)

    for key, m in man['music'].items():
        src = os.path.join(cache, 'music', key + os.path.splitext(m['url'])[1].lower())
        if not os.path.exists(src):
            sys.exit(f'missing {src}: run tools/audio/fetch.sh first')
        af = 'loudnorm=I=-20:TP=-2:LRA=11'
        cmd = [ff, '-y', '-loglevel', 'error', '-i', src]
        if m.get('trim'):
            t = float(m['trim'])
            cmd += ['-t', str(t)]
            af += f',afade=t=out:st={t - 4}:d=4'
        cmd += ['-af', af, '-ac', '2', '-ar', '44100', '-codec:a', 'libmp3lame', '-b:a', '80k',
                os.path.join(music_dir, key + '.mp3')]
        run(cmd)
        files['music'][key] = 1

    with open(os.path.join(OUT, 'files.json'), 'w') as f:
        json.dump(files, f, indent=1, sort_keys=True)
    with open(os.path.join(OUT, 'CREDITS.md'), 'w') as f:
        f.write('# Sounds and music in /play\n\nEvery file here is CC0 (public domain). Thank you to the authors.\n'
                'Rebuild with `tools/audio/fetch.sh && python3 tools/audio/build.py` (sources: tools/audio/manifest.json).\n\n'
                '## Sound effects (audio/sfx)\n\n')
        for p in man['packs'].values():
            f.write(f"- **{p['title']}** by {p['author']}, {p['license']} — {p['page']}\n")
        f.write('\nSpell, swing and ambience sounds that are not in these packs are made in the browser (audio.js).\n\n'
                '## Music (audio/music)\n\n')
        for key, m in man['music'].items():
            f.write(f"- `{key}.mp3`: **{m['title']}** by {m['author']}, {m['license']} — {m['page']}\n")
    total = sum(os.path.getsize(os.path.join(d, n)) for d in (sfx_dir, music_dir) for n in os.listdir(d))
    print(f"{sum(files['sfx'].values())} sounds, {len(files['music'])} tracks, {total / 1e6:.1f} MB in {os.path.normpath(OUT)}")


if __name__ == '__main__':
    main()
