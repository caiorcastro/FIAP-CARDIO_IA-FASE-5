import json, time, random
from pathlib import Path
import torch
from torch import nn, optim
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms, models
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, classification_report

root = Path('FASE4')
data_dir = root / 'data' / 'raw' / 'chest_xray'
reports = root / 'reports'
app_dir = root / 'app'
class_names = ['NORMAL', 'PNEUMONIA']
img_size = (128, 128)
batch_size = 32
num_epochs = 3
max_train = 800
max_val = 400

normalize = transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
transform = transforms.Compose([
    transforms.Resize(img_size),
    transforms.ToTensor(),
    normalize,
])

train_ds_full = datasets.ImageFolder(data_dir / 'train', transform=transform)
val_ds_full = datasets.ImageFolder(data_dir / 'val', transform=transform)

train_indices = list(range(len(train_ds_full)))
val_indices = list(range(len(val_ds_full)))
random.seed(42)
random.shuffle(train_indices)
random.shuffle(val_indices)
train_ds = Subset(train_ds_full, train_indices[:max_train])
val_ds = Subset(val_ds_full, val_indices[:max_val])

train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

device = torch.device('cpu')

try:
    weights = models.ResNet18_Weights.DEFAULT
except Exception:
    weights = None
model = models.resnet18(weights=weights)
for p in model.parameters():
    p.requires_grad = False
in_features = model.fc.in_features
model.fc = nn.Linear(in_features, len(class_names))
model = model.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.fc.parameters(), lr=1e-3)

history=[]
start=time.time()
for epoch in range(num_epochs):
    model.train(); total_loss=total_acc=total_samples=0
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        logits = model(images)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()
        bs = labels.size(0)
        total_loss += loss.item()*bs
        total_acc += (torch.argmax(logits,1)==labels).float().sum().item()
        total_samples += bs
    tr_loss = total_loss/total_samples
    tr_acc = total_acc/total_samples

    model.eval(); v_loss=v_acc=v_samples=0; preds_list=[]; labels_list=[]
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            logits = model(images)
            loss = criterion(logits, labels)
            bs = labels.size(0)
            v_loss += loss.item()*bs
            v_acc += (torch.argmax(logits,1)==labels).float().sum().item()
            v_samples += bs
            preds_list.append(torch.argmax(logits,1).cpu())
            labels_list.append(labels.cpu())
    val_loss = v_loss/v_samples
    val_acc = v_acc/v_samples
    preds = torch.cat(preds_list)
    labels_cat = torch.cat(labels_list)
    history.append({'epoch': epoch+1, 'train_loss': tr_loss, 'train_acc': tr_acc, 'val_loss': val_loss, 'val_acc': val_acc})
    print(f"[TL] Epoch {epoch+1}/{num_epochs} train_loss={tr_loss:.4f} acc={tr_acc:.3f} val_loss={val_loss:.4f} acc={val_acc:.3f}")

cm = confusion_matrix(labels_cat.numpy(), preds.numpy(), labels=list(range(len(class_names))))
report = classification_report(labels_cat.numpy(), preds.numpy(), target_names=class_names, output_dict=True, zero_division=0)

reports.mkdir(parents=True, exist_ok=True)
fig, ax = plt.subplots(figsize=(4,4))
ax.imshow(cm, cmap='Blues')
ax.set_xticks(range(len(class_names)))
ax.set_yticks(range(len(class_names)))
ax.set_xticklabels(class_names, rotation=45, ha='right')
ax.set_yticklabels(class_names)
for i in range(cm.shape[0]):
    for j in range(cm.shape[1]):
        ax.text(j, i, cm[i, j], ha='center', va='center', color='black')
ax.set_xlabel('Predito'); ax.set_ylabel('Verdadeiro'); ax.set_title('Matriz de confusao (ResNet18 subset)')
fig.tight_layout()
confusion_path = reports / 'confusion_matrix_transfer.png'
fig.savefig(confusion_path, dpi=150)
plt.close(fig)

fig2, ax2 = plt.subplots()
ax2.plot([h['epoch'] for h in history], [h['train_loss'] for h in history], label='train_loss')
ax2.plot([h['epoch'] for h in history], [h['val_loss'] for h in history], label='val_loss')
ax2.set_xlabel('Epoch'); ax2.set_ylabel('Loss'); ax2.legend(); ax2.set_title('Curvas de treino (ResNet18 subset)')
fig2.tight_layout()
curve_path = reports / 'training_curves_transfer.png'
fig2.savefig(curve_path, dpi=150)
plt.close(fig2)

metrics = {
    'class_names': class_names,
    'history': history,
    'classification_report': report,
    'confusion_matrix': cm.tolist(),
    'note': f"Transfer learning ResNet18 (weights={'DEFAULT' if weights is not None else 'None'}), subset train={len(train_ds)} val={len(val_ds)}, epochs={num_epochs}, img_size={img_size}, bs={batch_size}"
}
with open(reports/'metrics_transfer.json', 'w', encoding='utf-8') as f:
    json.dump(metrics, f, ensure_ascii=False, indent=2)

model_path = app_dir / 'model.pt'
torch.save(model, model_path)
print('Artefatos TL salvos:', confusion_path, curve_path, reports/'metrics_transfer.json', model_path)
print('Tempo total: %.1fs' % (time.time()-start))
