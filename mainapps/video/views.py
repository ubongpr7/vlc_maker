from django.shortcuts import render

# Create your views here.
def make_video(request):
    # if request.method == 'POST':
    #     textfile = request.files.get('textfile')
    #     voice_id = request.form.get('voiceid')
    #     api_key = request.form.get('elevenlabs_apikey')
    #     api_key = request.form.get('elevenlabs_apikey')


    #     resoulution = request.form.get('resolution')

            
    #     font_color = request.form.get('font_color')
    #     subtitle_box_color = request.form.get('subtitle_box_color')
    #     # subtitle_box_color = (0,0,0)
    #     font_size = request.form.get('font_size')
    #     margin = request.form.get('margin')

    #     session['resoulution']=resoulution
    #     font_file = request.files.get('font_file')
    #     if font_file:
    #         font_file_path = os.path.join(app.config['UPLOAD_FOLDER'], font_file.filename)
    #         font_file.save(font_file_path)
    #         print(font_file)
    #     else:
    #         font_file_path = os.path.join(os.getcwd(), 'data', "Montserrat-SemiBold.ttf")
                
    #     # Validate inputs
    #     if textfile and voice_id and api_key:
    #         # Save the uploaded text file
    #         filepath = os.path.join(app.config['UPLOAD_FOLDER'], textfile.filename)
    #         textfile.save(filepath)
            
    #         # Read the file and split by lines
    #         with open(filepath, 'r') as f:
    #             lines = f.readlines()
    #         lines = [line.strip() for line in lines]
            
    #         # Render the slide creation page
    #         topic_folders = [f for f in os.listdir(app.config['ASSET_FOLDER']) if os.path.isdir(os.path.join(app.config['ASSET_FOLDER'], f))]
    #         # return render_template('slides.html',font_file=font_file.filename,margin=margin,font_color=font_color,font_size=font_size,subtitle_box_color=subtitle_box_color, lines=lines, topic_folders=topic_folders, uploaded_file=filepath)
    #         return render('vlc/frontend/VLSMaker/sceneselection/index.html',)
    
    # return render_template('index.html')

    return render(request,'vlc/frontend/VLSMaker/index.html')
    