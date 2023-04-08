from flask import Flask, url_for
from markupsafe import escape
from flask import request, flash, redirect
from flask import render_template
from flask import jsonify
import datetime
from pathlib import Path
#クライアントの命名したファイル名を利用するためのsecure_filename()
from werkzeug.utils import secure_filename

import cv2
from retinaface.pre_trained_models import get_model
from retinaface.utils import vis_annotations
import os

import torch
import torchvision
from torchvision import transforms
import torch.nn as nn
from torch.nn import functional as F
from PIL import Image
import json

app = Flask(__name__)
#app.config["SECRET_ KEY"] = "2AZSMss3p5QPbcY2hBsJ"
app.secret_key =  "2AZSMss3p5QPbcY2hBsJ"

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST', 'GET'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'the_file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['the_file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # 保存時のファイル名を現在時刻に変更する
            ext = Path(file.filename).suffix
            now = datetime.datetime.now()
            fname = now.strftime('%Y%m%d%H%M%S') + ext

            saveFilePath = os.path.join(os.path.join('static', 'img'), secure_filename(fname))
            file.save(saveFilePath)

            #アップロードしてサーバーにファイルが保存されたらfinishedを表示
            return render_template('finished.html', filepath = saveFilePath)
        return
    else:
    	#GETでアクセスされた時、uploadsを表示
    	return render_template('upload.html')

@app.route('/object_detect', methods=['POST', 'GET'])
def object_detection():
    # Linuxだとフルパスでないと動作しないようなので
    appPath = os.path.dirname(__file__)
    filePath = os.path.join(appPath, os.path.join(os.path.join('static', 'img'), Path(request.json).name))
    print(filePath)
    out_filepath = os.path.join(os.path.join('static', 'img'), 'out.jpg')

    model = torch.hub.load('ultralytics/yolov5', 'yolov5s')

    # 推論
    results = model(filePath)

    # 分類結果をDataFrame形式で取得できる
    df = results.pandas().xywh[0] # .xyxy[0]
    results.render() # 画面にボンディングボックスを表示する
    im_rgb = cv2.cvtColor(results.ims[0], cv2.COLOR_RGB2BGR)
    cv2.imwrite(out_filepath, im_rgb)
    #results.save(out_filepath)

    return jsonify('\\' + out_filepath)

@app.route('/detect', methods=['POST', 'GET'])
def detect_file():
    # Linuxだとフルパスでないと動作しないようなので
    appPath = os.path.dirname(__file__)
    filePath = os.path.join(appPath, os.path.join(os.path.join('static', 'img'), Path(request.json).name))
    print(filePath)
    out_filepath = os.path.join(os.path.join('static', 'img'), 'out.jpg')
    face_detect(filePath, out_filepath)

    return jsonify('\\' + out_filepath)

def face_detect(inPath, outPath):
    model = get_model("resnet50_2020-07-20", max_size=2048)
    model.eval()

    results, image = find_faces(inPath)
    image_out = draw_res(image,results)
    cv2.imwrite(outPath, image_out)

def find_faces(inPath):
    model = get_model("resnet50_2020-07-20", max_size=2048)
    model.eval()

    image = cv2.imread(inPath)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = model.predict_jsons(image)
    return results, image

@app.route('/face_recognition', methods=['POST', 'GET'])
def face_recognition():
    # Linuxだとフルパスでないと動作しないようなので
    appPath = os.path.dirname(__file__)
    filePath = os.path.join(appPath, os.path.join(os.path.join('static', 'img'), Path(request.json).name))

    model_detect = torchvision.models.resnet18(pretrained=True)
    num_ftrs = model_detect.fc.in_features
    model_detect.fc = nn.Linear(num_ftrs, 4) # 4分類

    model_detect.load_state_dict(torch.load(os.path.join(appPath, 'model_gpu.pth')))

    # デバイスを選択する。
    device = get_device(use_gpu=True)
    model_detect.to(device)

    transform = transforms.Compose(
        [
            transforms.Resize(256),  # (256, 256) で切り抜く。
            transforms.CenterCrop(224),  # 画像の中心に合わせて、(224, 224) で切り抜く
            transforms.ToTensor(),  # テンソルにする。
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
            ),  # 標準化する。
        ]
    )
    
    # クラス名一覧を取得する。
    class_names = get_classes()

    # 顔を抽出
    results, image = find_faces(filePath)
 
    image_out = image.copy()
    height, width, channels = image_out.shape[:3]
    for rect in results:
        fname = "out.jpg"
        outPath = os.path.join(appPath, os.path.join(os.path.join('static', 'img'), fname))
        bbox = rect['bbox']
        if len(results) > 2:
            face = image[bbox[1] : bbox[3], bbox[0] : bbox[2]] #縦位置上：下, 横位置左：右
            cv2.imwrite(outPath, face)
        else:
            cv2.imwrite(outPath, image_out)

        img = Image.open(outPath)
        inputs = transform(img)
        inputs = inputs.unsqueeze(0).to(device)
        # 推論モード
        model_detect.eval()
        outputs = model_detect(inputs)

        batch_probs = F.softmax(outputs, dim=1)
        batch_probs, batch_indices = batch_probs.sort(dim=1, descending=True)

        fontScale = 1.0
        if width > 2048:
            fontScale = 10.0
        if width > 1024:
            fontScale = 5.0
        for probs, indices in zip(batch_probs, batch_indices):
            for k in range(len(class_names)):
                print(f"Top-{k + 1} {indices[k]} {probs[k]:.2%} {class_names[indices[k]]}")
                if class_names[indices[k]] == 'Sara':
                    color = (0, 255, 0)
                    probability = probs[k].item()
                    if (0.6 <= probability and probability < 0.8) :
                        color = (0, 255, 255)
                    elif probability < 0.6:
                        color = (0, 0, 255)
                    cv2.rectangle(image_out,(bbox[0],bbox[1]),(bbox[2],bbox[3]),color,thickness=10)
                    cv2.putText(image_out,
                        text=f'{class_names[indices[k]]}:{probability:.2%}',
                        org=(bbox[0], bbox[1]),
                        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=1.0,
                        color=(255, 255, 255),
                        thickness=1,
                        lineType=cv2.LINE_4)

    out_filepath = os.path.join(os.path.join('static', 'img'), 'out.jpg')
    cv2.imwrite(out_filepath, image_out)
    return jsonify('\\' + out_filepath)

def draw_res(image,results):
    for r in results:
        bbox = r['bbox']
        if not bbox:continue
        cv2.rectangle(image,(bbox[0],bbox[1]),(bbox[2],bbox[3]),(0,0,255),thickness=10)
    return image

def get_device(use_gpu):
    if use_gpu and torch.cuda.is_available():
        # これを有効にしないと、計算した勾配が毎回異なり、再現性が担保できない。
        torch.backends.cudnn.deterministic = True
        return torch.device("cuda")
    else:
        return torch.device("cpu")

def get_classes():
    appPath = os.path.dirname(__file__)
    filePath = os.path.join(appPath, 'class_name.json') 

    # クラス一覧を読み込む。
    with open(filePath) as f:
        data = json.load(f)
        class_names = [x["name"] for x in data]

    return class_names