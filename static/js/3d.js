var stage;

function init() {   
	var canvas = document.getElementById("canvas");
    if (!canvas || !canvas.getContext) return;
		
	stage = new createjs.Stage(canvas);  
    stage.enableMouseOver(true);
    stage.mouseMoveOutside = true; 
    createjs.Touch.enable(stage);
    
    var imgList = ["{{ url_for('static', filename='3d/1.jpg')}}", 
                   "{{ url_for('static', filename='3d/2.jpg')}}", 
                   "{{ url_for('static', filename='3d/3.jpg')}}", 
                   "{{ url_for('static', filename='3d/4.jpg')}}", 
                   "{{ url_for('static', filename='3d/5.jpg')}}", 
                   "{{ url_for('static', filename='3d/6.jpg')}}", 
                   "{{ url_for('static', filename='3d/7.jpg')}}", 
                   "{{ url_for('static', filename='3d/8.jpg')}}", 
                   "{{ url_for('static', filename='3d/9.jpg')}}", 
                   "{{ url_for('static', filename='3d/10.jpg')}}", 
                   "{{ url_for('static', filename='3d/11.jpg')}}", 
                   "{{ url_for('static', filename='3d/12.jpg')}}", 
                   "{{ url_for('static', filename='3d/13.jpg')}}", 
                   "{{ url_for('static', filename='3d/14.jpg')}}", 
                   "{{ url_for('static', filename='3d/15.jpg')}}", 
                   "{{ url_for('static', filename='3d/16.jpg')}}", 
                   "{{ url_for('static', filename='3d/17.jpg')}}", 
                   "{{ url_for('static', filename='3d/18.jpg')}}", 
                   "{{ url_for('static', filename='3d/19.jpg')}}", 
                   "{{ url_for('static', filename='3d/20.jpg')}}", 
                   "{{ url_for('static', filename='3d/21.jpg')}}", 
                   "{{ url_for('static', filename='3d/22.jpg')}}", 
                   "{{ url_for('static', filename='3d/23.jpg')}}", 
                   "{{ url_for('static', filename='3d/24.jpg')}}", 
                   "{{ url_for('static', filename='3d/25.jpg')}}", 
                   "{{ url_for('static', filename='3d/26.jpg')}}", 
                   "{{ url_for('static', filename='3d/27.jpg')}}", 
                   "{{ url_for('static', filename='3d/28.jpg')}}", 
                   "{{ url_for('static', filename='3d/29.jpg')}}", 
                   "{{ url_for('static', filename='3d/30.jpg')}}", 
                   "{{ url_for('static', filename='3d/31.jpg')}}"];  
    var images = [], loaded = 0, currentFrame = 0, totalFrames = imgList.length; 
    var rotate360Interval, start_x;
    
    var bg = new createjs.Shape();
    stage.addChild(bg);  
    
    var bmp = new createjs.Bitmap();	  
    stage.addChild(bmp);
    
    var myTxt = new createjs.Text("HTC One", '24px Ubuntu', "#ffffff");
    myTxt.x = myTxt.y =20;
    myTxt.alpha = 0.08;
    stage.addChild(myTxt);   
    
    
    function load360Image() {
        var img = new Image();
        img.src = imgList[loaded];
        img.onload = img360Loaded;
        images[loaded] = img;   
    }
    
    function img360Loaded(event) {
        loaded++;        
        bg.graphics.clear()
        bg.graphics.beginFill("#222").drawRect(0,0,stage.canvas.width * loaded/totalFrames, stage.canvas.height);
        bg.graphics.endFill();
        
        if(loaded==totalFrames) start360();
        else load360Image();
    }

    
    function start360() {
        document.body.style.cursor='none';
        
        // 360 icon
        var iconImage = new Image();
        iconImage.src = "http://jsrun.it/assets/y/n/D/c/ynDcT.png";
        iconImage.onload = iconLoaded;        
       
        // update-draw
        update360(0);
        
        // first rotation
        rotate360Interval = setInterval(function(){ if(currentFrame===totalFrames-1) { clearInterval(rotate360Interval); addNavigation(); } update360(1); }, 25);
    }
    
    function iconLoaded(event) {
        var iconBmp = new createjs.Bitmap();
        iconBmp.image = event.target;
        iconBmp.x = 20;
        iconBmp.y = canvas.height - iconBmp.image.height - 20;
        stage.addChild(iconBmp);
    }
    
    function update360(dir) {
        currentFrame+=dir;
        if(currentFrame<0) currentFrame = totalFrames-1;
        else if(currentFrame>totalFrames-1) currentFrame = 0;
        bmp.image = images[currentFrame];
    }


    //------------------------------- 
     function addNavigation() { 
        stage.onMouseOver = mouseOver;
        stage.onMouseDown = mousePressed;        
        document.body.style.cursor='auto';
    }
    
    function mouseOver(event) {
        document.body.style.cursor='pointer';
    }
    
    function mousePressed(event) {
        start_x = event.rawX;
        stage.onMouseMove = mouseMoved;
        stage.onMouseUp = mouseUp;
        
        document.body.style.cursor='w-resize';        
    }
    
	function mouseMoved(event) {
        var dx = event.rawX - start_x;
        var abs_dx = Math.abs(dx);
        
        if(abs_dx>5) {
            update360(dx/abs_dx);
            start_x = event.rawX;
        }
	}
    
    function mouseUp(event) {
        stage.onMouseMove = null;
        stage.onMouseUp = null;         
        document.body.style.cursor='pointer';
	}    
    
    function handleTick() {	
         stage.update();
    }    
    
    document.body.style.cursor='progress';
    load360Image();
    
    
     // TICKER
    createjs.Ticker.addEventListener("tick", handleTick);
    createjs.Ticker.setFPS(60);
    createjs.Ticker.useRAF = true;
}




// Init
window.addEventListener('load', init, false);