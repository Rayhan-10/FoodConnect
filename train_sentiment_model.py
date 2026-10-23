"""Optional Phase 8 trainer: train a tiny review sentiment model and export TFLite.

Requires TensorFlow: python -m pip install tensorflow
Run: python train_sentiment_model.py
This is an educational starter model, not a production-quality sentiment model.
"""
import json
from pathlib import Path
import tensorflow as tf

ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / 'models'
MODEL_DIR.mkdir(exist_ok=True)

# Small illustrative starter corpus. Expand and label a real dataset for research use.
texts = [
    'Amazing food and very friendly staff', 'The meal was delicious and fresh',
    'Great taste and excellent service', 'Loved the ambience and tasty food',
    'Wonderful experience, highly recommend', 'The best restaurant in the area',
    'Very good food, I will come again', 'Perfect dinner and helpful staff',
    'Food was awful and the service was rude', 'The meal was cold and bland',
    'Terrible experience, very disappointing', 'Overpriced food and slow service',
    'Dirty tables and stale food', 'Worst restaurant, never coming back',
    'Poor service and bad taste', 'The food was horrible',
    'It was okay, nothing special', 'Average food and normal service',
    'The place was fine', 'Not bad but not amazing',
    'A regular meal at a regular place', 'The experience was neither good nor bad',
]
# 0=negative, 1=neutral, 2=positive
labels = [2,2,2,2,2,2,2,2,0,0,0,0,0,0,0,0,1,1,1,1,1,1]

vectorizer = tf.keras.layers.TextVectorization(max_tokens=1200, output_mode='int', output_sequence_length=40, standardize='lower_and_strip_punctuation')
vectorizer.adapt(tf.data.Dataset.from_tensor_slices(texts).batch(8))
vocab = vectorizer.get_vocabulary()
model = tf.keras.Sequential([
    tf.keras.Input(shape=(), dtype=tf.string),
    vectorizer,
    tf.keras.layers.Embedding(len(vocab), 16, mask_zero=True),
    tf.keras.layers.GlobalAveragePooling1D(),
    tf.keras.layers.Dense(16, activation='relu'),
    tf.keras.layers.Dense(3, activation='softmax'),
])
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
model.fit(tf.constant(texts), tf.constant(labels), epochs=35, verbose=0)
# Convert a model accepting integer token sequences, so inference can use the saved vocabulary.
input_model = tf.keras.Sequential([
    tf.keras.Input(shape=(40,), dtype=tf.int32),
    *model.layers[1:]
])
converter = tf.lite.TFLiteConverter.from_keras_model(input_model)
(MODEL_DIR / 'sentiment.tflite').write_bytes(converter.convert())
(MODEL_DIR / 'sentiment_vocab.json').write_text(json.dumps({word: i for i, word in enumerate(vocab)}, ensure_ascii=False, indent=2), encoding='utf-8')
print('Created models/sentiment.tflite and models/sentiment_vocab.json')
