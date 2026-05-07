"""
Train MobileNetV2 model on the downloaded cattle/buffalo breed dataset.

Usage:
    python download_dataset.py   # first download images
    python train.py              # then train

Output:
    buffalo_breed_model.h5   — trained Keras model
    classes.txt              — breed names in index order
"""

import os
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2

# ── Config ─────────────────────────────────────────────────────────────────────
IMG_SIZE    = (224, 224)
BATCH_SIZE  = 16
EPOCHS      = 20
DATASET_DIR = os.path.join(os.path.dirname(__file__), "dataset")
MODEL_OUT   = os.path.join(os.path.dirname(__file__), "buffalo_breed_model.h5")
CLASSES_OUT = os.path.join(os.path.dirname(__file__), "classes.txt")

# ── Model ──────────────────────────────────────────────────────────────────────
def build_model(num_classes):
    base = MobileNetV2(input_shape=(224, 224, 3), include_top=False, weights="imagenet")
    base.trainable = False  # freeze base, only train top layers

    model = models.Sequential([
        base,
        layers.GlobalAveragePooling2D(),
        layers.Dense(256, activation="relu"),
        layers.Dropout(0.3),
        layers.Dense(num_classes, activation="softmax"),
    ])
    return model

# ── Train ──────────────────────────────────────────────────────────────────────
def train():
    if not os.path.exists(DATASET_DIR):
        print(f"❌ Dataset not found at {DATASET_DIR}")
        print("   Run: python download_dataset.py")
        return

    # Count breeds
    breeds = sorted([
        d for d in os.listdir(DATASET_DIR)
        if os.path.isdir(os.path.join(DATASET_DIR, d))
    ])
    print(f"✅ Found {len(breeds)} breeds: {breeds}")

    # Data generators
    datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True,
        zoom_range=0.15,
        brightness_range=[0.8, 1.2],
        validation_split=0.2,
    )

    train_gen = datagen.flow_from_directory(
        DATASET_DIR,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="training",
        shuffle=True,
    )

    val_gen = datagen.flow_from_directory(
        DATASET_DIR,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="validation",
        shuffle=False,
    )

    num_classes = len(train_gen.class_indices)
    print(f"✅ Classes ({num_classes}): {train_gen.class_indices}")

    model = build_model(num_classes)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks = [
        tf.keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=3, verbose=1),
        tf.keras.callbacks.ModelCheckpoint(MODEL_OUT, save_best_only=True, verbose=1),
    ]

    print(f"\n🚀 Training for up to {EPOCHS} epochs...")
    model.fit(
        train_gen,
        epochs=EPOCHS,
        validation_data=val_gen,
        callbacks=callbacks,
    )

    # Save classes in index order (CRITICAL — must match model output)
    sorted_classes = sorted(train_gen.class_indices.keys(),
                            key=lambda c: train_gen.class_indices[c])
    with open(CLASSES_OUT, "w") as f:
        for cls in sorted_classes:
            f.write(f"{cls}\n")

    print(f"\n✅ Model saved: {MODEL_OUT}")
    print(f"✅ Classes saved: {CLASSES_OUT}")
    print(f"   Classes: {sorted_classes}")

    # Quick eval
    loss, acc = model.evaluate(val_gen, verbose=0)
    print(f"\n📊 Validation accuracy: {acc * 100:.1f}%")

if __name__ == "__main__":
    train()
