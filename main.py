#!/usr/bin/env python3

""" Script to map the pyreverse DSL to the mermaid DSL to generate classDiagram.

Ref:
- https://www.bhavaniravi.com/python/generate-uml-diagrams-from-python-code
- https://mermaid.js.org/syntax/classDiagram.html

Usage example:

cd superduperdb
pyreverse -Akmy --colorized --max-color-depth 10 -o puml .
cat classes.dot | ./../scripts/generate_classdiagrams.py
"""
import dataclasses
import json
import sys
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


class Nodes(List["Node"]):
    def add(self, other: "Node"):
        root_found = False
        for node in self:
            if node.id == other.root_id():
                root_found = True
                node.nodes.add(other)
                break
        if not root_found:
            self.append(other)


def test_Nodes_append():
    tests = [
        {
            "given": Nodes([Node("foo", "foo", Nodes([]))]),
            "input": Node("foo.bar", "foo", Nodes([])),
            "want": Nodes([Node("foo", "foo", Nodes([Node("foo.bar", "foo", Nodes([]))]))]),
        },
        {
            "given": Nodes([Node("foo", "foo", Nodes([]))]),
            "input": Node("bar", "bar", Nodes([])),
            "want": Nodes([Node("foo", "foo", Nodes([])), Node("bar", "bar", Nodes([]))]),
        },
    ]

    for test in tests:
        test["given"].add(test["input"])
        assert test["given"] == test["want"]


@dataclasses.dataclass
class Node:
    id: str
    name: str
    nodes: Nodes

    def __eq__(self, other: "Node") -> bool:
        flag = self.id == other.id and self.name == self.name and len(self.nodes) == len(other.nodes)
        if not flag:
            return False

        for l, r in zip(self.nodes, other.nodes):
            if l != r:
                return False

        return True

    def root_id(self) -> str:
        return self.id.split(".")[0]


def new_node(id_str: str) -> Node:
    node_names = id_str.split(".")[-1::-1]
    node = Node(id_str, node_names[0], Nodes([]))

    i = 1
    while i < len(node_names):
        node_id = ".".join(node_names[i:][-1::-1])
        node = Node(node_id, node_names[i], Nodes([node]))
        i += 1

    return node


def test_new_node():
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
        assert new_node(test["input"]) == test["want"]


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

    def get_nodes(self) -> Nodes:
        o: Nodes = []  # type: ignore
        for link in self:
            o.append(new_node(link.start))
            o.append(new_node(link.end))
        return o


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


def _is_relation(el: str) -> bool:
    return " --" in el


def main(dsl_puml: List[str]) -> str:
    """ Main runner.

    :param dsl_puml: Input as the PUML DSL.
    :returns HTML page.
    """
    links: Links = Links([])

    for line in dsl_puml:
        if _is_relation(line):
            links.append(Link(line))

    links_deduplicated = links.deduplicate()
    nodes = links_deduplicated.get_nodes()

    return ""


if __name__ == "__main__":
    _in = []
    for line in sys.stdin:
        _inL = line.rstrip()
        if 'q' == _inL:
            break
        _in.append(_inL)

    _out = main(_in)

    with open("classes.html", "w") as fout:
        fout.write(_out)
