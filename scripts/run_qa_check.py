from src.qa_engine import QAEngine
import sys, os

# Ensure python can see the root
sys.path.append(os.getcwd())

qa = QAEngine()
video_path = "output/20261003_130040_405188_long.mp4"
score = qa.analyze_video(video_path)
print(f"Video QA Score Final: {score*100:.2f}%")
