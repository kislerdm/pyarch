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


@dataclasses.dataclass
class Node:
    id: str
    name: str
    nodes: List["Node"]

    @staticmethod
    def from_string_id(id_str: str) -> "Node":
        o: Node

        node_names = id_str.split(".")
        parent_node = Node(node_names[0], node_names[0], [])
        o = parent_node

        for i, node_name in enumerate(node_names[1:]):
            node_id = f"{parent_node.id}.{node_name}"
            node = Node(node_id, node_name, [])
            parent_node.nodes.append(node)
            o.nodes.append(parent_node)
            parent_node = node

        return o

    def __eq__(self, other: "Node") -> bool:
        flag = self.id == other.id and self.name == self.name and len(self.nodes) == len(other.nodes)
        if not flag:
            return False

        for l, r in zip(self.nodes, other.nodes):
            if l != r:
                return False

        return True


def test_Node_from_string_id():
    tests = [
        {
            "input": "superduperdb.container.artifact.Artifact",
            "want": Node("superduperdb", "superduperdb", [
                Node("superduperdb.container", "container", [
                    Node("superduperdb.container.artifact", "artifact", [
                        Node("superduperdb.container.artifact", "artifact", [
                            Node("superduperdb.container.artifact.Artifact", "Artifact", []),
                        ]),
                    ]),
                ])
            ]),
        },
    ]
    for test in tests:
        assert Node.from_string_id(test["input"]) == test["want"]


class Nodes(List[Node]):
    def add(self, node: Node) -> None:
        pass


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
        pass


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
