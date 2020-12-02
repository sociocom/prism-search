import json

import mojimoji
from medner_j import Ner

from app import xml2html, xml2bone, mednerj2xml

model = Ner.from_pretrained(model_name="radiology", normalizer="dict")


def main(docs):
    """Convert a list of documents to a JSON-formated search source

    Args:
        docs (list[str]): a list of documents
    """
    htmls = []
    bones = []
    for d in docs:
        d = mojimoji.han_to_zen(d)
        d_ = model.predict([d])
        xml = mednerj2xml(d_[0])
        htmls.append(xml2html(xml))
        bones.append(xml2bone(xml))

    with open("search_source.json", "w") as fout:
        json.dump(
            [{"html": html, "bones": bone} for html, bone in zip(htmls, bones)],
            fout,
            ensure_ascii=False,
        )
