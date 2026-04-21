from pathlib import Path
from collections import deque
from flask import Flask, Response

app = Flask(__name__)

LOG_DIRS = [
    '/var/log/cron-jobs',
    '/var/log/cobian-logs'
]

NUM_LINES = 18


def read_last_lines(filepath, n=NUM_LINES):
    for enc in ["utf-8", "utf-16", "latin-1"]:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                return [line.rstrip() for line in deque(f, maxlen=n)]
        except UnicodeError:
            continue
        except PermissionError:
            return ['[Permission denied]']
        except Exception as e:
            return [f'[Error: {e}]']


def get_results():
    results = {}
    for log_dir_str in LOG_DIRS:
        log_dir = Path(log_dir_str)
        if not log_dir.exists():
            continue

        # Para cobian-logs, solo el archivo más reciente
        if 'cobian' in log_dir_str:
            files = [p for p in log_dir.rglob('*') if p.is_file() and '.stfolder' not in p.parts]
            if files:
                latest = max(files, key=lambda p: p.stat().st_mtime)
                relative = f"{log_dir.name}/{latest.relative_to(log_dir)}"
                lines = read_last_lines(latest)
                if lines:
                    results[relative] = lines
            continue

        # Para el resto, todos los archivos
        for path in sorted(log_dir.rglob('*')):
            if '.stfolder' in path.parts:
                continue
            if path.is_file():
                relative = f"{log_dir.name}/{path.relative_to(log_dir)}"
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
            <div class="log-filename" style="font-weight: 500;">{filename}</div>
            <pre class="log-content">{content}</pre>
        </div>
        '''

    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500&amp;display=swap" rel="stylesheet">
<style>
  html, body {{ margin: 0; height: fit-content; background-color: hsl(232, 23%, 18%) !important; font-family: 'Inter', sans-serif; scrollbar-color: #525984 #232638;}}
  p {{ margin: 3px 0; }}
  canvas {{ width: 100% !important; }}
  * {{
    -webkit-user-select: none;
    user-select: none;
    -webkit-touch-callout: none;
  }}
  .log-block {{
    margin-bottom: 12px;
  }}
  .log-filename {{
    font-size: 13px; 
    color: #ffffff;
    margin-bottom: 2px;
    border-bottom: 1px solid rgba(255,255,255,0.15);
    padding-bottom: 2px;
  }}
  .log-content {{
    margin: 0;
    font-size: 11px; 
    color: #7B99D7;
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
<div style="background: rgba(37,40,60,1); border: 1px solid hsl(232, 23%, 22%); box-shadow: 0px 3px 0px 0px hsl(232, 23%, 18%); border-radius: 8px; padding: 16px 16px;">
{rows if rows else '<p>No log files found.</p>'}
</div>
</body>
</html>'''

    return Response(html, mimetype='text/html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082)
