import argparse
import os
import cv2
import numpy as np
import torch
import face_recognition
import dlib
import glob
import yaml
from PIL import Image
from decord import VideoReader, cpu
from torchvision import transforms
from tqdm import tqdm

from model.genconvit import GenConViT

device = "cuda" if torch.cuda.is_available() else "cpu"

def face_rec(frames):
    temp_face = np.zeros((len(frames), 224, 224, 3), dtype=np.uint8)
    count = 0
    mod = "cnn" if dlib.DLIB_USE_CUDA else "hog"
    
    for _, frame in tqdm(enumerate(frames), total=len(frames)):
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        face_locations = face_recognition.face_locations(
            frame, number_of_times_to_upsample=0, model=mod
        )

        for face_location in face_locations:
            if count < len(frames):
                top, right, bottom, left = face_location
                face_image = frame[top:bottom, left:right]
                face_image = cv2.resize(
                    face_image, (224, 224), interpolation=cv2.INTER_AREA
                )
                face_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

                temp_face[count] = face_image
                count += 1
            else:
                break

    return ([], 0) if count == 0 else (temp_face[:count], count)

def preprocess_frame(frame):
    df_tensor = torch.tensor(frame, device=device).float()
    df_tensor = df_tensor.permute((0, 3, 1, 2))
    
    normalize_vid = transforms.Compose([transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    for i in range(len(df_tensor)):
        df_tensor[i] = normalize_vid(df_tensor[i] / 255.0)

    return df_tensor

def pred_vid(df, model):
    with torch.no_grad():
        y_pred = torch.sigmoid(model(df).squeeze())
        mean_val = torch.mean(y_pred, dim=0)
        idx = torch.argmax(mean_val).item()
        val = torch.max(mean_val).item()
        return idx, val

def extract_frames(video_file, num_frames=15):
    vr = VideoReader(video_file, ctx=cpu(0))
    total_frames = len(vr)

    if num_frames == -1: 
        indices = np.arange(total_frames).astype(int)
    else:
        indices = np.linspace(0, total_frames -1, num_frames, dtype=int) 
    
    return vr.get_batch(indices).asnumpy()

def main():
    parser = argparse.ArgumentParser("Simple GenConViT Single Video Inference")
    parser.add_argument("video_path", type=str, help="Path to the video file or folder of extracted frames")
    parser.add_argument("--num_frames", type=int, default=15, help="Number of frames to extract and test")
    parser.add_argument("--net", type=str, default="genconvit", choices=["genconvit", "ed", "vae"], help="Network block to use")
    parser.add_argument("--ed_weight", type=str, default="genconvit_ed_inference", help="ED weight name")
    parser.add_argument("--vae_weight", type=str, default="genconvit_vae_inference", help="VAE weight name")
    parser.add_argument("--fp16", action="store_true", help="Use half precision")
    args = parser.parse_args()

    if not os.path.exists(args.video_path):
        print(f"Error: Path '{args.video_path}' does not exist.")
        return

    # 1) Load Config locally!
    with open(os.path.join('model', 'config.yaml')) as file:
        config = yaml.safe_load(file)

    # 2) Load Model natively!
    print(f"\n[1] Loading {args.net} model weights...")
    model = GenConViT(
        config,
        ed=args.ed_weight,
        vae=args.vae_weight, 
        net=args.net,
        fp16=args.fp16
    )
    model.to(device)
    model.eval()
    if args.fp16:
        model.half()

    print(f"[2] Extracting and preprocessing faces from: {args.video_path}...")
    
    # 3) Extract Frames and Faces
    df = []
    if os.path.isdir(args.video_path):
        img_list = glob.glob(os.path.join(args.video_path, "*"))
        img = []
        for f in img_list:
            try:
                im = Image.open(f).convert('RGB')
                img.append(np.asarray(im))
            except Exception:
                pass
        face, count = face_rec(img[:args.num_frames])
        df = preprocess_frame(face) if count > 0 else []
    elif os.path.isfile(args.video_path) and args.video_path.lower().endswith((".avi", ".mp4", ".mpg", ".mpeg", ".mov")):
        img = extract_frames(args.video_path, args.num_frames)
        face, count = face_rec(img)
        df = preprocess_frame(face) if count > 0 else []
    else:
        print("Error: Invalid video file format provided. Must be a folder or a valid video (.mp4, .avi, etc)")
        return
        
    if len(df) == 0:
        print("No faces detected in the video! Cannot make a prediction.")
        return

    if args.fp16:
        df = df.half()

    print("[3] Running inference...")
    y, y_val = pred_vid(df, model)
    
    # In model training, Class 0 = FAKE, Class 1 = REAL
    label = "REAL" if y == 1 else "FAKE"
    
    print("\n" + "=" * 40)
    print(f"  PREDICTION: {label}")
    print(f"  CONFIDENCE: {y_val:.4f} ({(y_val * 100):.2f}%)")
    print("=" * 40 + "\n")

if __name__ == "__main__":
    main()
