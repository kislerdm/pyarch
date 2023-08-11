#!/usr/bin/env python3

"""
pyarch: generates HTML with dynamic classDiagram based on the pyreverse PUML DSL.

Ref:
- https://www.bhavaniravi.com/python/generate-uml-diagrams-from-python-code
- https://mermaid.js.org/syntax/classDiagram.html

Usage example:

cd superduperdb
pyreverse -Akmy -o puml .
./main.py --classes classes.puml --packages packages.puml --output index.html
"""
import argparse
import dataclasses
import json
from typing import List, Dict


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

    def __eq__(self, other: "Link") -> bool:
        return self.start == other.start \
            and self.end == other.end \
            and self.arrow == other.arrow \
            and self.description == other.description

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
        """ Creates a new Node object given its id.

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

    def __eq__(self, other: "Node") -> bool:
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


def generate_html(nodes: Nodes, links: Links) -> str:
    """ Generates HTML file.

    Args:
        nodes: Nodes object to generate diagrams.
        links: Links to connect nodes.

    Returns:
        HTML string.
    """
    template = """<!DOCUMENT>
<html lang="en">
<head>
    <title>Package architecture</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta charset="UTF-8">
    <style>:root{font-family:Inter,system-ui,Avenir,Helvetica,Arial,sans-serif;line-height:1.5;font-weight:400;--code-bg:rgb(245, 245, 245);background:var(--code-bg);font-synthesis:none;text-rendering:optimizeLegibility;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;-webkit-text-size-adjust:100%}.alert {color:red;font-size:25px;text-align:center}* {box-sizing:border-box}.column {float:left;border:#000 2px solid;border-radius:20px;height:85vh;margin:0 .25vw 0}.left {width:25vw;padding:10px}.right {padding:0;width:73vw}.row:after {display:table;clear:both}#lab-input {display:block;text-align:center;vertical-align:center;margin-top:-10px;font-size:20pt}@media only screen and (max-width:1600px) {.left, .right {width:95vw}.right {height:73vh;margin-top:1vh}.left {height:6vh}#input {width:0}p#diagram-title {transform:translate(-50%, 50%);font-size:15pt;text-align:center}.header {font-size:1rem}}.header {font-size:2rem}.tree-panel {height:95%;width:100%;overflow:scroll;float:right}#input::-webkit-scrollbar {width:10px;height:10px}.force-overflow {min-height:100px}#input::-webkit-scrollbar-thumb {background:#7f7f7f;border:2px #000 solid;border-radius:5px;margin-bottom:10px}.tree-panel ul {list-style-type:none}.tree-panel .caret, .tree-panel .custom-control-input {cursor:pointer;user-select:none}.tree-panel .collapsed {display:none}.caret {font-style:normal;font-size:20px;margin-right:10px}.minimize:before {content:"-";margin-right:3px}.maximize:before {content:"+"}.fixed:before {content:"*";margin-right:15px}#output {height:100%;align-content:center;margin:0}#diagram {max-width:none !important;width:100%;height:100%}footer {text-align:center;padding:1rem }a {color:#000}a:link {text-decoration:none}a:visited {text-decoration:none}a:hover {text-decoration:none}a:active {text-decoration:none}header {font-size:30px;font-weight:bold;text-align:center;margin-bottom:10px}#diagram-title{position:absolute;font-size:20pt;text-align:center;left:50%;transform:translate(0%,50%)}p.info,ul.info{text-align:left;font-size:1rem;font-weight:300}ul.info{list-style-type:decimal}</style>
</head>

<body>
<header>
    <div class="header">Python package architecture</div>
</header>
<div id="tree"></div>
<div class="row">
    <div class="column left" id="in_col"><label id="lab-input" for="input">Select node</label>
        <div id="input" class="tree-panel"></div>
    </div>
    <div class="column right" id="out_col">
        <div id="output"></div>
    </div>
</div>
<footer>
    <p style="font-size:15px">Generated by <a href="https://github.com/kislerdm/pyarch" target="_blank">pyarch</a></p>
    <p style="font-size:15px">Built with ❤️ by <a href="https://www.dkisler.com" target="_blank">Dmitry Kisler - dkisler.com</a></p>
</footer>

<script type="module">
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

    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
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
</script>

</body>
</html>
"""
    return template \
        .replace("{{.Nodes}}", nodes.to_json()) \
        .replace("{{.Links}}", links.to_json())


def main(puml_packages: str, puml_classes: str) -> str:
    """ Main runner.

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

    return generate_html(nodes, links_deduplicated)


def get_args() -> argparse.Namespace:
    """ Parses stdin arguments. """
    parser = argparse.ArgumentParser(prog="pyarch", usage="""pyarch: generates HTML with dynamic classDiagram based on the pyreverse PUML DSL.

Ref:
- https://www.bhavaniravi.com/python/generate-uml-diagrams-from-python-code
- https://mermaid.js.org/syntax/classDiagram.html

Usage example:

cd superduperdb
pyreverse -Akmy --colorized --max-color-depth 10 -o puml .
./main.py --classes classes.puml --packages packages.puml --output index.html""")
    parser.add_argument("-p", "--packages", required=True, help="Path to packages.puml file.")
    parser.add_argument("-c", "--classes", required=True, help="Path to classess.puml file.")
    parser.add_argument("-o", "--output", required=True, help="Path to output html file.")
    return parser.parse_args()


if __name__ == "__main__":
    # args = get_args()
    class Args:
        packages: str = ""
        classes: str = ""
        output: str = ""


    args = Args()

    args.packages = "/Users/dkisler/projects/python-pkg-architecture/packages.puml"
    args.classes = "/Users/dkisler/projects/python-pkg-architecture/classes.puml"
    args.output = "/Users/dkisler/projects/python-pkg-architecture/index.html"

    with open(args.packages, "r") as fin:
        puml_packages = fin.read()

    with open(args.classes, "r") as fin:
        puml_classes = fin.read()

    html = main(puml_packages=puml_packages, puml_classes=puml_classes)

    with open(args.output, "w") as fout:
        fout.write(html)


def test_Node_from_str():
    tests = [
        {
            "input": "superduperdb.container.artifact.Artifact",
            "want": Node("superduperdb", "superduperdb", Nodes([
                Node("superduperdb.container", "container", Nodes([
                    Node("superduperdb.container.artifact", "artifact", Nodes([
                        Node("superduperdb.container.artifact.Artifact", "Artifact", Nodes([])),
                    ])),
                ])),
            ])),
        },
        {
            "input": "superduperdb",
            "want": Node("superduperdb", "superduperdb", Nodes([])),
        },
        {
            "input": "",
            "want": Node("", "", Nodes([])),
        },
        {
            "input": "foo.bar.",
            "want": Node("foo", "foo", Nodes([Node("foo.bar", "bar", Nodes([Node("foo.bar.", "", Nodes([])), ])), ])),
        },
        {
            "input": ".",
            "want": Node("", "", Nodes([Node(".", "", Nodes([])), ])),
        },
    ]
    for test in tests:
        assert Node.from_str(test["input"]) == test["want"]


def test_Nodes_to_json():
    tests = [
        {
            "input": Nodes([Node("foo", "foo", Nodes([]))]),
            "want": """[{"id": "foo", "name": "foo", "nodes": []}]"""
        },
        {
            "input": Nodes([
                Node("foo", "foo", Nodes([
                    Node("foo.bar", "bar", Nodes([
                        Node("foo.bar.qux", "qux", Nodes([])),
                        Node("foo.bar.quxx", "quxx", Nodes([])),
                    ])),
                    Node("foo.baz", "baz", Nodes([])),
                ]))
            ]),
            "want": """[{"id": "foo", "name": "foo", "nodes": [{"id": "foo.bar", "name": "bar", "nodes": [{"id": "foo.bar.qux", "name": "qux", "nodes": []}, {"id": "foo.bar.quxx", "name": "quxx", "nodes": []}]}, {"id": "foo.baz", "name": "baz", "nodes": []}]}]"""
        },
    ]
    for test in tests:
        assert test["input"].to_json() == test["want"]


def test_Nodes_add():
    tests = [
        {
            "given": Nodes([Node("foo", "foo", Nodes([]))]),
            "input": [
                Node("foo", "foo", Nodes([
                    Node("foo.bar", "foo", Nodes([]))
                ])),
            ],
            "want": Nodes([Node("foo", "foo", Nodes([Node("foo.bar", "foo", Nodes([]))]))]),
        },
        {
            "given": Nodes([Node("foo", "foo", Nodes([]))]),
            "input": [Node("bar", "bar", Nodes([]))],
            "want": Nodes([Node("foo", "foo", Nodes([])), Node("bar", "bar", Nodes([]))]),
        },
        {
            "given": Nodes([]),
            "input": [
                Node.from_str("superduperdb.base.config.Notebook"),
                Node.from_str("superduperdb.data.cache.key_cache"),
            ],
            "want": Nodes([
                Node(id="superduperdb", name="superduperdb",
                     nodes=Nodes([
                         Node(id="superduperdb.base",
                              name="base",
                              nodes=Nodes([
                                  Node(id="superduperdb.base.config",
                                       name="config",
                                       nodes=Nodes([
                                           Node(id="superduperdb.base.config.Notebook",
                                                name="Notebook",
                                                nodes=Nodes([])
                                                ),
                                       ])),
                              ])
                              ),
                         Node(id="superduperdb.data",
                              name="data",
                              nodes=Nodes([
                                  Node(id="superduperdb.data.cache",
                                       name="cache",
                                       nodes=Nodes([
                                           Node(id="superduperdb.data.cache.key_cache",
                                                name="key_cache",
                                                nodes=Nodes([])),
                                       ])
                                       ),
                              ])
                              ),
                     ])
                     ),
            ]),
        },
    ]
    for test in tests:
        for other in test["input"]:
            test["given"].add(other)
        assert test["given"] == test["want"]


def test_Node_parent_id():
    tests = [
        {
            "node": Node("foo", "foo", Nodes([])),
            "want": "",
        },
        {
            "node": Node("foo.bar.qux", "qux", Nodes([])),
            "want": "foo.bar",
        },
    ]
    for test in tests:
        assert test["node"].parent_id() == test["want"]


def test_Links_to_json():
    tests = [
        {
            "input": Links([Link(
                "superduperdb.container.artifact.Artifact --* superduperdb.ext.torch.model.TorchTrainerConfiguration : optimizer_cls")]),
            "want": """[{"start": "superduperdb.container.artifact.Artifact", "end": "superduperdb.ext.torch.model.TorchTrainerConfiguration", "arrow": "--*", "description": "optimizer_cls"}]""",
        },
        {
            "input": Links([Link(
                "superduperdb.container.artifact.Artifact --* superduperdb.ext.torch.model.TorchTrainerConfiguration")]),
            "want": """[{"start": "superduperdb.container.artifact.Artifact", "end": "superduperdb.ext.torch.model.TorchTrainerConfiguration", "arrow": "--*", "description": ""}]""",
        },
    ]
    for test in tests:
        assert test["input"].to_json() == test["want"]


def test_Links_deduplicate():
    tests = [
        {
            "input": Links([
                Link("foo --* bar : qux"),
                Link("foo --* bar : quxx"),
                Link("foo --* bar : qux"),
                Link("foo --* bar : quxx"),
                Link("foo --* bar : quxx1"),
                Link("foo --* bar : quxx"),
            ]),
            "want": 3,
        }
    ]
    for test in tests:
        assert len(test["input"].deduplicate()) == test["want"]
