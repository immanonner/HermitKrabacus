
// Notes:
// derived from: https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Objects/Object_building_practice
// todo: that cool astro fidget spinners?
// todo: flip character visualization
// todo: better colors / fades from white printing, green standard, highlighted green single chars, to black ending
// todo: glitched character after print, highlighted ones only? how often?
// todo: spell significant sentences: ie family member names // quotes from the movie etc.
// - it took me way too long to discover the Map class == literally the python Dict data structure. 2 days of research and refactoring. ugh.
// -"this" is a funky variable. highly dependent on scope; needed to save state of parent "this" as current_app for raindrop constructor function for a few computations which was odd.
//      perhaps that could have been done with super()? -- thats still something i need to study.
// -I'm certain the droplet printing switch case logic could be refactored for DRY purposes--however in its current state, I find it....acceptable...
// -keep track of all setInterval's: else you may run into runaway accelerations of code; you can also delete intervals on certain conditions
// -I wonder if i can back in resize functionality into the app...
//  !BREAKING ISSUE?? doesnt run on FF. or EDGE. and poorly on chrome. Something to do with setInterval / animateFrame / setTimeout? Maybe?
// !however, it worked fantastically on my surface pro...
//  solved!! 3/9/2022 disabled fingerprinting chrome plugin and it works great again on chrome. 
// solved!! 3/11/2022 for firefox too. textbounding box measuring is locked behind a setting...and requires it to be enabled to work properly: "dom.textMetrics.fontBoundingBox.enabled"
//  https://developer.mozilla.org/en-US/docs/Web/API/TextMetrics

class Matrix_App {
  constructor(canvas, width, height) {
    const current_app = this;
    this.maxX_pxl = canvas.width = width;
    this.maxY_pxl = canvas.height = height;
    this.ctx = canvas.getContext("2d");
    this.Raindrops = new Map();
    this.Raindrop = class Raindrop {
      constructor(fontFamily, fontSize) {
        let current_drop = this;
        this.fontString = `bold ${fontSize}px ${fontFamily}`;
        this.metrics = current_app.getFontMetrics(current_drop.fontString);
        this.xColUbound = Math.round(current_app.maxX_pxl / current_drop.metrics.fwidth) - 1;
        this.yColUbound = Math.round(current_app.maxY_pxl / current_drop.metrics.fheight) + 1;
        this.xCol = current_app.randint(0, current_drop.xColUbound);
        this.yCol = current_app.randint(0, Math.round(current_drop.yColUbound));
        this.xPx = Math.round(current_drop.xCol * current_drop.metrics.fwidth);
        this.yPx = Math.round(current_drop.yCol * current_drop.metrics.fheight);
        this.textString = current_app.randStr(current_drop.yColUbound - current_drop.yCol);
        this.passMe = current_app.randint(0, current_drop.yColUbound);
        this.status = ["print", "pause", "spin"][current_app.randint(0, 2)];
        this.cycleCount = 0;
      };

    };
  };

  // helper functions
  randint(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  };

  randStr(length) {
    const lChars = "abcdefghijklmnopqrstuvwxyz";
    const uChars = lChars.toUpperCase();
    const asciiStr = uChars;
    let textStr = "";

    for (let i = 0; i < length; i++) {
      textStr += asciiStr[this.randint(0, asciiStr.length - 1)];
    };
    return textStr;
  };

  getFontMetrics(fontString) {
    this.ctx.font = fontString;
    let metrics = this.ctx.measureText("M");
    let fontHeight = metrics.fontBoundingBoxAscent + metrics.fontBoundingBoxDescent;
    return {
      fwidth: metrics.width,
      fheight: fontHeight
    };
  };

  // dynamic website functions
  updateCanvasDimensions(canvas, W, H) {
    this.maxX_pxl = canvas.width = W;
    this.maxY_pxl = canvas.height = H; // update all droplets for dynamic responsiveness; adjust length of strings and delete any droplet outside the new dimension

    for (let [k, drop] of this.Raindrops) {
      drop.metrics = this.getFontMetrics(drop.fontString);
      drop.xColUbound = Math.round(this.maxX_pxl / drop.metrics.fwidth) - 1;
      drop.yColUbound = Math.round(this.maxY_pxl / drop.metrics.fheight) + 1;
      let currentPrintedString = drop.textString.substring(0, drop.cycleCount);
      if (drop.xCol >= drop.xColUbound || drop.yCol >= drop.yColUbound) {
        this.Raindrops.delete(k);
      } else if (drop.yColUbound - currentPrintedString.length - 1 > 0) {
        drop.textString = currentPrintedString + this.randStr(drop.yColUbound - currentPrintedString.length - 1);
      } else {
        drop.status = "shrink";
      };
    };
    // continue running the app after the height / width are resized if it was already running
  };

  // spawn droplets within the confines of the canvas
  getDrops() {
    while (this.Raindrops.size < Math.round(this.maxX_pxl / 60)) {
      let dewDrop = new this.Raindrop("Courier", 25);

      while (this.Raindrops.has(dewDrop.xPx)) {
        dewDrop = new this.Raindrop("Courier", 25);
      };
      this.Raindrops.set(dewDrop.xPx, dewDrop);
    };
  };

  showAllRaindrops() {
    this.ctx.fillStyle = "green";
    for (let drop of this.Raindrops.values()) {
      this.ctx.font = drop.fontString;
      let count = 0;
      for (let letter in drop.textString) {
        this.ctx.fillText(drop.textString[letter], drop.xPx, drop.yPx + count * drop.metrics.fheight);
        count += 1;
      };
    };
  };

  // droplet printer logic
  // limit printed textString to maximum of 6? chars.
  // adjust colors: highlighted green for 'glitch', standard green, and gradual black/grey
  makeItRainText() {
    for (let [k, drop] of this.Raindrops) {
      this.ctx.font = drop.fontString;
      this.ctx.fillStyle = "green";
      let currCycle = 0;

      switch (drop.status) {
        case "pause":
          // prevent string from printing at all to give simulate random raindrops falling
          if (drop.passMe != 0) {
            drop.passMe -= 1;
          } else {
            drop.status = "print";
          };
          break;

        case "print":
          // print the string for visualization, increase the shown string by 1 letter, change status to spin, increase passMe count
          while (currCycle < drop.cycleCount + 1) {
            this.ctx.fillText(drop.textString[currCycle], drop.xPx, drop.yPx + currCycle * drop.metrics.fheight);
            currCycle += 1;
          };

          if (drop.cycleCount < drop.textString.length - 1) {
            drop.cycleCount += 1;
            drop.status = "spin";
            drop.passMe = this.randint(5, 15);
          } else {
            drop.status = "shrink";
          };
          break;

        case "spin":
          // spin the current letter to illustrate "hacking"
          while (currCycle < drop.cycleCount + 1) {
            this.ctx.fillText(drop.textString[currCycle], drop.xPx, drop.yPx + currCycle * drop.metrics.fheight);
            currCycle += 1;
          };

          if (drop.passMe > 0) {
            this.ctx.fillStyle = "rgb(204, 255,204)";
            this.ctx.fillText(this.randStr(1), drop.xPx, drop.yPx + currCycle * drop.metrics.fheight);
            drop.passMe -= 1;
          } else if (drop.cycleCount < drop.textString.length - 1) {
            this.ctx.fillText(drop.textString[currCycle], drop.xPx, drop.yPx + currCycle * drop.metrics.fheight);
            drop.status = "print";
          } else {
            drop.status = "shrink";
          };
          break;

        case "shrink":
          // when string hits y coord destination begin to remove beginning letters and adjust the y coord start position
          while (currCycle < drop.textString.length) {
            this.ctx.fillText(drop.textString[currCycle], drop.xPx, drop.yPx + currCycle * drop.metrics.fheight);
            currCycle += 1;
          };

          if (drop.textString.length < 2) {
            drop.status = "delete";
          };
          drop.textString = drop.textString.substring(1);
          drop.yPx += drop.metrics.fheight;
          break;

        case "delete":
          //  shrink status is finished, delete the string from memory and generate a new one
          this.Raindrops.delete(k);
          this.getDrops();
          break;

        default:
          // not currently used
          break;
      };
    };
  };

  kill(frameid) {
    this.Raindrops.clear();
    this.ctx.fillStyle = '#232323';
    this.ctx.fillRect(0, 0, this.maxX_pxl, this.maxY_pxl);
    cancelAnimationFrame(frameid);
  };
};
const matrix_canvas = document.getElementById('mtx');
const app = new Matrix_App(matrix_canvas, window.innerWidth, window.innerHeight);


// run app in loop
function run() {
  app.getDrops();
  app.ctx.fillStyle = '#232323';
  app.ctx.fillRect(0, 0, app.maxX_pxl, app.maxY_pxl);
  app.makeItRainText();
  frameid = requestAnimationFrame(run);
};
run();

window.onresize = function () {
  app.updateCanvasDimensions(matrix_canvas, window.innerWidth, window.innerHeight);
};