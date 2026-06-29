# Usage

`mpt-extension-contrib-shared` is **internal** to this repository. Extension
repositories must not depend on it directly; only other contrib packages use it,
declaring it as a workspace dependency (`{ workspace = true }`).

## Import

Helpers live under the shared namespace:

```python
from mpt_extension_contrib.shared import normalize_token
```

## Example

`normalize_token` normalizes a free-form token for comparisons — trims, lowercases,
and replaces spaces and hyphens with underscores:

```python
normalize_token("Payment-Terms 30")  # -> "payment_terms_30"
```
