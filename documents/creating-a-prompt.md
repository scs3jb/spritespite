I want to generate a CLAUDE.md and prompt that will create a linux app that allows me to take input videos and export either a gif or spritesheet that can be used in godot. 

A video or gif can be input, and this will allow the user to select which frames to export.  This can either be selected which frames from a video of every frame or to choose the length and number of frames.  The app should allow chroma keying to filter out the background and make this transparent.  The output options should be gif, mp4 or sprite sheet.  When sprite sheet is selected, there should be a txt file with instructions to import the sprite (i.e positions, etc.) into godot.


Details
* Write the application in python with a UI
* You should be able to select an input which will be a file, mp4, mkv and common video formats should be supported, as well as gif.
* You should have an option to select frames (sorted in the correct order) or process the video (including a slider for start and finish time, number of frames, fps)
* You should be able to crop the video
* There should be a live preview on the right hand side of the UI
* You should be able to do chroma keying, selecting a colour and removing it
* Use ffmpeg to work with the video
* The output should be an mp4, a gif or a spritesheet as a PNG.  PNG output should have a transparent bottom layer and the sprite sheet must be compatible with dogot.


How to Test
* Take input.mp4
* Select the first frame and the last frame.
* Select the output to sprite sheet.
* Validate the first and last frame match exactly the sprite sheet
* Follow the godot instructions in the txt to create a simple test to display the sprite in game.
* Clean up the temporary files when test has finished.
