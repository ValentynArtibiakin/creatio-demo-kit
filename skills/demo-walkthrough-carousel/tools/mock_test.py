"""Make a local test copy of a built carousel with a stand-in claude.ai runtime, to test the edit layer before publishing.

Usage:  python -I -X utf8 mock_test.py <carousel.html> <seed_dir>        (seed_dir = the seed_dir of carousel.json)
        python -I -X utf8 mock_test.py --clean <seed_dir>
Writes <seed_dir>/.test-mock.html and <seed_dir>/.mock_claude.js. Serve <seed_dir> on localhost
(python -m http.server 8765 --bind 127.0.0.1 -d <seed_dir>), open
http://localhost:8765/.test-mock.html?run=1#<ScreenWithSteps> and run tools/mock_check.js in the page: expect pass: true.
Then ?run=2&can=false (viewer: no Edit button, change stays local) and ?run=3&fail=1 (pending bar with Retry / Discard).
Use a new ?run=N each time: a hash-only change does not reload the page. Clean up afterwards with --clean.
"""
import os, shutil, sys

here = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) != 3:
    sys.exit(__doc__)
if sys.argv[1] == '--clean':
    for f in ('.test-mock.html', '.mock_claude.js'):
        fp = os.path.join(sys.argv[2], f)
        if os.path.exists(fp):
            os.remove(fp)
    print('removed test files')
    sys.exit(0)
page, seed = sys.argv[1], sys.argv[2]
if not os.path.isdir(os.path.join(seed, 'screens-seed')):
    sys.exit('%s/screens-seed not found: set "seed_dir" in carousel.json and run make_carousel.py first' % seed)
shutil.copy(os.path.join(here, 'mock_claude.js'), os.path.join(seed, '.mock_claude.js'))
html = open(page, encoding='utf-8').read()
open(os.path.join(seed, '.test-mock.html'), 'w', encoding='utf-8', newline='\n').write(
    '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    '<script src=".mock_claude.js"></script>' + html)
print('ok: %s/.test-mock.html (+ .mock_claude.js)' % seed)
