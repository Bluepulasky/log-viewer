from pathlib import Path
from collections import deque
from flask import Flask, Response

app = Flask(__name__)

LOG_DIR = '/var/log/cron-jobs'
NUM_LINES = 12


def read_last_lines(filepath, n=NUM_LINES):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            return [line.rstrip() for line in deque(f, maxlen=n)]
    except PermissionError:
        return ['[Permission denied]']
    except Exception as e:
        return [f'[Error: {e}]']


def get_results():
    log_dir = Path(LOG_DIR)
    if not log_dir.exists():
        return {}
    results = {}
    for path in sorted(log_dir.rglob('*')):
        if path.is_file():
            relative = str(path.relative_to(LOG_DIR))
            lines = read_last_lines(path)
            if lines:
                results[relative] = lines
    return results


@app.route('/')
def index():
    results = get_results()

    rows = ''
    for filename, lines in results.items():
        content = '\n'.join(lines)
        rows += f'''
        <div class="log-block">
            <div class="log-filename">{filename}</div>
            <pre class="log-content">{content}</pre>
        </div>
        '''

    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  :root {{
    --bgh: 232;
    --bgs: 23%;
    --bgl: 18%;
    --color-primary: hsl(220, 83%, 75%);
    --color-positive: hsl(105, 48%, 72%);
    --color-negative: hsl(351, 74%, 73%);
  }}
  html, body {{
    background-color: hsl(var(--bgh), var(--bgs), var(--bgl)) !important;
    color: var(--color-primary) !important;
    font-family: monospace;
    font-size: 12px;
    margin: 0;
    padding: 4px;
  }}
  .log-block {{
    margin-bottom: 12px;
  }}
  .log-filename {{
    font-weight: bold;
    color: var(--color-primary);
    margin-bottom: 2px;
    border-bottom: 1px solid rgba(255,255,255,0.15);
    padding-bottom: 2px;
  }}
  .log-content {{
    margin: 0;
    white-space: pre-wrap;
    word-break: break-all;
    opacity: 0.75;
  }}
</style>
<script>
  function applyTheme(t) {{
    var root = document.documentElement;
    // store it so we can reapply if needed
    root._glanceTheme = t;

    var bgh = t.bgh;
    var bgs = t.bgs.replace('%','');
    var bgl = t.bgl.replace('%','');

    root.style.setProperty('--bgh', bgh);
    root.style.setProperty('--bgs', bgs + '%');
    root.style.setProperty('--bgl', bgl + '%');
    root.style.setProperty('--color-primary', t.primary || 'hsl(' + bgh + ',' + bgs + '%,' + (parseFloat(bgl)+50) + '%)');
    root.style.setProperty('--color-positive', t.positive);
    root.style.setProperty('--color-negative', t.negative);

    var bg = 'hsl(' + bgh + ', ' + bgs + '%, ' + bgl + '%)';
    document.documentElement.style.setProperty('background-color', bg, 'important');
    document.body.style.setProperty('background-color', bg, 'important');
  }}

  window.addEventListener('message', function(e) {{
    if (!e.data || !e.data.glanceTheme) return;
    applyTheme(e.data.glanceTheme);
  }});

  // reapply on any DOM change just in case
  new MutationObserver(function() {{
    if (document.documentElement._glanceTheme) {{
      applyTheme(document.documentElement._glanceTheme);
    }}
  }}).observe(document.documentElement, {{ attributes: true, attributeFilter: ['style'] }});
</script>
</head>
<body>
{rows if rows else '<p>No log files found.</p>'}
</body>
</html>'''

    return Response(html, mimetype='text/html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082)
