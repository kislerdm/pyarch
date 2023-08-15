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

const nodes = [{
    "id": "superduperdb",
    "name": "superduperdb",
    "nodes": [{
        "id": "superduperdb.db",
        "name": "db",
        "nodes": [{
            "id": "superduperdb.db.mongodb",
            "name": "mongodb",
            "nodes": [{
                "id": "superduperdb.db.mongodb.metadata",
                "name": "metadata",
                "nodes": [{
                    "id": "superduperdb.db.mongodb.metadata.MongoMetaDataStore",
                    "name": "MongoMetaDataStore",
                    "nodes": []
                }]
            }, {
                "id": "superduperdb.db.mongodb.cdc",
                "name": "cdc",
                "nodes": [{
                    "id": "superduperdb.db.mongodb.cdc.MongoEventMixin",
                    "name": "MongoEventMixin",
                    "nodes": []
                }, {
                    "id": "superduperdb.db.mongodb.cdc.CDCHandler",
                    "name": "CDCHandler",
                    "nodes": []
                }, {
                    "id": "superduperdb.db.mongodb.cdc.MongoDatabaseListener",
                    "name": "MongoDatabaseListener",
                    "nodes": []
                }, {
                    "id": "superduperdb.db.mongodb.cdc.CDCKeys",
                    "name": "CDCKeys",
                    "nodes": []
                }, {
                    "id": "superduperdb.db.mongodb.cdc._DatabaseListenerThreadScheduler",
                    "name": "_DatabaseListenerThreadScheduler",
                    "nodes": []
                }, {
                    "id": "superduperdb.db.mongodb.cdc.CachedTokens",
                    "name": "CachedTokens",
                    "nodes": []
                }, {
                    "id": "superduperdb.db.mongodb.cdc.DBEvent",
                    "name": "DBEvent",
                    "nodes": []
                }, {
                    "id": "superduperdb.db.mongodb.cdc.BaseDatabaseListener",
                    "name": "BaseDatabaseListener",
                    "nodes": []
                }]
            }],
        }],
    }],
}];
const links = [{
    "start": "superduperdb",
    "end": "superduperdb.base",
    "arrow": "-->",
    "description": ""
}, {
    "start": "superduperdb",
    "end": "superduperdb.misc.superduper",
    "arrow": "-->",
    "description": ""
}, {
    "start": "superduperdb.__main__",
    "end": "superduperdb.cli",
    "arrow": "-->",
    "description": ""
}, {
    "start": "superduperdb.__main__",
    "end": "superduperdb.cli.config",
    "arrow": "-->",
    "description": ""
}, {
    "start": "superduperdb.__main__",
    "end": "superduperdb.cli.docs",
    "arrow": "-->",
    "description": ""
}, {
    "start": "superduperdb.__main__",
    "end": "superduperdb.cli.info",
    "arrow": "-->",
    "description": ""
}, {
    "start": "superduperdb.__main__",
    "end": "superduperdb.cli.serve",
    "arrow": "-->",
    "description": ""
}, {
    "start": "superduperdb.base.config",
    "end": "superduperdb.base.jsonable",
    "arrow": "-->",
    "description": ""
}];
// const nodes = {{.Nodes}};
// const links = {{.Links}};

class Router {
    #history;
    #location;
    #base;

    #token = "q";

    constructor() {
        this.#location = window.location;
        this.#history = window.history;
        this.#base = this.#removeTrailingCharacters(this.#split()[0]);
    }

    updateRouteToNode(nodeID) {
        this.#history.pushState({}, "", `${this.#base}?${this.#token}=${nodeID}`)
    }

    readNodeIDFromRoute() {
        const spl = this.#split();
        if (spl.length < 2) {
            return "";
        }
        return spl[1];
    }

    #split() {
        return this.#location.href.split(`${this.#token}=`);
    }

    #removeTrailingCharacters(s) {
        const lastChar = s.slice(-1);
        if (lastChar !== "?" && lastChar !== "/") {
            return s;
        }
        return this.#removeTrailingCharacters(s.slice(0, -1));
    }
}

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
    if (l.length === 0) {
        return "";
    }

    let o = `classDiagram
`;

    for (const link of l) {
        o += `${convertID(link["start"])} ${link["arrow"]} ${convertID(link["end"])}`
        if (link["description"] !== undefined && link["description"] !== "") {
            o += ` : ${link["description"]}`
        }
        o += `
`
    }

    return o
}

const inputSelectedIdStyle = "font-weight:bold;font-size:18px";

function generateListDepth(nodes, selected_id, level, maxDepth) {
    if (nodes.length === 0) {
        return ""
    }

    let o = level < maxDepth ? "<ul>" : `<ul class="collapsed">`;
    const minimizeFlag = level < maxDepth - 1 ? "minimize" : "maximize";

    for (const node of nodes) {
        const checked = node["id"] === selected_id ? `style=${inputSelectedIdStyle}` : "";
        const listRow = `<span class="custom-control-input" id="${node["id"]}" ${checked}>${node["name"]}</span>`;
        const dropDownSelection = `<span class="caret ${minimizeFlag}"></span>`;

        if (node["nodes"] !== undefined && node["nodes"].length > 0) {
            o += `<li>${dropDownSelection}${listRow}${generateListDepth(node["nodes"], selected_id, level + 1, maxDepth)}</li>`
        } else {
            o += `<li><span class="fixed"></span>${listRow}</li>`
        }
    }

    return `${o}</ul>`
}

function generateList(nodes, selected_id) {
    const maxDepth = 2;
    return generateListDepth(nodes, selected_id, 0, maxDepth);
}

const router = new Router();
let id = router.readNodeIDFromRoute();
if (id === "") {
    id = nodes[0].id;
}
let prevSelectedId = id;
const inputElements = document.getElementsByClassName("custom-control-input");
const carets = document.getElementsByClassName('caret');
const out = document.getElementById("output");

document.addEventListener("DOMContentLoaded", async function () {
    const el = document.getElementById("input");
    el.innerHTML = `<div class="force-overflow"><form class="tree" id="intputForm">${generateList(nodes, id)}</form></div>`;

    await draw(id);

    for (const caret of carets) {
        caret.addEventListener('click', () => {
            caret.parentElement.querySelector('ul').classList.toggle('collapsed');
            caret.classList.toggle('minimize');
            caret.classList.toggle('maximize');
        });
    }

    for (const elInput of inputElements) {
        elInput.addEventListener("click", async (e) => {
            const id = e.target.id;
            await draw(id);
            resetDefaultStyleInputElement(prevSelectedId);
            elInput.setAttribute("style", inputSelectedIdStyle);
            prevSelectedId = id;
            router.updateRouteToNode(id);

            if (isMobileDevice()) {
                hideInputPanel();
                isClickedSelectorLabel = false;
            }
        })
    }
});

async function draw(nodeId) {
    const shown = generateDiagram(nodeId);
    if (shown === "") {
        const errorMsg = `No data found for the input nodeID: ${nodeId}`
        out.innerHTML = `<h2 style="text-align:center;font-weight:bold;font-size:20pt;color:red">${errorMsg}</h2>`;
        console.error(errorMsg);
    } else {
        try {
            const {svg} = await mermaid.render("diagram", shown, out);
            out.innerHTML = svg;
        } catch (err) {
            console.error(err.message);
        }
    }
}

const btnExpandAll = document.getElementById("expand-all");
btnExpandAll.addEventListener("click", function () {
    for (const caret of document.getElementsByClassName('caret')) {
        caret.parentElement.querySelector('ul').classList.remove('collapsed');
        caret.classList.remove('maximize');
        caret.classList.add('minimize');
    }
});

const btnCollapseAll = document.getElementById("collapse-all");
btnCollapseAll.addEventListener("click", function () {
    for (const caret of document.getElementsByClassName('caret')) {
        caret.parentElement.querySelector('ul').classList.add('collapsed');
        caret.classList.remove('minimize');
        caret.classList.add('maximize');
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
    const btns = document.getElementById("selector-btn");
    btns.setAttribute("style", "display:block")
}

function hideInputPanel() {
    const inputPanel = document.getElementById("in_col");
    inputPanel.setAttribute("style", `height:6vh`);
    const inputTree = document.getElementById("input");
    inputTree.setAttribute("style", "width:0")
    const btns = document.getElementById("selector-btn");
    btns.setAttribute("style", "display:none");
}

function isMobileDevice() {
    return window.screen.availWidth <= 1600
}
