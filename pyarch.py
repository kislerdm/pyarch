#!/usr/bin/env python3

"""
pyarch: generates HTML with dynamic classDiagram based on the pyreverse PUML DSL.

Ref:
- https://www.bhavaniravi.com/python/generate-uml-diagrams-from-python-code
- https://mermaid.js.org/syntax/classDiagram.html

Usage example:

cd superduperdb
pyreverse -Akmy -o puml .
./pyarch.py --output index.html --input .
"""
import argparse
import dataclasses
import json
import logging
import os.path
import sys
from typing import Dict, List


class Link:
    def __init__(self, dsl_puml: str) -> None:
        o = dsl_puml.split(" ")

        if len(o) != 3 and len(o) != 5:
            raise ValueError("input is not compliant with the PlantUML DSL")

        self.start: str = o[0]
        self.end: str = o[2]
        self.arrow: str = o[1]

        self.description: str = ""
        if len(o) == 5:
            self.description = o[4]

    def __eq__(self, other: "Link") -> bool:  # type: ignore
        return (
                self.start == other.start
                and self.end == other.end
                and self.arrow == other.arrow
                and self.description == other.description
        )

    def to_dict(self) -> Dict[str, str]:
        return {
            "start": self.start,
            "end": self.end,
            "arrow": self.arrow,
            "description": self.description,
        }


class Links(List[Link]):
    def to_json(self) -> str:
        return json.dumps([el.to_dict() for el in self])

    def deduplicate(self) -> "Links":
        if len(self) == 0:
            return Links([])

        o = [self[0]]

        for el in self[1:]:
            if len({None for i in o if i == el}) == 0:
                o.append(el)

        return Links(o)

    def get_nodes(self) -> "Nodes":
        ids = []  # type: ignore
        for link in self:
            ids.append(link.start)
            ids.append(link.end)

        ids_set = set(ids)

        o = Nodes()
        for _id in ids_set:
            node = Node.from_str(_id)
            o.add(node)

        return o


@dataclasses.dataclass
class Node:
    id: str
    name: str
    nodes: "Nodes"

    _SEPARATOR = "."

    @staticmethod
    def from_str(id: str) -> "Node":
        """Creates a new Node object given its id.

        Args:
            id: Node's id string.

        Returns:
            Node object.
        """
        node_names = id.split(Node._SEPARATOR)[-1::-1]
        node = Node(id, node_names[0], Nodes([]))

        i = 1
        while i < len(node_names):
            node_id = Node._SEPARATOR.join(node_names[i:][-1::-1])
            node = Node(node_id, node_names[i], Nodes([node]))
            i += 1

        return node

    def __eq__(self, other: "Node") -> bool:  # type: ignore
        flag = self.id == other.id and self.name == self.name and len(self.nodes) == len(other.nodes)
        if not flag:
            return False

        for l, r in zip(self.nodes, other.nodes):
            if l != r:
                return False

        return True

    def parent_id(self) -> str:
        return Node._SEPARATOR.join(self.id.split(Node._SEPARATOR)[:-1])


class Nodes(List["Node"]):
    def add(self, other: "Node"):
        root_found = False
        for node in self:
            if node.parent_id() == other.parent_id() and node.id == other.id:
                root_found = True
                for child in other.nodes:
                    node.nodes.add(child)
                break
        if not root_found:
            self.append(other)

    def to_json(self) -> str:
        return json.dumps([dataclasses.asdict(el) for el in self])


def _is_relation(el: str) -> bool:
    return " --" in el


def generate_js(nodes: Nodes, links: Links) -> str:
    """Generates JS file.

    Args:
        nodes: Nodes object to generate diagrams.
        links: Links to connect nodes.

    Returns:
        JS string.
    """
    template = """import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
mermaid.initialize({
    theme: "default",
    dompurifyConfig: {
        USE_PROFILES: {
            svg: true,
        },
    },
    startOnLoad: true,
    htmlLabels: true,
    c4: {
        diagramMarginY: 0,
    }
})

const nodes = {{.Nodes}};
const links = {{.Links}};

function selectLinks(id) {
    const o = links.filter(link => link["start"] === id || link["end"] === id);
    if (o.length === 0) {
        return links.filter(link => link["start"].startsWith(id) || link["end"].startsWith(id));
    }
    return o;
}

function convertID(s) {
    return s.replaceAll(".", "-")
}

function generateDiagram(id) {
    const l = selectLinks(id);

    let o = `classDiagram
`;

    for (const link of l) {
        o+= `${convertID(link["start"])} ${link["arrow"]} ${convertID(link["end"])}`
        if (link["description"] !== undefined && link["description"] !== "") {
            o += ` : ${link["description"]}`
        }
        o += `
`
    }

    return o
}

const inputSelectedIdStyle = "font-weight:bold;font-size:18px";

function generateList(nodes, selected_id) {
    if (nodes.length === 0) {
        return ""
    }

    let o = "<ul>";

    for (const node of nodes) {
        const checked = node["id"] === selected_id ? `style=${inputSelectedIdStyle}` : "";
        const listRow = `<span class="custom-control-input" id="${node["id"]}" ${checked}>${node["name"]}</span>`;
        const dropDownSelection = `<span class="caret minimize"></span>`;

        if (node["nodes"] !== undefined && node["nodes"].length > 0) {
            o += `<li>${dropDownSelection}${listRow}${generateList(node["nodes"], selected_id)}</li>`
        } else {
            o += `<li><span class="fixed"></span>${listRow}</li>`
        }
    }

    return `${o}</ul>`
}

const id = nodes[0].id;
let prevSelectedId = id;

const inputElements = document.getElementsByClassName("custom-control-input");
const carets = document.getElementsByClassName('caret');
const out = document.getElementById("output");

document.addEventListener("DOMContentLoaded", async function () {
    const el = document.getElementById("input");
    el.innerHTML = `<div class="force-overflow"><form class="tree" id="intputForm">${generateList(nodes, id)}</form></div>`;

    const {svg} = await mermaid.render("diagram", generateDiagram(id), out);
    out.innerHTML = svg;

    for (const caret of carets) {
        caret.addEventListener('click', () => {
            caret.parentElement.querySelector('ul').classList.toggle('collapsed');
            caret.classList.toggle('maximize');
            caret.classList.toggle('minimize');
        });
    }

    for (const elInput of inputElements) {
        elInput.addEventListener("click", async (e) => {
            const id = e.target.id
            try {
                const shown = generateDiagram(id);
                console.log(shown);
                const {svg} = await mermaid.render("diagram", shown, out);
                out.innerHTML = svg;
            } catch (err) {
                console.error(err.message);
            }

            resetDefaultStyleInputElement(prevSelectedId);
            elInput.setAttribute("style", inputSelectedIdStyle);
            prevSelectedId = id;

            if (isMobileDevice()) {
                hideInputPanel();
                isClickedSelectorLabel = false;
            }
        })
    }

});

function resetDefaultStyleInputElement(id) {
    for (const el of inputElements) {
        if (el.id === id) {
            el.setAttribute("style", "")
        }
    }
}

// drop-down input to adopt for mobile devices
let isClickedSelectorLabel = false;
const selectorLabel = document.getElementById("lab-input");
selectorLabel.addEventListener("click", () => {
    if (isMobileDevice()) {
        if (isClickedSelectorLabel) {
            hideInputPanel()
            isClickedSelectorLabel = false;
        } else {
            showInputPanel();
            isClickedSelectorLabel = true;
        }
    }
})

function showInputPanel() {
    const inputPanel = document.getElementById("in_col");
    inputPanel.setAttribute("style", "height:70vh");
    const inputTree = document.getElementById("input");
    inputTree.setAttribute("style", "width:100%")
}

function hideInputPanel() {
    const inputPanel = document.getElementById("in_col");
    inputPanel.setAttribute("style", `height:6vh`);
    const inputTree = document.getElementById("input");
    inputTree.setAttribute("style", "width:0")
}

function isMobileDevice() {
    return window.screen.availWidth <= 1600
}
"""

    return template.replace("{{.Nodes}}", nodes.to_json()).replace("{{.Links}}", links.to_json())


_HTML = """<!DOCUMENT><html lang="en"><head> <title>Package architecture</title> <meta name="viewport" content="width=device-width, initial-scale=1.0"> <meta charset="UTF-8"> <style>:root{font-family:Inter,system-ui,Avenir,Helvetica,Arial,sans-serif;line-height:1.5;font-weight:400;--code-bg:rgb(245, 245, 245);background:var(--code-bg);font-synthesis:none;text-rendering:optimizeLegibility;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;-webkit-text-size-adjust:100%}.alert{color:red;font-size:25px;text-align:center}*{box-sizing:border-box}.column{float:left;border:#000 2px solid;border-radius:20px;height:85vh;margin:0 .25vw 0}.left{width:25vw;padding:10px}.right{padding:0;width:73vw}.row:after{display:table;clear:both}#lab-input{display:block;text-align:center;vertical-align:center;margin-top:-10px;font-size:20pt}@media only screen and (max-width:1600px){.left, .right{width:95vw}.right{height:73vh;margin-top:1vh}.left{height:6vh}#input{width:0}p#diagram-title{transform:translate(-50%, 50%);font-size:15pt;text-align:center}.header{font-size:1rem}}.header{font-size:2rem}.tree-panel{height:95%;width:100%;overflow:scroll;float:right}#input::-webkit-scrollbar{width:10px;height:10px}.force-overflow{min-height:100px}#input::-webkit-scrollbar-thumb{background:#7f7f7f;border:2px #000 solid;border-radius:5px;margin-bottom:10px}.tree-panel ul{list-style-type:none}.tree-panel .caret, .tree-panel .custom-control-input{cursor:pointer;user-select:none}.tree-panel .collapsed{display:none}.caret{font-style:normal;font-size:20px;margin-right:10px}.minimize:before{content:"-";margin-right:3px}.maximize:before{content:"+"}.fixed:before{content:"*";margin-right:15px}#output{height:100%;align-content:center;margin:0}#diagram{max-width:none !important;width:100%;height:100%}footer{text-align:center;padding:1rem}a{color:#000}a:link{text-decoration:none}a:visited{text-decoration:none}a:hover{text-decoration:none}a:active{text-decoration:none}header{font-size:30px;font-weight:bold;text-align:center;margin-bottom:10px}#diagram-title{position:absolute;font-size:20pt;text-align:center;left:50%;transform:translate(0%,50%)}p.info,ul.info{text-align:left;font-size:1rem;font-weight:300}ul.info{list-style-type:decimal}</style></head><body><header> <div class="header">Python package architecture</div></header><div id="tree"></div><div class="row"> <div class="column left" id="in_col"><label id="lab-input" for="input">Select node</label> <div id="input" class="tree-panel"></div></div><div class="column right" id="out_col"> <div id="output"></div></div></div><footer> <p style="font-size:15px">Generated by <a href="https://github.com/kislerdm/pyarch" target="_blank">pyarch</a></p><p style="font-size:15px">Built with ❤️ by <a href="https://www.dkisler.com" target="_blank">Dmitry Kisler - dkisler.com</a></p></footer><script type="module" src="./index.js"></script></body></html>"""


def main(puml_packages: str, puml_classes: str) -> str:
    """Main runner.

    Args:
        puml_packages: PUML DSL definition packages relations.
        puml_classes: PUML DSL definition classes relations.

    Returns:
        HTML page.
    """
    links: Links = Links([])

    dsl_puml = [*puml_packages.split("\n"), *puml_classes.split("\n")]

    for line in dsl_puml:
        if _is_relation(line):
            links.append(Link(line))

    links_deduplicated = links.deduplicate()
    nodes = links_deduplicated.get_nodes()

    return generate_js(nodes, links_deduplicated)


def get_args() -> argparse.Namespace:
    """Parses stdin arguments."""
    parser = argparse.ArgumentParser(
        prog="pyarch",
        usage="""pyarch: generates HTML with dynamic classDiagram based on the pyreverse PUML DSL.

Ref:
- https://www.bhavaniravi.com/python/generate-uml-diagrams-from-python-code
- https://mermaid.js.org/syntax/classDiagram.html

Usage example:

cd superduperdb
pyreverse -Akmy -o puml .
./pyarch.py --input . --output index.html""",
    )
    parser.add_argument("-i", "--input", required=True, type=str, help="Directory with {classes,packages}.puml files.")
    parser.add_argument("-o", "--output", required=True, type=str, help="Directory to output index.html file.")
    parser.add_argument("-v", "--verbose", required=False, default=False, action="store_true", help="Verbosity.")
    return parser.parse_args()


logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)
_LOGS = logging.getLogger("pyarch")


def read_input_puml(path: str) -> str:
    """Reads input file.

    Args:
        path: Path to file.

    Returns:
        File content.

    Raises:
        FileNotFoundError: raised when the file is not found.
        IOError: raised upon reading error.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError("file %s not found" % path)

    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as ex:
        raise IOError(ex) from ex


if __name__ == "__main__":
    args = get_args()

    path_classes_puml = f"{args.input}/classes.puml"
    path_packages_puml = f"{args.input}/packages.puml"

    puml_packages: str = ""
    puml_classes: str = ""

    if args.verbose:
        _LOGS.info("reading %s" % path_classes_puml)
    try:
        puml_classes = read_input_puml(path_classes_puml)
    except FileNotFoundError as ex:
        _LOGS.warning(ex)
    except IOError as ex:
        _LOGS.error(ex)
        sys.exit(1)

    if args.verbose:
        _LOGS.info("reading %s" % path_packages_puml)
    try:
        puml_packages = read_input_puml(path_packages_puml)
    except FileNotFoundError as ex:
        _LOGS.warning(ex)
    except IOError as ex:
        _LOGS.error(ex)
        sys.exit(1)

    if puml_classes == "" and puml_packages == "":
        _LOGS.error("no required inputs found")
        sys.exit(1)

    if args.verbose:
        _LOGS.info("generating report files")

    js = main(puml_packages=puml_packages, puml_classes=puml_classes)

    if args.verbose:
        _LOGS.info("writing %s" % f"{args.output}/index.js")

    with open(f"{args.output}/index.js", "w") as fout:
        fout.write(js)

    if args.verbose:
        _LOGS.info("writing %s" % f"{args.output}/index.html")

    with open(f"{args.output}/index.html", "w") as fout:
        fout.write(_HTML)
