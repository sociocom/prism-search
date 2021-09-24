import json

import mojimoji
from medner_j import Ner
from textformatting import ssplit

from app import xml2html, xml2bone, mednerj2xml

model = Ner.from_pretrained(model_name="radiology", normalizer="dict")


def main(docs):
    """Convert a list of documents to a JSON-formated search source

    Args:
        docs (list[str]): a list of documents
    Return:
        None
    Side effect:
        Write a file named "search_source.json".
        This JSON is a list of document objects, each of which contains an html-formated clinical text (as string) and a bag of named entities (as space-separated string).
    """
    htmls = []
    bones = []
    for d in docs:
        d = mojimoji.han_to_zen(d)
        sentences = ssplit(d)
        ner_sents = model.predict(sentences)
        xml = mednerj2xml("".join(ner_sents))
        htmls.append(xml2html(xml))
        bones.append(xml2bone(xml))

    with open("search_source.json", "w") as fout:
        json.dump(
            [{"html": html, "bones": bone} for html, bone in zip(htmls, bones)],
            fout,
            ensure_ascii=False,
        )
