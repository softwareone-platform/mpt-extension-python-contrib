# Architecture

`mpt-extension-contrib-shared` contains internal helpers reused by public
contrib packages.

The module is imported as:

```python
from mpt_extension_contrib.shared import normalize_token
```

The distribution is internal. Extension repositories should not depend on it
directly.
