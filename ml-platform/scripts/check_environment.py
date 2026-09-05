import torch
import cv2
import ultralytics


print("=" * 50)

print("PyTorch:")
print(torch.__version__)

print("CUDA Available:")
print(torch.cuda.is_available())

print("OpenCV:")
print(cv2.__version__)

print("Ultralytics:")
print(ultralytics.__version__)

print("=" * 50)
