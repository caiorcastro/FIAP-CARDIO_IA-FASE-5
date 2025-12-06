from pathlib import Path
from typing import Dict, List

import torch
from flask import Flask, jsonify, request
from PIL import Image
from torchvision import transforms

# Ajuste conforme o modelo salvo pelo notebook (torch.save).
# Exemplo no notebook: torch.save(model, \"FASE4/app/model.pt\")
MODEL_PATH = Path(__file__).resolve().parent / "model.pt"
# Defina class names apos treinar (mesma ordem usada na rede).
CLASS_NAMES: List[str] = ["normal", "pneumonia"]

device = torch.device("cpu")

preprocess = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)


def load_model():
    if MODEL_PATH.exists():
        try:
            # weights_only=False porque salvamos o modelo inteiro (torch.save(model))
            model = torch.load(MODEL_PATH, map_location=device, weights_only=False)
            model.eval()
            return model
        except Exception as exc:
            print(f"[warn] Nao foi possivel carregar model.pt ({exc})")
    return None


model = load_model()
app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "model_loaded": model is not None, "classes": CLASS_NAMES})


@app.post("/predict")
def predict():
    if "file" not in request.files:
        return jsonify({"error": "expected file field"}), 400
    file = request.files["file"]
    img = Image.open(file.stream).convert("RGB")
    tensor = preprocess(img).unsqueeze(0).to(device)

    if model is None:
        probs = {c: round(1.0 / len(CLASS_NAMES), 3) for c in CLASS_NAMES}
        return jsonify({"warning": "model.pt not found, returning dummy probs", "probs": probs})

    with torch.no_grad():
        logits = model(tensor)
        prob_tensor = torch.softmax(logits, dim=1)[0]

    classes = CLASS_NAMES if len(CLASS_NAMES) == prob_tensor.numel() else [str(i) for i in range(prob_tensor.numel())]
    probs: Dict[str, float] = {cls: round(prob_tensor[i].item(), 4) for i, cls in enumerate(classes)}
    top_class = max(probs, key=probs.get)
    return jsonify({"top_class": top_class, "probs": probs})


if __name__ == "__main__":
    app.run(debug=True)
