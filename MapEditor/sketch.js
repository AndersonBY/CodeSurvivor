var widthElement;
var heightElement;
var currentTypeElement;
var changeBtn;
var outputBtn;
var MAP_WIDTH = 30;
var MAP_HEIGHT = 20;
var TIEL_SIZE = 20;
var mapArr;
var colorArr = [
	[123, 225, 154], 
	[182, 181, 184], 
	[42, 102, 55], 
	[38, 191, 191]]
var currentType = 0;

function setup() {
	let p = createCanvas(30*TIEL_SIZE+1, 20*TIEL_SIZE+1);
	p.parent('canvas-container');
	widthElement = select('#width-input');
	heightElement = select('#height-input');
	widthElement.value(30);
	heightElement.value(20);
	changeBtn = select('#change-btn');
	outputBtn = select('#output-btn');
	currentTypeElement = select('#current-type');
	changeBtn.mouseClicked(changeBtnClicked);
	outputBtn.mouseClicked(outputBtnClicked);

	mapArr = new Array(MAP_WIDTH)
	for (var x = 0; x < MAP_WIDTH; x++) {
		mapArr[x] = new Array(MAP_HEIGHT);
		for (var y = 0; y < MAP_HEIGHT; y++) {
			mapArr[x][y] = 0;
		}
	}
	drawMap();
}

function draw() {
	background(220);
	drawMap();
}

function drawMap() { 
	for (var x = 0; x < MAP_WIDTH; x++) {
		for (var y = 0; y < MAP_HEIGHT; y++) {
			fill(...colorArr[mapArr[x][y]]);
			rect(x*TIEL_SIZE, y*TIEL_SIZE, TIEL_SIZE, TIEL_SIZE);
		}
	}
}

function changeBtnClicked() {
	MAP_WIDTH = int(widthElement.value());
	MAP_HEIGHT = int(heightElement.value());
	resizeCanvas(MAP_WIDTH*TIEL_SIZE+1, MAP_HEIGHT*TIEL_SIZE+1)
	drawMap();
}

function outputBtnClicked() {
	let data = {
		width: MAP_WIDTH,
		height: MAP_HEIGHT,
		mapArr: mapArr
	}
	save(data, 'map.json')
}

function mouseClicked() {
	let x = int(mouseX/TIEL_SIZE);
	let y = int(mouseY/TIEL_SIZE);
	if (x<MAP_WIDTH&&y<MAP_HEIGHT) {
		mapArr[x][y] = currentType;
	}
}

function mouseDragged() {
	let x = int(mouseX/TIEL_SIZE);
	let y = int(mouseY/TIEL_SIZE);
	if (x<MAP_WIDTH&&y<MAP_HEIGHT) {
		mapArr[x][y] = currentType;
	}
}

function keyPressed() {
	currentType = keyCode - 48;
	if (currentType<0 || currentType>3) {
		currentType = 0;
	}
	currentTypeElement.html(`当前类型：${currentType}`);
}