"""Convert native renderer readback to PNG and check the P1A fixture."""

import argparse
import json
import math
import pathlib

from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('directory', type=pathlib.Path)
args = parser.parse_args()
root = args.directory
info = dict(line.split('=', 1) for line in (root / 'render-info.txt').read_text(encoding='utf-8').splitlines() if '=' in line)
width = int(info['readback_width'])
height = int(info['readback_height'])
assert (width, height) == (1920, 1080), 'Incorrect physical readback dimensions'
assert (int(info['renderer_width']), int(info['renderer_height'])) == (1920, 1080)
assert (int(info['overlay_width']), int(info['overlay_height'])) == (1920, 1080)
assert info['readback_ok'] == '1'


def load_bgra(name):
    data = (root / name).read_bytes()
    assert len(data) == width * height * 4, f'Invalid byte count: {name}'
    return Image.frombytes('RGBA', (width, height), data, 'raw', 'BGRA')


frame = load_bgra('readback.bgra').convert('RGB')
source = load_bgra('source.bgra')
frame.save(root / 'alpha-test-1920x1080.png')
frame.save(root / 'alpha-ramp-1920x1080.png')
source.save(root / 'alpha-source.png')
foreground = tuple(map(int, info['foreground_rgb'].split(',')))
background = tuple(map(int, info['background_rgb'].split(',')))
alpha_bits = int(info['texture_a_bits'])
assert alpha_bits > 1, 'GPU texture has no smooth alpha'

# The device may truncate during conversion. Bound one input quantization step,
# plus one framebuffer step and one unit of blend/clear rounding. This is derived
# from the reported formats rather than fitted to the measured pixels.
alpha_step = 255 / ((1 << alpha_bits) - 1)
limits = []
for channel, fg, bg in zip('rgb', foreground, background):
    texture_step = 255 / ((1 << int(info[f'texture_{channel}_bits'])) - 1)
    output_step = 255 / ((1 << int(info[f'readback_native_{channel}_bits'])) - 1)
    limits.append(math.ceil(abs(fg - bg) * alpha_step / 255 + texture_step + output_step + 1))


def sample(x, y, alpha):
    rgba = source.getpixel((x, y))
    assert rgba == foreground + (alpha,), f'Source fixture differs at {(x, y)}: {rgba}'
    expected = tuple(round(bg + (fg - bg) * alpha / 255) for fg, bg in zip(foreground, background))
    actual = frame.getpixel((x, y))
    error = tuple(abs(a - e) for a, e in zip(actual, expected))
    return {'x': x, 'y': y, 'source_alpha': alpha, 'expected_rgb': expected,
            'actual_rgb': actual, 'absolute_error': error,
            'pass': all(e <= limit for e, limit in zip(error, limits))}


blocks = [sample(112 + index * 152, 88, alpha) for index, alpha in enumerate((0, 64, 128, 192, 255))]
ramp = [sample(49 + alpha * 3, 184, alpha) for alpha in range(256)]
background_actual = frame.getpixel((36, 36))
background_ok = all(abs(a - b) <= 1 for a, b in zip(background_actual, background))
all_ok = background_ok and all(s['pass'] for s in blocks + ramp)
all_ok = all_ok and len({tuple(s['actual_rgb']) for s in blocks}) == 5
result = {
    'status': 'PASS' if all_ok else 'FAIL',
    'dimensions': [width, height], 'alpha_contract': info['alpha_contract'],
    'texture_alpha_bits': alpha_bits, 'per_channel_error_limits': limits,
    'background_expected': background, 'background_actual': background_actual,
    'blocks': blocks, 'ramp_unique_rgb': len({tuple(s['actual_rgb']) for s in ramp}),
    'ramp_max_error': [max(s['absolute_error'][c] for s in ramp) for c in range(3)],
    'ramp': ramp,
}
(root / 'alpha-pixels.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
lines = [f"status={result['status']}", f'texture_alpha_bits={alpha_bits}', f'error_limits={limits}',
         f'background_expected={background} actual={background_actual}',
         'alpha x y expected_rgb actual_rgb absolute_error pass']
lines += [f"{s['source_alpha']} {s['x']} {s['y']} {s['expected_rgb']} {s['actual_rgb']} {s['absolute_error']} {s['pass']}"
          for s in blocks + ramp]
(root / 'alpha-pixels.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(json.dumps({key: value for key, value in result.items() if key != 'ramp'}, indent=2))
raise SystemExit(not all_ok)
