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

const nodes = [];
const links = [];
// const nodes = {{.Nodes}};
// const links = {{.Links}};

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