from flask import Flask, render_template, request, jsonify
import os
import cv2
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import ImageGrab, Image
import pyperclip

app = Flask(__name__)

load_dotenv()
from groq import Groq
groq_client = Groq(api_key=os.environ['GROQ_API_KEY'])
genai.configure(api_key=os.environ['GOOGLE_API_KEY'])


sys_msg= (
'You are a multi-modal AI voice assistant. Your user may or may not have attached a photo for context ' 
'(either a screenshot or a webcam capture). Any photo has already been processed into a highly detailed '
'text prompt that will be attached to their transcribed voice prompt. Generate the most useful and ' 
'factual response possible, carefully considering all previous generated text in your response before ' 
'adding new tokens to the response. Do not expect or request images, just use the context if added. ' 
'Use all of the context of this conversation so your response is relevant to the conversation. Make ' 
'your responses clear and concise, avoiding any verbosity.'
)
convo = [{'role': 'system', 'content': sys_msg}]

generation_config = {
    'temperature': 0.7,
    'top_p': 1,
    'top_k': 1,
    'max_output_tokens': 2048
}
safety_settings = [
    {
        'category': 'HARM_CATEGORY_HARASSMENT',
        'threshold': 'BLOCK_NONE',
    },
    {
        'category': 'HARM_CATEGORY_HATE_SPEECH',
        'threshold': 'BLOCK_NONE',
    },
    {
        'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT',
        'threshold': 'BLOCK_NONE',
    },
    {
        'category': 'HARM_CATEGORY_DANGEROUS_CONTENT',
        'threshold': 'BLOCK_NONE',
    },
]
model = genai.GenerativeModel('gemini-1.5-flash-latest',
                              generation_config=generation_config,
                              safety_settings=safety_settings)
def groq_prompt(prompt,img_context):
    if img_context:
        prompt = f'USER PROMPT: {prompt}\n\n  IMAGE CONTEXT: {img_context}'
    convo.append({'role': 'user', 'content': prompt})
    chat_completion = groq_client.chat.completions.create(messages=convo,model='llama-3.1-70b-versatile')
    response = chat_completion.choices[0].message
    convo.append(response)
    return response.content

def function_call(prompt):
    sys_msg=('You are an AI function calling model. You will determine whether extracting the users clipboard content, ' 
             'taking a screenshot, capturing the webcam or calling no functions Is best for a voice assistant to respond ' 
             'to the users prompt. The webcam can be assumed to be a normal laptop webcam facing the user. You will ' 
             'respond with only one selection from this list: ["extract clipboard", "take screenshot", "capture webcam", "None"] \n' 
             'Do not respond with anything but the most logical selection from that list with no explanations. Format the ' 
             'function call name exactly as I listed.'
             )
    function_convo = [{'role':'system','content':sys_msg},
                      {'role':'user','content':prompt}]
    chat_completion = groq_client.chat.completions.create(messages=function_convo, model='llama-3.1-70b-versatile')
    response = chat_completion.choices[0].message
    return response.content
def take_screenshot():
    path = 'screenshot.jpg'
    screenshot = ImageGrab.grab()
    rgb_screenshot = screenshot.convert('RGB')
    rgb_screenshot.save(path,quality=100)
def web_cam_capture():
    web_cam = cv2.VideoCapture(0)
    if not web_cam.isOpened():
        print('web_cam is not opened')
        exit()
    path = 'web_cam.jpg'
    ret, frame = web_cam.read()
    cv2.imwrite(path, frame)
    web_cam.release()
def get_clipboard_text():
    clipboard_content = pyperclip.paste()
    if isinstance(clipboard_content, str):
        return clipboard_content
    else:
        print('No clipboard text to copy')
        return None
def vision_prompt(prompt,photo_path):
    img = Image.open(photo_path)
    prompt = (
        'You are the vision analysis AI that provides semantic meaning from images to provide context ' 
        'to send to another AI that will create a response to the user. Do not respond as the AI assistant ' 
        'to the user. Instead take the user prompt input and try to extract all meaning from the photo ' 
        'relevant to the user prompt. Then generate as much objective data about the image for the AI ' 
        f'assistant who will respond to the user. \nUSER PROMPT: {prompt}'
    )
    response = model.generate_content([prompt,img])
    return response.text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    prompt = request.json['prompt']
    call = function_call(prompt)
    visual_context = None
    function_called = None

    if 'take screenshot' in call:
        take_screenshot()
        visual_context = vision_prompt(prompt=prompt, photo_path='screenshot.jpg')
        function_called = 'take_screenshot'
    elif 'capture webcam' in call:
        web_cam_capture()
        visual_context = vision_prompt(prompt=prompt, photo_path='web_cam.jpg')
        function_called = 'web_cam_capture'
    elif 'extract clipboard' in call:
        paste = get_clipboard_text()
        prompt = f'{prompt}\n\nCLIPBOARD CONTENT: {paste}'
        function_called = 'get_clipboard_text'

    response = groq_prompt(prompt=prompt, img_context=visual_context)
    return jsonify({'response': response, 'function_called': function_called})

if __name__ == '__main__':
    app.run(debug=True)