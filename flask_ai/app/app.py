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
import pandas

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

            saveFilePath = os.path.join(os.path.join('static/ai', 'img'), secure_filename(fname))
            file.save(saveFilePath)

            #アップロードしてサーバーにファイルが保存されたらfinishedを表示
            return render_template('finished.html', filepath = saveFilePath)
        return
    else:
    	#GETでアクセスされた時、uploadsを表示
    	return render_template('upload.html')

def resize_image(filePath):
    # 対象画像読み込み
    img = cv2.imread(filePath,cv2.IMREAD_COLOR)

    # 画像の大きさを取得
    height, width, channels = img.shape[:3]
    if width > 1024 or height > 1024:
        appPath = os.path.dirname(__file__)
        re_h = re_w = 1024/max(height,width)
        img2 = cv2.resize(img, dsize=None, fx=re_h , fy=re_w)
        tmpFilePath = os.path.join(appPath, os.path.join(os.path.join('static/ai', 'img'), "tmp.jpg"))
        cv2.imwrite(tmpFilePath, img2)
        return tmpFilePath
    
    return filePath
        
@app.route('/object_detect', methods=['POST', 'GET'])
def object_detection():
    # Linuxだとフルパスでないと動作しないようなので
    appPath = os.path.dirname(__file__)
    filePath = os.path.join(appPath, os.path.join(os.path.join('static/ai', 'img'), Path(request.json).name))
    print(filePath)
    
    # 入力画像の大きさが大きいと失敗するようなのでリサイズする
    filePath = resize_image(filePath)

    out_filepath = os.path.join(os.path.join('static/ai', 'img'), 'out.jpg')

    device = get_device(use_gpu=True)
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
    model.to(device)

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
    filePath = os.path.join(appPath, os.path.join(os.path.join('static/ai', 'img'), Path(request.json).name))
    print(filePath)
    out_filepath = os.path.join(os.path.join('static/ai', 'img'), 'out.jpg')
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
    filePath = os.path.join(appPath, os.path.join(os.path.join('static/ai', 'img'), Path(request.json).name))

    # 入力画像が大きければリサイズする
    filePath = resize_image(filePath)

    model_detect = torchvision.models.resnet18(pretrained=True)
    num_ftrs = model_detect.fc.in_features
    model_detect.fc = nn.Linear(num_ftrs, 4) # 4分類

    # デバイスを選択する。
    device = get_device(use_gpu=True)
    model_detect.to(device)
    
    model_detect.load_state_dict(torch.load(os.path.join(appPath, 'model_gpu.pth'), map_location=device))

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

    # 人を抽出
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
    model.to(device)

    # 推論
    results = model(filePath)

    # 分類結果をDataFrame形式で取得できる
    df = results.pandas().xyxy[0] # .xyxy[0]
    print(df)
    print(len(df))
    im_rgb = cv2.cvtColor(results.ims[0], cv2.COLOR_RGB2BGR)
    for i in range(len(df)):
        name = df.loc[i, "name"]
        if  name == "person":
            fname = "out.jpg"
            outPath = os.path.join(appPath, os.path.join(os.path.join('static/ai', 'img'), fname))
            xmin = df.loc[i, "xmin"].astype(int)
            ymin = df.loc[i, "ymin"].astype(int)
            xmax = df.loc[i, "xmax"].astype(int)
            ymax = df.loc[i, "ymax"].astype(int)
            person = im_rgb[ymin : ymax, xmin : xmax] #縦位置上：下, 横位置左：右
            cv2.imwrite(outPath, person)

            img = Image.open(outPath)
            inputs = transform(img)
            inputs = inputs.unsqueeze(0).to(device)
            # 推論モード
            model_detect.eval()
            outputs = model_detect(inputs)

            batch_probs = F.softmax(outputs, dim=1)
            batch_probs, batch_indices = batch_probs.sort(dim=1, descending=True)

            text = ''
            fontFace = cv2.FONT_HERSHEY_SIMPLEX
            fontScale = 1.0
            thickness = 2
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
                        # 矩形描画
                        cv2.rectangle(im_rgb,(xmin, ymin),(xmax, ymax),color,thickness=10)
                        # 文字の幅、高さ取得
                        text = f'{class_names[indices[k]]}:{probability:.2%}'
                        (w, h), b = cv2.getTextSize(text = text,
                                fontFace = fontFace,
                                fontScale = fontScale,
                                thickness = thickness)
                        # 文字描画
                        cv2.rectangle(im_rgb,(xmin, ymin),(xmin + w, ymin + h),(234, 202, 10),thickness=-1)
                        cv2.putText(im_rgb,
                            text=text,
                            org=(xmin, ymin + h),
                            fontFace=fontFace,
                            fontScale=fontScale,
                            color=(255, 255, 255),
                            thickness=thickness,
                            lineType=cv2.LINE_4)

    out_filepath = os.path.join(os.path.join('static/ai', 'img'), 'out.jpg')
    cv2.imwrite(out_filepath, im_rgb)
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