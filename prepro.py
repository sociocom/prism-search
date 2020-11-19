from app import xml2html, xml2bone
import json

if __name__ == "__main__":
    with open(
        "/Users/s-yada/Datasets/NAIST-SocioCom/PRISM/2019Q3_json/ncc_20191219.json"
    ) as fin:
        data = json.load(fin)

    htmls = []
    bones = []
    for d in data["読影所見"].values():
        rooted = f"<root>{content}</root>"
        htmls.append(xml2html(rooted))
        bones.append(xml2bone(rooted))

    with open("ncc1079.json", "w") as fout:
        json.dump(
            [{"html": html, "bones": bone} for html, bone in zip(htmls, bones)],
            fout,
            ensure_ascii=False,
        )
