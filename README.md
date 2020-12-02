# PRISM Search

ユーザが入力した医療文書に対し，PRISMアノテーションが施された医療文書群から類似するものを提示する文書検索システム

Web-based search engine to show similar clinical documents to a user-input clinical snippet

## Requirements

- Python 3.8 (could work with 3.6+ but not tested)
- scikit-learn
- mojimoji
- [MedNER-J](https://github.com/sociocom/MedNER-J.git)
- Flask

## Installation

If you use [poetry](https://python-poetry.org), just run `poetry install`.
Otherwise, you can install the dependencies with `pip` (ver. 20.0.0+) by `pip install -r requirements.txt`.
You may want to create a virtual environment first.

You need to prepare a PRISM-annotated document source for search.
We prepared `preprocess.py` for this purpose.
Please adapt the code for the data format of your document data.
The script, `prepro.py`, is another example for PRISM's Q3 data.

After these setups completed, you should be able to run the server with `python app.py` in the Flask's development mode.

The procedure to deploy this app to a production environment depends on the web-server's setting.
Please consult with the administrators.

## Usage

1. Submit a clinical document to find relevant text thereof at `/` (root)
2. You will see an NER result of your input and its top 3-ranked "similar" documents at `/result`
3. You can modify the similarity criteria:
   - Options to calculate similarity among clinical docs
   - Clinical NE tags to consider in similarity search

## How it works

This app first apply PRISM-based clinical NER to your input document.
The NER result is used for similarity calculation with a search-source documents, which are NER-ed in advance.

The current version's similarity calculation is simply based on what-is-called "bag of named entities" (BoNE).
Like the "bag of words" (BoW), documents are vectorised into occurrence counts of the named entities appearing in the whole source.
Then, the "similarity" among documents is calculated with the cosine-similarity measure.

This similarity calculation can be regarded as a baseline for this purpose.
Further improvements could be implemented.

## Development

Developed by [Shuntaro Yada](https://shuntaroy.com) in [Social Computing Lab.](https://sociocom.naist.jp) at [NAIST](https://www.naist.jp).

## Licence

To be announced.
