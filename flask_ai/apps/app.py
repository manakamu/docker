from flask import Flask, url_for
from markupsafe import escape
from flask import request
from flask import render_template
import datetime
from pathlib import Path
#クライアントの命名したファイル名を利用するためのsecure_filename()
from werkzeug.utils import secure_filename

import cv2
from matplotlib import pyplot as plt
from retinaface.pre_trained_models import get_model
from retinaface.utils import vis_annotations
import os

import torch
import torchvision
from torchvision import transforms
import torch.nn as nn
from torch.nn import functional as F
from PIL import Image
import tracemalloc

app = Flask(__name__)
app.config["SECRET_ KEY"] = "2AZSMss3p5QPbcY2hBsJ"

@app.route('/upload', methods=['POST', 'GET'])
def upload_file():
    if request.method == 'POST':
        file = request.files["the_file"]
        # 保存時のファイル名を現在時刻に変更する
        ext = Path(file.filename).suffix
        now = datetime.datetime.now()
        fname = now.strftime('%Y%m%d%H%M%S') + ext

        # uploadsフォルダは外部公開できない
        file.save('./uploads/' + secure_filename(fname))
        path = os.path.join('uploads', fname)
        # 外部公開できるstaticフォルダに保存する
        out_filepath = os.path.join(os.path.join('static', 'IMG'), 'out.jpg')
        face_detect(path, out_filepath)
        face_recognition(path)

        #アップロードしてサーバーにファイルが保存されたらfinishedを表示
        return render_template('finished.html', filepath = out_filepath)
    else:
    	#GETでアクセスされた時、uploadsを表示
    	return render_template('upload.html')

def face_detect(inPath, outPath):
    model = get_model("resnet50_2020-07-20", max_size=2048)
    model.eval()

    image = cv2.imread(inPath)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = model.predict_jsons(image)
    image_out = draw_res(image,results)
    cv2.imwrite(outPath, image_out)

def face_recognition(inFile):
    tracemalloc.start()

    model_detect = torchvision.models.resnet18(pretrained=True)
    num_ftrs = model_detect.fc.in_features
    model_detect.fc = nn.Linear(num_ftrs, 3)

    model_detect.load_state_dict(torch.load(os.path.join('static', 'model_gpu.pth')))

    # デバイスを選択する。
    device = get_device(use_gpu=True)

    model_detect.to(device)
    # 推論モード
    model_detect.eval()

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
    img = Image.open(inFile)
    inputs = transform(img)
    inputs = inputs.unsqueeze(0).to(device)
    outputs = model_detect(inputs)

    batch_probs = F.softmax(outputs, dim=1)
    batch_probs, batch_indices = batch_probs.sort(dim=1, descending=True)

    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')

    print("[ Top 10 ]")
    for stat in top_stats[:10]:
        print(stat)

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