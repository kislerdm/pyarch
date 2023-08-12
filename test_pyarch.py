from pyarch import Node, Nodes, Link, Links


def test_Node_from_str():
    tests = [
        {
            "input": "superduperdb.container.artifact.Artifact",
            "want": Node(
                "superduperdb",
                "superduperdb",
                Nodes(
                    [
                        Node(
                            "superduperdb.container",
                            "container",
                            Nodes(
                                [
                                    Node(
                                        "superduperdb.container.artifact",
                                        "artifact",
                                        Nodes(
                                            [
                                                Node("superduperdb.container.artifact.Artifact", "Artifact", Nodes([])),
                                            ]
                                        ),
                                    ),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
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
            "want": Node(
                "foo",
                "foo",
                Nodes(
                    [
                        Node(
                            "foo.bar",
                            "bar",
                            Nodes(
                                [
                                    Node("foo.bar.", "", Nodes([])),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        },
        {
            "input": ".",
            "want": Node(
                "",
                "",
                Nodes(
                    [
                        Node(".", "", Nodes([])),
                    ]
                ),
            ),
        },
    ]
    for test in tests:
        assert Node.from_str(test["input"]) == test["want"]


def test_Nodes_to_json():
    tests = [
        {"input": Nodes([Node("foo", "foo", Nodes([]))]), "want": """[{"id": "foo", "name": "foo", "nodes": []}]"""},
        {
            "input": Nodes(
                [
                    Node(
                        "foo",
                        "foo",
                        Nodes(
                            [
                                Node(
                                    "foo.bar",
                                    "bar",
                                    Nodes(
                                        [
                                            Node("foo.bar.qux", "qux", Nodes([])),
                                            Node("foo.bar.quxx", "quxx", Nodes([])),
                                        ]
                                    ),
                                ),
                                Node("foo.baz", "baz", Nodes([])),
                            ]
                        ),
                    )
                ]
            ),
            "want": """[{"id": "foo", "name": "foo", "nodes": [{"id": "foo.bar", "name": "bar", "nodes": [{"id": "foo.bar.qux", "name": "qux", "nodes": []}, {"id": "foo.bar.quxx", "name": "quxx", "nodes": []}]}, {"id": "foo.baz", "name": "baz", "nodes": []}]}]""",
        },
    ]
    for test in tests:
        assert test["input"].to_json() == test["want"]


def test_Nodes_add():
    tests = [
        {
            "given": Nodes([Node("foo", "foo", Nodes([]))]),
            "input": [
                Node("foo", "foo", Nodes([Node("foo.bar", "foo", Nodes([]))])),
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
            "want": Nodes(
                [
                    Node(
                        id="superduperdb",
                        name="superduperdb",
                        nodes=Nodes(
                            [
                                Node(
                                    id="superduperdb.base",
                                    name="base",
                                    nodes=Nodes(
                                        [
                                            Node(
                                                id="superduperdb.base.config",
                                                name="config",
                                                nodes=Nodes(
                                                    [
                                                        Node(
                                                            id="superduperdb.base.config.Notebook",
                                                            name="Notebook",
                                                            nodes=Nodes([]),
                                                        ),
                                                    ]
                                                ),
                                            ),
                                        ]
                                    ),
                                ),
                                Node(
                                    id="superduperdb.data",
                                    name="data",
                                    nodes=Nodes(
                                        [
                                            Node(
                                                id="superduperdb.data.cache",
                                                name="cache",
                                                nodes=Nodes(
                                                    [
                                                        Node(
                                                            id="superduperdb.data.cache.key_cache",
                                                            name="key_cache",
                                                            nodes=Nodes([]),
                                                        ),
                                                    ]
                                                ),
                                            ),
                                        ]
                                    ),
                                ),
                            ]
                        ),
                    ),
                ]
            ),
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
            "input": Links(
                [
                    Link(
                        "superduperdb.container.artifact.Artifact --* superduperdb.ext.torch.model.TorchTrainerConfiguration : optimizer_cls"
                    )
                ]
            ),
            "want": """[{"start": "superduperdb.container.artifact.Artifact", "end": "superduperdb.ext.torch.model.TorchTrainerConfiguration", "arrow": "--*", "description": "optimizer_cls"}]""",
        },
        {
            "input": Links(
                [
                    Link(
                        "superduperdb.container.artifact.Artifact --* superduperdb.ext.torch.model.TorchTrainerConfiguration"
                    )
                ]
            ),
            "want": """[{"start": "superduperdb.container.artifact.Artifact", "end": "superduperdb.ext.torch.model.TorchTrainerConfiguration", "arrow": "--*", "description": ""}]""",
        },
    ]
    for test in tests:
        assert test["input"].to_json() == test["want"]


def test_Links_deduplicate():
    tests = [
        {
            "input": Links(
                [
                    Link("foo --* bar : qux"),
                    Link("foo --* bar : quxx"),
                    Link("foo --* bar : qux"),
                    Link("foo --* bar : quxx"),
                    Link("foo --* bar : quxx1"),
                    Link("foo --* bar : quxx"),
                ]
            ),
            "want": 3,
        }
    ]
    for test in tests:
        assert len(test["input"].deduplicate()) == test["want"]
