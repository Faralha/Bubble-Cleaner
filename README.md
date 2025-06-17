
# Fast Bubble Cleaner

Bubble Cleaner untuk manga menggunakan model YOLOv11-segmented, untuk inferensi yang lebih cepat dan ringan, selagi mempertahankan akurasi deteksi yang tinggi. GPU tidak diperlukan (CPU saja cukup!).

Bubble Cleaner for manga using the YOLOv11-segmented model, optimized for faster and lighter inference while maintaining high detection accuracy. A GPU isn't needed (Just CPU is enough!).
## Class Detection Features

- Ellipse / Bubble default
- Polygon
- Square / Narrative Dialogue
- Thorns / Shout (kurang dataset)


## Demo

![H-010_debug_grid2](https://github.com/user-attachments/assets/495a8bc0-008f-4a75-af25-1d49496bc9cc)

## Training Model


## To-Do List
- Increase Dataset Variations
- Improve Post-processing, especially for joined bubble

## Run Locally

Clone the project

```bash
  git clone https://github.com/faralha/bubble-cleaner.git
```

Go to the project directory

```bash
  cd Bubble-Cleaner
```

Configure path
```
This file was imported from google collab, and all the training dataset and models were assumed stored in Drive. Change this accordingly.

For Training: Configure Dataset Path
For Inference: Configure Models Path
```

Run Notebook

- train.ipynb for Training Purposes, and
- inference.ipynb for Main Usage
