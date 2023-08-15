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
        if len(self) < 2:
            return self

        o = [self[0]]

        for el in self[1:]:
            if len({None for i in o if i == el}) == 0:
                o.append(el)

        return Links(o)

    def get_nodes(self) -> "Nodes":
        ids = set()
        for link in self:
            ids.add(link.start)
            ids.add(link.end)

        o = Nodes()
        for _id in ids:
            o.add(Node.from_str(_id))

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


@dataclasses.dataclass
class WebpageConfig:
    title: str = "Python package architecture"
    header: str = "Python package architecture"
    footer: str = """<p style="font-size:15px">Built with ❤️ by <a href=https://www.dkisler.com target=_blank>Dmitry Kisler - dkisler.com</a></p>"""


@dataclasses.dataclass
class WebpageGenerator:
    nodes: Nodes
    links: Links
    cfg: WebpageConfig

    def __call__(self) -> str:
        """ Creates the webpage with architecture details. """

        template = """<!doctypehtml><html lang=en><title>{{.Title}}</title><meta content="width=device-width,initial-scale=1"name=viewport><meta charset=UTF-8><script src=https://cdn.jsdelivr.net/npm/mermaid@10.3.1/dist/mermaid.min.js></script><style>:root{font-family:Inter,system-ui,Avenir,Helvetica,Arial,sans-serif;line-height:1.5;font-weight:400;--code-bg:rgb(245, 245, 245);background:var(--code-bg);font-synthesis:none;text-rendering:optimizeLegibility;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;-webkit-text-size-adjust:100%}body,html{height:100%;width:100%;background:var(--code-bg)}.alert{color:red;font-size:25px}*{box-sizing:border-box}.column{float:left;border:2px solid #000;border-radius:20px;height:85vh;margin:0 .25vw}.left{width:25vw;padding:10px}.right{padding:0;width:73vw}.row:after{display:table;clear:both}#lab-input{display:block;vertical-align:center;horiz-align:center}@media only screen and (max-width:1600px){.left,.right{width:95vw}.right{height:73vh;margin-top:1vh}.left{height:6vh}#input{width:0}header{font-size:1rem}#selector-btn{display:none}.tree{height:90%}}.tree{width:100%;height:80%;overflow:scroll}.tree::-webkit-scrollbar{width:10px;height:fit-content}.tree::-webkit-scrollbar-thumb{background:#7f7f7f;border:2px solid #000;border-radius:5px}.tree-panel{height:100%;width:100%}.tree-panel ul{list-style-type:none}.tree-panel .caret,.tree-panel .custom-control-input{cursor:pointer;user-select:none}.tree-panel .collapsed{display:none}.caret{font-style:normal;font-size:20px;margin-right:10px}.minimize:before{content:"-";margin-right:3px}.maximize:before{content:"+"}.fixed:before{content:"*";margin-right:15px}#output{height:100%;align-content:center;margin:0}#diagram{max-width:none!important;width:100%;height:100%}footer{padding:1rem}a{color:#000}a:active,a:hover,a:link,a:visited{text-decoration:none}header{font-size:2rem;font-weight:700;margin-bottom:10px}#diagram-title{position:absolute;left:50%;transform:translate(0,50%)}p.info,ul.info{text-align:left;font-size:1rem;font-weight:300}ul.info{list-style-type:decimal}.container{display:flex;justify-content:space-evenly}#diagram-title,#lab-input{font-size:20pt;text-align:center}#diagram-title,#lab-input,.alert,footer,header{text-align:center}</style><header>{{.Header}}</header><div class=row><div class="column left"id=in_col><label for=input id=lab-input>Select node</label><div id=selector-btn><hr><div class=container><button id=expand-all>Expand All</button> <button id=collapse-all>Collapse All</button></div><hr></div><div class=tree-panel id=input></div></div><div class="column right"id=out_col><div id=output></div></div></div><footer><p style=font-size:15px>Generated by <a href=https://github.com/kislerdm/pyarch target=_blank>pyarch</a></p>{{.Footer}}</footer><script>const nodes={{.Nodes}},links={{.Links}};mermaid.initialize({theme:"default",dompurifyConfig:{USE_PROFILES:{svg:!0}},startOnLoad:!0,htmlLabels:!0,c4:{diagramMarginY:0}});class Router{#a;#b;#c;#d="q";constructor(){this.#b=window.location,this.#a=window.history,this.#c=this.#e(this.#f()[0])}updateRouteToNode(e){this.#a.pushState({},"",`${this.#c}?${this.#d}=${e}`)}readNodeIDFromRoute(){let e=this.#f();return e.length<2?"":e[1]}#f(){return this.#b.href.split(`${this.#d}=`)}#e(e){let t=e.slice(-1);return"?"!==t&&"/"!==t?e:this.#e(e.slice(0,-1))}}function selectLinks(e){let t=links.filter(t=>t.start===e||t.end===e);return 0===t.length?links.filter(t=>t.start.startsWith(e)||t.end.startsWith(e)):t}function convertID(e){return e.replaceAll(".","-")}function generateDiagram(e){let t=selectLinks(e);if(0===t.length)return"";let l=`classDiagram
`;for(let i of t)l+=`${convertID(i.start)} ${i.arrow} ${convertID(i.end)}`,void 0!==i.description&&""!==i.description&&(l+=` : ${i.description}`),l+=`
`;return l}const inputSelectedIdStyle="font-weight:bold;font-size:18px";function generateListDepth(e,t,l,i){if(0===e.length)return"";let n=l<i?"<ul>":'<ul class="collapsed">',s=l<i-1?"minimize":"maximize";for(let r of e){let a=r.id===t?`style=${inputSelectedIdStyle}`:"",o=`<span class="custom-control-input" id="${r.id}" ${a}>${r.name}</span>`,c=`<span class="caret ${s}"></span>`;void 0!==r.nodes&&r.nodes.length>0?n+=`<li>${c}${o}${generateListDepth(r.nodes,t,l+1,i)}</li>`:n+=`<li><span class="fixed"></span>${o}</li>`}return`${n}</ul>`}function generateList(e,t){return generateListDepth(e,t,0,2)}const router=new Router;let id=router.readNodeIDFromRoute();""===id&&(id=nodes[0].id);let prevSelectedId=id;const inputElements=document.getElementsByClassName("custom-control-input"),carets=document.getElementsByClassName("caret"),out=document.getElementById("output");async function draw(e){let t=generateDiagram(e);if(""===t){let l=`No data found for the input nodeID: ${e}`;out.innerHTML=`<h2 style="text-align:center;font-weight:bold;font-size:20pt;color:red">${l}</h2>`,console.error(l)}else try{let{svg:i}=await mermaid.render("diagram",t,out);out.innerHTML=i}catch(n){console.error(n.message)}}document.addEventListener("DOMContentLoaded",async function(){let e=document.getElementById("input");for(let t of(e.innerHTML=`<form class="tree" id="intputForm">${generateList(nodes,id)}</form>`,await draw(id),carets))t.addEventListener("click",()=>{t.parentElement.querySelector("ul").classList.toggle("collapsed"),t.classList.toggle("minimize"),t.classList.toggle("maximize")});for(let l of inputElements)l.addEventListener("click",async e=>{let t=e.target.id;await draw(t),resetDefaultStyleInputElement(prevSelectedId),l.setAttribute("style",inputSelectedIdStyle),prevSelectedId=t,router.updateRouteToNode(t),isMobileDevice()&&(hideInputPanel(),isClickedSelectorLabel=!1)})});const btnExpandAll=document.getElementById("expand-all");btnExpandAll.addEventListener("click",function(){for(let e of document.getElementsByClassName("caret"))e.parentElement.querySelector("ul").classList.remove("collapsed"),e.classList.remove("maximize"),e.classList.add("minimize")});const btnCollapseAll=document.getElementById("collapse-all");function resetDefaultStyleInputElement(e){for(let t of inputElements)t.id===e&&t.setAttribute("style","")}btnCollapseAll.addEventListener("click",function(){for(let e of document.getElementsByClassName("caret"))e.parentElement.querySelector("ul").classList.add("collapsed"),e.classList.remove("minimize"),e.classList.add("maximize")});let isClickedSelectorLabel=!1;const selectorLabel=document.getElementById("lab-input");function showInputPanel(){let e=document.getElementById("in_col");e.setAttribute("style","height:70vh");let t=document.getElementById("input");t.setAttribute("style","width:100%");let l=document.getElementById("selector-btn");l.setAttribute("style","display:block")}function hideInputPanel(){let e=document.getElementById("in_col");e.setAttribute("style","height:6vh");let t=document.getElementById("input");t.setAttribute("style","width:0");let l=document.getElementById("selector-btn");l.setAttribute("style","display:none")}function isMobileDevice(){return window.screen.availWidth<=1600}selectorLabel.addEventListener("click",()=>{isMobileDevice()&&(isClickedSelectorLabel?(hideInputPanel(),isClickedSelectorLabel=!1):(showInputPanel(),isClickedSelectorLabel=!0))});</script></body></html>"""

        footer = self.cfg.footer if self.cfg.footer != "" else WebpageConfig.footer
        return template \
            .replace("{{.Nodes}}", self.nodes.to_json()) \
            .replace("{{.Links}}", self.links.to_json()) \
            .replace("{{.Title}}", self.cfg.title) \
            .replace("{{.Header}}", self.cfg.header) \
            .replace("{{.Footer}}", footer)


def main(puml_packages: str, puml_classes: str, webpage_cfg: WebpageConfig) -> str:
    """Main runner.

    Args:
        puml_packages: PUML DSL definition packages relations.
        puml_classes: PUML DSL definition classes relations.
        webpage_cfg: Page templating configuration.

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

    webpage_generator = WebpageGenerator(nodes, links_deduplicated, webpage_cfg)

    return webpage_generator()


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
    parser.add_argument("--title", required=False, type=str, default=WebpageConfig.title,
                        help="Custom page title.")
    parser.add_argument("--header", required=False, type=str, default=WebpageConfig.header,
                        help="Custom header string.")
    parser.add_argument("--footer", required=False, type=str, help="Custom footer as HTML encoded string.",
                        default=WebpageConfig.footer)
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

    html = main(puml_packages=puml_packages, puml_classes=puml_classes,
                webpage_cfg=WebpageConfig(title=args.title, header=args.header, footer=args.footer))

    if args.verbose:
        _LOGS.info("writing %s" % f"{args.output}/index.html")

    with open(f"{args.output}/index.html", "w") as fout:
        fout.write(html)
