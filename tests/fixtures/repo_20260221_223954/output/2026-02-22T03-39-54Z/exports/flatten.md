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
