# Shared marketplace

`catalog.json` is the only authored plugin roster. Do not hand-edit either host marketplace JSON.
Run `python -B generate.py` after roster changes and `python -B generate.py --check` plus
`claude plugin validate .` before delivery. Keep existing source-repository marketplaces
available for previously installed identities.
