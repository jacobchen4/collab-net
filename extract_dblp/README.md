# extract_dblp.py

Streams the DBLP XML dump (~4 GB) and extracts author-to-publication records for ICSA, ICSE, and ECSA conferences from 2015 onward.

## Output

`author_publications.csv` — one row per author per paper.

| Column | Description |
|---|---|
| `author` | Author name as it appears in DBLP |
| `pub_key` | DBLP record key (e.g. `conf/icse/Smith2020`) |
| `title` | Paper title |
| `year` | Publication year |
| `conference` | `ICSA`, `ICSE`, or `ECSA` |

## Requirements

- Python 3.x
- `lxml` (`pip install -r requirements.txt`)

## Setup

Place `dblp.xml` (inside a `dblp.xml/` directory) and `dblp.dtd` in the project root. The script copies the DTD next to the XML automatically for entity resolution.

```
collab-net/
├── dblp.dtd
├── dblp.xml/
│   └── dblp.xml
└── extract_dblp.py
```

## Usage

```bash
python extract_dblp.py
```
