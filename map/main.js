"use strict";

const VERTEX_SHADER_SOURCE = `#version 300 es
precision highp float;

layout(location = 0) in vec2 aPosition;
layout(location = 1) in uint aColorTableIndex;

out vec4 vColor;

uniform mat3 uMapToView;
uniform mat3 uViewToClip;
uniform bool uColorFetch;
layout(std140) uniform uColorTableBlock {
    vec4 uColorTable[3026];
};

void main() {
    if (uColorFetch) {
        vColor = uColorTable[aColorTableIndex];
    } else {
        vColor = vec4(0.0, 0.0, 0.0, 1.0);
    }
    vec3 vPosition = uViewToClip * uMapToView * vec3(aPosition, 1.0);
    gl_Position = vec4(vPosition.xy, 0.0, 1.0);
}
`;

const FRAGMENT_SHADER_SOURCE = `#version 300 es
precision highp float;

in vec4 vColor;

out vec4 fColor;

void main() {
    fColor = vColor;
}
`;

let gl;

let glShaderProgram;

let vertexBuffer;
let faceBuffer;
let faceBufferSize;
let edgeBuffer;
let edgeBufferSize;
let colorTableBuffer;

let logZoom = -7.5;
let midX = (83748.4296875 + 732907.75) / 2;
let midY = (6629044.0 + 7776450.0) / 2;
let offX = 0;
let offY = 0;

let mouseViewPosition = null;
let mouseMapPosition = null;
let mouseMapPositionIsFixed = false;

let matrixMapToView;
let matrixViewToClip;

window.addEventListener("load", init, false);

function init() {
    // fetch the WebGL context
    gl = document.getElementById("target").getContext("webgl2");

    async function fetchFiles(filenames) {
        return Promise.all(filenames.map(filename => {
            return fetch(filename).then(response => response.arrayBuffer());
        }));
    }

    const filenames = [
        "map_vertex_position.dat",
        "map_vertex_color_index.dat",
        "map_face.dat",
        "map_edge.dat",
        "map_color_table.dat"
    ];

    fetchFiles(filenames).then(files => {
        buildShaders();
        buildBuffers(files);

        buildView();

        document.onmousemove = onMouseMove;
        document.onmouseleave = onMouseExit;
        document.onmousedown = onMouseDown;
        document.onmouseup = onMouseUp;
        document.onwheel = onMouseWheelMove;

        window.addEventListener("resize", onViewResize);

        drawRequest();
    });
}

function onViewResize(e) {
    buildView();
    drawRequest();
}

function onMouseMove(e) {
    mouseViewPosition = new Float32Array([
        e.clientX * window.devicePixelRatio, e.clientY * window.devicePixelRatio, 1
    ]);
    const newMouseMapPosition = multiplyM33V3(inverseM33(matrixMapToView), mouseViewPosition);
    if (!mouseMapPositionIsFixed) {
        mouseMapPosition = newMouseMapPosition;
    } else {
        offX += mouseMapPosition[0] - newMouseMapPosition[0];
        offY += mouseMapPosition[1] - newMouseMapPosition[1];
        buildView();
    }
    drawRequest();
}

function onMouseExit(e) {
    mouseViewPosition = null;
    if (!mouseMapPositionIsFixed) {
        mouseMapPosition = null;
    }
}

function onMouseDown(e) {
    if (e.button === 0) {
        mouseMapPositionIsFixed = true;
        document.body.style.cursor = "all-scroll";
    }
}

function onMouseUp(e) {
    if (e.button === 0) {
        mouseMapPositionIsFixed = false;
        document.body.style.cursor = "auto";
    }
}

function onMouseWheelMove(e) {
    logZoom = Math.min(Math.max(logZoom - 0.002 * e.deltaY, -7.5), -2.0);
    buildView();
    const newMouseMapPosition = multiplyM33V3(inverseM33(matrixMapToView), mouseViewPosition);
    offX += mouseMapPosition[0] - newMouseMapPosition[0];
    offY += mouseMapPosition[1] - newMouseMapPosition[1];
    buildView();
    drawRequest();
}

function buildShaders() {

    // build vertex shader
    const vertexShader = gl.createShader(gl.VERTEX_SHADER);
    gl.shaderSource(vertexShader, VERTEX_SHADER_SOURCE);
    gl.compileShader(vertexShader);

    // build fragment shader
    const fragmentShader = gl.createShader(gl.FRAGMENT_SHADER);
    gl.shaderSource(fragmentShader, FRAGMENT_SHADER_SOURCE);
    gl.compileShader(fragmentShader);

    // build shader program
    glShaderProgram = gl.createProgram();
    gl.attachShader(glShaderProgram, vertexShader);
    gl.attachShader(glShaderProgram, fragmentShader);
    gl.linkProgram(glShaderProgram);
}

function buildBuffers(files) {

    const vertexPositionArray = new Float32Array(files[0]);
    const vertexColorIndexArray = new Uint16Array(files[1]);
    const vertexData = new ArrayBuffer(vertexColorIndexArray.length * 12);
    const vertexDataAsFloat32 = new Float32Array(vertexData);
    const vertexDataAsUint16 = new Uint16Array(vertexData);
    for (let i = 0; i < vertexColorIndexArray.length; i++) {
        vertexDataAsFloat32[i * 3] = vertexPositionArray[i * 2];
        vertexDataAsFloat32[i * 3 + 1] = vertexPositionArray[i * 2 + 1];
        vertexDataAsUint16[i * 6 + 4] = vertexColorIndexArray[i];
    }
    const faceArray = new Uint32Array(files[2]);
    const edgeArray = new Uint32Array(files[3]);
    const colorTableArray = new Float32Array(files[4]);

    vertexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, vertexData, gl.STATIC_DRAW);

    faceBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, faceBuffer);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, faceArray, gl.STATIC_DRAW);
    faceBufferSize = faceArray.length;

    edgeBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, edgeBuffer);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, edgeArray, gl.STATIC_DRAW);
    edgeBufferSize = edgeArray.length;

    colorTableBuffer = gl.createBuffer();
    gl.bindBuffer(gl.UNIFORM_BUFFER, colorTableBuffer);
    gl.bufferData(gl.UNIFORM_BUFFER, colorTableArray, gl.DYNAMIC_DRAW);

    gl.bindBuffer(gl.ARRAY_BUFFER, null);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, null);
    gl.bindBuffer(gl.UNIFORM_BUFFER, null);
}

function buildView() {

    // compute viewport size in pixels
    const width  = Math.floor(gl.canvas.clientWidth  * window.devicePixelRatio);
    const height = Math.floor(gl.canvas.clientHeight * window.devicePixelRatio);

    // match canvas size with viewport size and update clipping area
    gl.canvas.width = width;
    gl.canvas.height = height;

    // update vertex transformation matrices
    const zoom = Math.exp(logZoom);
    matrixMapToView = new Float32Array([
        zoom, 0, 0,
        0, -zoom, 0,
        width / 2 - zoom * (midX + offX), height / 2 + zoom * (midY + offY), 1
    ]);
    matrixViewToClip = new Float32Array([
        2 / width, 0, 0,
        0, -2 / height, 0,
        -1, 1, 1
    ]);
}

function drawRequest() {
    window.requestAnimationFrame(draw);
}

function draw() {

    const uMapToView = gl.getUniformLocation(glShaderProgram, "uMapToView");
    const uViewToClip = gl.getUniformLocation(glShaderProgram, "uViewToClip");
    const uColorFetch = gl.getUniformLocation(glShaderProgram, "uColorFetch");
    const uColorTableBlock = gl.getUniformBlockIndex(glShaderProgram, "uColorTableBlock");
    gl.uniformBlockBinding(glShaderProgram, uColorTableBlock, 0);
    gl.bindBufferBase(gl.UNIFORM_BUFFER, 0, colorTableBuffer);

    const aPosition = gl.getAttribLocation(glShaderProgram, "aPosition");
    const aColorTableIndex = gl.getAttribLocation(glShaderProgram, "aColorTableIndex");

    // set viewport size
    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);

    // fill screen with background color
    gl.clearColor(0.8, 0.9, 1.0, 1.0);
    gl.clear(gl.COLOR_BUFFER_BIT);

    // enable shader program
    gl.useProgram(glShaderProgram);

    // set vertex transformation matrices
    gl.uniformMatrix3fv(uMapToView, false, matrixMapToView);
    gl.uniformMatrix3fv(uViewToClip, false, matrixViewToClip);

    // set vertex data
    gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);
    gl.enableVertexAttribArray(aPosition);
    gl.vertexAttribPointer(aPosition, 2,  gl.FLOAT, false, 12, 0);
    gl.enableVertexAttribArray(aColorTableIndex);
    gl.vertexAttribIPointer(aColorTableIndex, 1,  gl.UNSIGNED_SHORT, 12, 8);

    // set face data and draw faces
    gl.uniform1i(uColorFetch, 1);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, faceBuffer);
    gl.drawElements(gl.TRIANGLES, faceBufferSize, gl.UNSIGNED_INT, 0);

    // set edge data and draw edges
    gl.uniform1i(uColorFetch, 0);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, edgeBuffer);
    gl.drawElements(gl.LINES, edgeBufferSize, gl.UNSIGNED_INT, 0);

    // unbind buffers
    gl.bindBuffer(gl.ARRAY_BUFFER, null);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, null);

    // disable shader program
    gl.useProgram(null);

    gl.flush();
}

function multiplyM33V3(m, v) {
    let w = new Float32Array(3);
    for (let r = 0; r < 3; r++) {
        for (let k = 0; k < 3; k++) {
            w[r] += m[r + k * 3] * v[k];
        }
    }
    return w;
}

function multiplyM33M33(a, b) {
    let c = new Float32Array(9);
    for (let r = 0; r < 3; r++) {
        for (let c = 0; c < 3; c++) {
            for (let k = 0; k < 3; k++) {
                c[r + c * 3] += a[r + k * 3] * b[k + c * 3];
            }
        }
    }
    return c;
}

function inverseM33(a) {
    let d = 0;
    d += a[0] * (a[4] * a[8] - a[7] * a[5]);
    d -= a[3] * (a[1] * a[8] - a[7] * a[2]);
    d += a[6] * (a[1] * a[5] - a[4] * a[2]);
    let b = new Float32Array(9);
    b[0] = a[4] * a[8] - a[7] * a[5];
    b[1] = a[7] * a[2] - a[1] * a[8];
    b[2] = a[1] * a[5] - a[4] * a[2];
    b[3] = a[6] * a[5] - a[3] * a[8];
    b[4] = a[0] * a[8] - a[6] * a[2];
    b[5] = a[3] * a[2] - a[0] * a[5];
    b[6] = a[3] * a[7] - a[6] * a[4];
    b[7] = a[6] * a[1] - a[0] * a[7];
    b[8] = a[0] * a[4] - a[3] * a[1];
    for (let i = 0; i < 9; i++) {
        b[i] /= d;
    }
    return b;
}

function translateM33(x, y) {
    return new Float32Array([
        1, 0, 0,
        0, 1, 0,
        x, y, 1
    ]);
}

function scaleM33(x, y) {
    return new Float32Array([
        x, 0, 0,
        0, y, 0,
        0, 0, 1
    ]);
}
