# Auto Export: 2026-02-22T03-57-03Z

- repo_root: `C:\projects\repo-runner\tests\fixtures`
- snapshot_id: `2026-02-22T03-57-03Z`
- file_count: `14`
- tree_only: `False`
## Tree

```
└── repo_20260221_223954
    ├── frontend
    │   ├── app.tsx
    │   ├── components
    │   │   └── button.tsx
    │   └── legacy.js
    ├── output
    │   ├── 2026-02-22t03-39-54z
    │   │   ├── exports
    │   │   │   └── flatten.md
    │   │   ├── graph.json
    │   │   ├── manifest.json
    │   │   └── structure.json
    │   └── current.json
    ├── readme.md
    ├── requirements.txt
    ├── scripts
    │   └── deploy.py
    └── src
        ├── main.py
        └── utils
            ├── __init__.py
            └── logger.py
```

## File Contents

### `repo_20260221_223954/frontend/app.tsx`

```
﻿import React from 'react';
import { Button } from './components/Button';
import './styles.css';

export const App = () => <Button />;
```

### `repo_20260221_223954/frontend/components/button.tsx`

```
﻿import { useState } from 'react';
export const Button = () => <button>Click</button>;
```

### `repo_20260221_223954/frontend/legacy.js`

```
﻿const fs = require('fs');
const path = require('path');
// require('ignored');
```

### `repo_20260221_223954/output/2026-02-22t03-39-54z/exports/flatten.md`

```
# Auto Export: 2026-02-22T03-39-54Z

- repo_root: `C:\projects\repo-runner\tests\fixtures\repo_20260221_223954`
- snapshot_id: `2026-02-22T03-39-54Z`
- file_count: `9`
- tree_only: `False`
## Tree

```
├── frontend
│   ├── app.tsx
│   ├── components
│   │   └── button.tsx
│   └── legacy.js
├── readme.md
├── requirements.txt
├── scripts
│   └── deploy.py
└── src
    ├── main.py
    └── utils
        ├── __init__.py
        └── logger.py
```

## File Contents

### `frontend/app.tsx`

```
﻿import React from 'react';
import { Button } from './components/Button';
import './styles.css';

export const App = () => <Button />;
```

### `frontend/components/button.tsx`

```
﻿import { useState } from 'react';
export const Button = () => <button>Click</button>;
```

### `frontend/legacy.js`

```
﻿const fs = require('fs');
const path = require('path');
// require('ignored');
```

### `readme.md`

```
﻿# Test Repo 20260221_223954

Generated for semantic import testing.
```

### `requirements.txt`

```
﻿requests
numpy
pandas
```

### `scripts/deploy.py`

```
﻿import boto3
import json
```

### `src/main.py`

```
﻿import os
import sys
from utils.logger import log_msg

def main():
    print(os.getcwd())
    log_msg('Start')
```

### `src/utils/__init__.py`

```
﻿
```

### `src/utils/logger.py`

```
﻿import datetime
# This is a comment
def log_msg(msg):
    print(f'{datetime.datetime.now()}: {msg}')
```
```

### `repo_20260221_223954/output/2026-02-22t03-39-54z/graph.json`

```
{
  "edges": [
    {
      "relation": "imports",
      "source": "file:frontend/app.tsx",
      "target": "external:react"
    },
    {
      "relation": "imports",
      "source": "file:frontend/app.tsx",
      "target": "file:frontend/components/button.tsx"
    },
    {
      "relation": "imports",
      "source": "file:frontend/components/button.tsx",
      "target": "external:react"
    },
    {
      "relation": "imports",
      "source": "file:frontend/legacy.js",
      "target": "external:fs"
    },
    {
      "relation": "imports",
      "source": "file:frontend/legacy.js",
      "target": "external:path"
    },
    {
      "relation": "imports",
      "source": "file:scripts/deploy.py",
      "target": "external:boto3"
    },
    {
      "relation": "imports",
      "source": "file:scripts/deploy.py",
      "target": "external:json"
    },
    {
      "relation": "imports",
      "source": "file:src/main.py",
      "target": "external:os"
    },
    {
      "relation": "imports",
      "source": "file:src/main.py",
      "target": "external:sys"
    },
    {
      "relation": "imports",
      "source": "file:src/main.py",
      "target": "file:src/utils/logger.py"
    },
    {
      "relation": "imports",
      "source": "file:src/utils/logger.py",
      "target": "external:datetime"
    }
  ],
  "nodes": [
    {
      "id": "external:boto3",
      "type": "external"
    },
    {
      "id": "external:datetime",
      "type": "external"
    },
    {
      "id": "external:fs",
      "type": "external"
    },
    {
      "id": "external:json",
      "type": "external"
    },
    {
      "id": "external:os",
      "type": "external"
    },
    {
      "id": "external:path",
      "type": "external"
    },
    {
      "id": "external:react",
      "type": "external"
    },
    {
      "id": "external:sys",
      "type": "external"
    },
    {
      "id": "file:frontend/app.tsx",
      "type": "file"
    },
    {
      "id": "file:frontend/components/button.tsx",
      "type": "file"
    },
    {
      "id": "file:frontend/legacy.js",
      "type": "file"
    },
    {
      "id": "file:readme.md",
      "type": "file"
    },
    {
      "id": "file:requirements.txt",
      "type": "file"
    },
    {
      "id": "file:scripts/deploy.py",
      "type": "file"
    },
    {
      "id": "file:src/main.py",
      "type": "file"
    },
    {
      "id": "file:src/utils/__init__.py",
      "type": "file"
    },
    {
      "id": "file:src/utils/logger.py",
      "type": "file"
    }
  ],
  "schema_version": "1.0"
}
```

### `repo_20260221_223954/output/2026-02-22t03-39-54z/manifest.json`

```
{
  "config": {
    "depth": 25,
    "ignore_names": [
      ".git",
      "node_modules",
      "__pycache__",
      "dist",
      "build",
      ".next",
      ".expo",
      ".venv",
      "output"
    ],
    "include_extensions": [],
    "include_readme": true,
    "manual_override": false,
    "skip_graph": false,
    "tree_only": false
  },
  "files": [
    {
      "imports": [
        "./components/Button",
        "./styles.css",
        "react"
      ],
      "language": "typescript",
      "module_path": "frontend",
      "path": "frontend/app.tsx",
      "sha256": "c4e3f3274e7c43d41ab16610884d5b6bb58dee24e764a5ad46743661b53213bb",
      "size_bytes": 142,
      "stable_id": "file:frontend/app.tsx"
    },
    {
      "imports": [
        "react"
      ],
      "language": "typescript",
      "module_path": "frontend/components",
      "path": "frontend/components/button.tsx",
      "sha256": "e66b5591313c4a023c378a8301b8f5d4bfe93f97902f4006897253a587e59534",
      "size_bytes": 91,
      "stable_id": "file:frontend/components/button.tsx"
    },
    {
      "imports": [
        "fs",
        "path"
      ],
      "language": "javascript",
      "module_path": "frontend",
      "path": "frontend/legacy.js",
      "sha256": "6066685d1ea34d639ec83d9ef46f64a86dce63e0ee5c5126ec5da0eb143c50bd",
      "size_bytes": 85,
      "stable_id": "file:frontend/legacy.js"
    },
    {
      "imports": [],
      "language": "markdown",
      "module_path": ".",
      "path": "readme.md",
      "sha256": "b2a54c079bde2b3d7d164921f3a169f2856a486ed7dabbe59ee38f3e81873c22",
      "size_bytes": 72,
      "stable_id": "file:readme.md"
    },
    {
      "imports": [],
      "language": "unknown",
      "module_path": ".",
      "path": "requirements.txt",
      "sha256": "fa45fe2d500fbfcacd606225bcc56c4ee9f9e199dd03908ac6a323fe4e3baf54",
      "size_bytes": 26,
      "stable_id": "file:requirements.txt"
    },
    {
      "imports": [
        "boto3",
        "json"
      ],
      "language": "python",
      "module_path": "scripts",
      "path": "scripts/deploy.py",
      "sha256": "af9507ef7830ef0854f7ffe81e042d35e319e3609a33a7057c6241d51a791b47",
      "size_bytes": 30,
      "stable_id": "file:scripts/deploy.py"
    },
    {
      "imports": [
        "os",
        "sys",
        "utils.logger"
      ],
      "language": "python",
      "module_path": "src",
      "path": "src/main.py",
      "sha256": "39ed434953dad5ae0cb2f106c6a8adfafd7315cbfe1dafbc1ed26c9bc2541996",
      "size_bytes": 121,
      "stable_id": "file:src/main.py"
    },
    {
      "imports": [],
      "language": "python",
      "module_path": "src/utils",
      "path": "src/utils/__init__.py",
      "sha256": "f01a374e9c81e3db89b3a42940c4d6a5447684986a1296e42bf13f196eed6295",
      "size_bytes": 5,
      "stable_id": "file:src/utils/__init__.py"
    },
    {
      "imports": [
        "datetime"
      ],
      "language": "python",
      "module_path": "src/utils",
      "path": "src/utils/logger.py",
      "sha256": "a64e73ac733dc461d08ed36a17799d72dacc023ca64f65a8b8b40aa5cab1edee",
      "size_bytes": 108,
      "stable_id": "file:src/utils/logger.py"
    }
  ],
  "inputs": {
    "git": {
      "commit": null,
      "is_repo": false
    },
    "repo_root": "C:/projects/repo-runner/tests/fixtures/repo_20260221_223954",
    "roots": [
      "C:/projects/repo-runner/tests/fixtures/repo_20260221_223954"
    ]
  },
  "schema_version": "1.0",
  "snapshot": {
    "created_utc": "2026-02-22T03:39:54Z",
    "output_root": "tests\\fixtures\\repo_20260221_223954\\output",
    "snapshot_id": "2026-02-22T03-39-54Z"
  },
  "stats": {
    "external_dependencies": [
      "boto3",
      "datetime",
      "fs",
      "json",
      "os",
      "path",
      "react",
      "sys"
    ],
    "file_count": 9,
    "total_bytes": 680
  },
  "tool": {
    "name": "repo-runner",
    "version": "0.2.0"
  }
}
```

### `repo_20260221_223954/output/2026-02-22t03-39-54z/structure.json`

```
{
  "repo": {
    "modules": [
      {
        "files": [
          "file:readme.md",
          "file:requirements.txt"
        ],
        "path": ".",
        "stable_id": "module:."
      },
      {
        "files": [
          "file:frontend/app.tsx",
          "file:frontend/legacy.js"
        ],
        "path": "frontend",
        "stable_id": "module:frontend"
      },
      {
        "files": [
          "file:frontend/components/button.tsx"
        ],
        "path": "frontend/components",
        "stable_id": "module:frontend/components"
      },
      {
        "files": [
          "file:scripts/deploy.py"
        ],
        "path": "scripts",
        "stable_id": "module:scripts"
      },
      {
        "files": [
          "file:src/main.py"
        ],
        "path": "src",
        "stable_id": "module:src"
      },
      {
        "files": [
          "file:src/utils/__init__.py",
          "file:src/utils/logger.py"
        ],
        "path": "src/utils",
        "stable_id": "module:src/utils"
      }
    ],
    "root": ".",
    "stable_id": "repo:root"
  },
  "schema_version": "1.0"
}
```

### `repo_20260221_223954/output/current.json`

```
{
  "current_snapshot_id": "2026-02-22T03-39-54Z",
  "path": "2026-02-22T03-39-54Z",
  "schema_version": "1.0"
}
```

### `repo_20260221_223954/readme.md`

```
﻿# Test Repo 20260221_223954

Generated for semantic import testing.
```

### `repo_20260221_223954/requirements.txt`

```
﻿requests
numpy
pandas
```

### `repo_20260221_223954/scripts/deploy.py`

```
﻿import boto3
import json
```

### `repo_20260221_223954/src/main.py`

```
﻿import os
import sys
from utils.logger import log_msg

def main():
    print(os.getcwd())
    log_msg('Start')
```

### `repo_20260221_223954/src/utils/__init__.py`

```
﻿
```

### `repo_20260221_223954/src/utils/logger.py`

```
﻿import datetime
# This is a comment
def log_msg(msg):
    print(f'{datetime.datetime.now()}: {msg}')
```

---
## Context Stats
- **Total Characters:** 11,369
- **Estimated Tokens:** ~2,842 (assuming ~4 chars/token)
- **Model Fit:** GPT-4 (8k)
