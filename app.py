import json
import xml.etree.ElementTree as ET
import re

from flask import (
    Flask,
    send_from_directory,
    render_template,
    request,
    redirect,
    escape,
    Markup,
    session,
)
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import mojimoji

from medner_j import Ner

model = Ner.from_pretrained(model_name="radiology", normalizer="dict")

# to html
TAGNAMES = {
    "d": "disease",
    "a": "anatomical",
    "f": "feature",
    "c": "change",
    "TIMEX3": "TIMEX3",
    "t-test": "testtest",
    "t-key": "testkey",
    "t-val": "testval",
    "m-key": "medkey",
    "m-val": "medval",
    "cc": "cc",
    "r": "remedy",
    "p": "pending",
}

with open("ncc1079.json", "r") as fj:
    DATA = json.load(fj)

app = Flask(__name__)
app.secret_key = "Z2wwGDBrKArxXJVKZCfMQzZAqmweYEfXTg"


def e_xml2html(entity):
    attrv = entity.attrib.values()
    if len(attrv) == 1:
        entity.attrib = {"class": f"{TAGNAMES[entity.tag]}-{list(attrv)[0]}"}
    elif len(attrv) == 0:
        entity.attrib = {"class": f"{TAGNAMES[entity.tag]}"}
    else:
        entity.attrib = {"class": f"{TAGNAMES[entity.tag]} {' '.join(attrv)}"}
    entity.tag = "span"


def xml2html(doc):
    if isinstance(doc, str):
        root = ET.fromstring(doc)
    else:
        root = doc
    for entity in root.iter():
        if entity.tag == "root":
            continue
        e_xml2html(entity)
    return ET.tostring(root, encoding="unicode", method="html")


def xml2bone(doc):
    if isinstance(doc, str):
        root = ET.fromstring(doc)
    else:
        root = doc
    entities = []
    for entity in root.iter():
        if entity.tag == "root":
            continue
        entities.append(
            f"{entity.tag.replace('-', '').lower()}{''.join(v[:3] for v in entity.attrib.values())}_{entity.text}"
        )
    return " ".join(entities)


def mednerj2xml(analysed_text):
    xmldoc = f"<root>{analysed_text}</root>"
    root = ET.fromstring(xmldoc)
    for entity in root.iter():
        if entity.tag == "root":
            continue
        if "value" in entity.attrib:
            del entity.attrib["value"]

        if entity.tag == "TIMEX3DATE":
            entity.tag = "TIMEX3"
            entity.attrib["type"] = "DATE"
        elif entity.tag == "TIMEX3CC":
            entity.tag = "TIMEX3"
            entity.attrib["type"] = "CC"
        elif entity.tag == "d":
            entity.tag = "d"
        elif entity.tag == "dpositive":
            entity.tag = "d"
            entity.attrib["certainty"] = "positive"
        elif entity.tag == "dnegative":
            entity.tag = "d"
            entity.attrib["certainty"] = "negative"
        elif entity.tag == "dsuspicious":
            entity.tag = "d"
            entity.attrib["certainty"] = "suspicious"
        elif entity.tag == "mkeyexecuted":
            entity.tag = "m-key"
            entity.attrib["state"] = "executed"
        elif entity.tag == "mvalexecuted":
            entity.tag = "m-val"
            entity.attrib["state"] = "executed"
        elif entity.tag == "rexecuted":
            entity.tag = "r"
            entity.attrib["state"] = "executed"
        elif entity.tag == "ttestexecuted":
            entity.tag = "t-test"
            entity.attrib["state"] = "executed"
        elif entity.tag == "ttestother":
            entity.tag = "t-test"
            entity.attrib["state"] = "other"
        elif entity.tag == "ccother":
            entity.tag = "CC"
            entity.attrib["state"] = "other"

    return root


def analyse(text):
    text = mojimoji.han_to_zen(text)
    analysed_text = model.predict([text])
    xml = mednerj2xml(analysed_text[0])
    return xml


def filter_ne(
    boneslst,
    disease=True,
    certainty=True,
    anatomical=True,
    feature=True,
    change=True,
    t_test=True,
    t_key=True,
    t_val=True,
    m_key=True,
    m_val=True,
    remedy=True,
    state=True,
    timex3=True,
    type_=True,
    cc=True,
):
    for bones in boneslst:
        filtered = bones
        if disease is None:
            filtered = re.sub(r"d\w*_[^ ]+", "", filtered)
        if certainty is None:
            filtered = re.sub(r"d\w+_", "d_", filtered)
        if anatomical is None:
            filtered = re.sub(r"a_[^ ]+", "", filtered)
        if feature is None:
            filtered = re.sub(r"f_[^ ]+", "", filtered)
        if change is None:
            filtered = re.sub(r"c_[^ ]+", "", filtered)
        if t_test is None:
            filtered = re.sub(r"ttest\w*_[^ ]+", "", filtered)
        if t_key is None:
            filtered = re.sub(r"tkey\w*_[^ ]+", "", filtered)
        if t_val is None:
            filtered = re.sub(r"tval_[^ ]+", "", filtered)
        if m_key is None:
            filtered = re.sub(r"mkey\w*_[^ ]+", "", filtered)
        if m_val is None:
            filtered = re.sub(r"mval_[^ ]+", "", filtered)
        if remedy is None:
            filtered = re.sub(r"r\w*_[^ ]+", "", filtered)
        if state is None:
            filtered = re.sub(r"r\w+_", "r_", filtered)
            filtered = re.sub(r"cc\w+_", "cc_", filtered)
            filtered = re.sub(r"ttest\w+_", "ttest_", filtered)
            filtered = re.sub(r"tkey\w+_", "tkey_", filtered)
            filtered = re.sub(r"tval\w+_", "tval_", filtered)
            filtered = re.sub(r"mkey\w+_", "mkey_", filtered)
            filtered = re.sub(r"mval\w+_", "mval_", filtered)
        if timex3 is None:
            filtered = re.sub(r"timex3\w+_", "", filtered)
        if type_ is None:
            filtered = re.sub(r"timex3\w+_", "timex3_", filtered)
        if cc is None:
            filtered = re.sub(r"cc\w+_", "", filtered)

        yield filtered


def search(analysed_text, **kwargs):
    vec = CountVectorizer()
    bones = [d["bones"] for d in DATA]
    boneslst = [analysed_text] + bones
    bonesiter = filter_ne(boneslst, **kwargs)
    X = vec.fit_transform(bonesiter)
    mat = cosine_similarity(X[0], X[1:])  # (1, 1079)
    row = mat[0]
    ind = np.argpartition(row, -3)[-3:]  # top 3 index (rand)
    inds = ind[np.argsort(row[ind])]  # sort by values (asc)
    return [(Markup(DATA[i]["html"]), i, row[i]) for i in reversed(inds)]


# form input
@app.route("/")
def index():
    if "html" in session and "bone" in session:
        session.pop("html", None)
        session.pop("bone", None)
    # print(session)
    return send_from_directory("static", "index.html")


@app.route("/result", methods=["POST"])
def result():
    input_rr = request.form.get("radiorep")
    if input_rr:
        analysed_xml = analyse(request.form["radiorep"].strip())
        session["bone"] = xml2bone(analysed_xml)
        radiorep_ner = Markup(xml2html(analysed_xml))
        session["html"] = radiorep_ner
        results = search(session["bone"])
        return render_template(
            "result.html",
            radiorep_ner=radiorep_ner,
            results=results,
            disease=True,
            certainty=True,
            anatomical=True,
            feature=True,
            change=True,
            t_test=True,
            t_key=True,
            t_val=True,
            m_key=True,
            m_val=True,
            remedy=True,
            state=True,
            timex3=True,
            type_=True,
            cc=True,
        )
    else:
        if "html" in session and "bone" in session:
            print(request.form)
            results = search(
                session["bone"],
                disease=request.form.get("disease"),
                certainty=request.form.get("certainty"),
                anatomical=request.form.get("anatomical"),
                feature=request.form.get("feature"),
                change=request.form.get("change"),
                t_test=request.form.get("t_test"),
                t_key=request.form.get("t_key"),
                t_val=request.form.get("t_val"),
                m_key=request.form.get("m_key"),
                m_val=request.form.get("m_val"),
                remedy=request.form.get("remedy"),
                state=request.form.get("state"),
                timex3=request.form.get("timex3"),
                type_=request.form.get("type_"),
                cc=request.form.get("cc"),
            )
            return render_template(
                "result.html",
                radiorep_ner=session["html"],
                results=results,
                disease=request.form.get("disease"),
                certainty=request.form.get("certainty"),
                anatomical=request.form.get("anatomical"),
                feature=request.form.get("feature"),
                change=request.form.get("change"),
                t_test=request.form.get("t_test"),
                t_key=request.form.get("t_key"),
                t_val=request.form.get("t_val"),
                m_key=request.form.get("m_key"),
                m_val=request.form.get("m_val"),
                remedy=request.form.get("remedy"),
                state=request.form.get("state"),
                timex3=request.form.get("timex3"),
                type_=request.form.get("type_"),
                cc=request.form.get("cc"),
            )
        else:
            return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)