"""Upload article images before publishing; requires Python 3 and Git SSH login."""
import hashlib
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.image-repo'
REMOTE = 'git@github.com:Limanman507/pictureSource.git'
RAW = 'https://raw.githubusercontent.com/Limanman507/pictureSource/'
# Inline Markdown destinations, including angle brackets, spaces, and nested parentheses.
INLINE = re.compile(r'!\[[^\]\n]*\]\(\s*(?:<(?P<angle>[^>]+)>|(?P<plain>(?:[^()\n]|\([^()]*\))+?))(?:\s+["\'][^\n]*?["\'])?\s*\)')
HTML = re.compile(r'<img\b[^>]*?\bsrc\s*=\s*(["\'])(?P<src>.*?)\1', re.I)
DEFINITION = re.compile(r'^ {0,3}\[(?P<label>[^\]]+)\]:\s*(?:<(?P<angle>[^>]+)>|(?P<plain>\S+))', re.M)
REFERENCE = re.compile(r'!\[(?P<alt>[^\]]*)\](?:\[(?P<label>[^\]]*)\])?(?!\()')


def image_spans(text):
    # Ignore fenced code, inline code and comments so examples remain untouched.
    masked = list(text)
    code = re.compile(r'^ {0,3}(?P<fence>`{3,}|~{3,})[^\n]*\n.*?^ {0,3}(?P=fence)[ \t]*$|`+[^`\n]*`+|<!--[\s\S]*?-->', re.M | re.S)
    for match in code.finditer(text):
        for pos in range(match.start(), match.end()):
            if masked[pos] != '\n':
                masked[pos] = ' '
    visible = ''.join(masked)
    spans = []
    for pattern in (INLINE, HTML):
        for match in pattern.finditer(visible):
            group = 'src' if pattern is HTML else ('angle' if match.group('angle') is not None else 'plain')
            start, end = match.span(group)
            while end > start and text[end - 1].isspace():
                end -= 1
            spans.append((start, end))
    labels = {' '.join((m.group('label') or m.group('alt')).split()).casefold() for m in REFERENCE.finditer(visible)}
    for match in DEFINITION.finditer(visible):
        if ' '.join(match.group('label').split()).casefold() in labels:
            spans.append(match.span('angle' if match.group('angle') is not None else 'plain'))
    return sorted(set(spans))


def extension(data):
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return '.png'
    if data.startswith(b'\xff\xd8\xff'):
        return '.jpg'
    if data.startswith((b'GIF87a', b'GIF89a')):
        return '.gif'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return '.webp'
    if b'<svg' in data[:1024].lower():
        return '.svg'
    if data.startswith(b'BM'):
        return '.bmp'
    if data[4:8] == b'ftyp' and b'avif' in data[8:32]:
        return '.avif'
    raise ValueError('Unsupported image or response is not an image. Save it as PNG/JPEG/WebP and retry.')


def load_image(source, article):
    source = source.replace('&amp;', '&')
    if source.startswith('//'):
        source = 'https:' + source
    if source.startswith(('https://', 'http://')):
        request = urllib.request.Request(source, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    if source.startswith('data:'):
        import base64
        header, payload = source.split(',', 1)
        return base64.b64decode(payload) if ';base64' in header else urllib.parse.unquote_to_bytes(payload)
    if source.startswith('file:'):
        parsed = urllib.parse.urlsplit(source)
        source = urllib.request.url2pathname(parsed.path)
        if parsed.netloc:
            source = '//' + parsed.netloc + source
    else:
        source = urllib.parse.unquote(source)
        source = re.sub(r'\\([ ()])', r'\1', source)
    path = Path(source)
    if not path.is_absolute():
        path = article.parent / path
    if not path.is_file():
        raise FileNotFoundError(f'Image not found in {article.name}: {path}')
    return path.read_bytes()


def git(*args):
    result = subprocess.run(['git', '-C', str(CACHE), *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def main():
    changes = []
    images = {}
    for article in sorted((ROOT / 'docs').rglob('*')):
        if article.suffix.lower() not in {'.md', '.markdown'}:
            continue
        original = article.read_text(encoding='utf-8-sig')
        replacements = []
        for start, end in image_spans(original):
            source = original[start:end]
            if source.startswith(RAW):
                continue
            try:
                data = load_image(source, article)
                name = hashlib.sha256(data).hexdigest() + extension(data)
            except Exception as exc:
                # Do not echo signed URL query strings or other credentials.
                raise RuntimeError(f'Cannot load image in {article.name} ({type(exc).__name__}). Check the image path or save the image locally.') from None
            images[name] = data
            replacements.append((start, end, name))
        if replacements:
            changes.append((article, original, replacements))
    if not changes:
        print('Images: no new images to upload.')
        return
    if not CACHE.exists():
        subprocess.run(['git', 'clone', REMOTE, str(CACHE)], check=True)
    if git('remote', 'get-url', 'origin') != REMOTE:
        raise RuntimeError('Image cache origin does not match pictureSource.')
    if git('status', '--porcelain'):
        raise RuntimeError('Image cache has unfinished changes. Resolve them before publishing.')
    git('fetch', 'origin')
    branch = git('symbolic-ref', '--short', 'refs/remotes/origin/HEAD').removeprefix('origin/')
    git('merge', '--ff-only', 'origin/' + branch)
    paths = []
    for name, data in images.items():
        relative = 'blog/' + name
        destination = CACHE / relative
        destination.parent.mkdir(exist_ok=True)
        destination.write_bytes(data)
        paths.append(relative)
    git('add', '--', *paths)
    if git('diff', '--cached', '--name-only'):
        git('commit', '-m', 'Add blog images')
    git('push', 'origin', branch)
    # Only rewrite links after images have been pushed successfully.
    for article, original, replacements in changes:
        updated = original
        for start, end, name in reversed(replacements):
            updated = updated[:start] + RAW + branch + '/blog/' + name + updated[end:]
        article.write_text(updated, encoding='utf-8', newline='')
        print('Updated image links:', article.name)
    print(f'Uploaded {len(images)} unique image(s) to pictureSource.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Image upload failed:', str(exc), file=sys.stderr)
        sys.exit(1)
