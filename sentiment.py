"""FoodConnect Phase 8 sentiment analysis.

When models/sentiment.tflite and models/sentiment_vocab.json exist, use the
TensorFlow Lite model. If they are not present, use a small explainable lexical
baseline so local demos still run without TensorFlow installed.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / 'models' / 'sentiment.tflite'
VOCAB_PATH = ROOT / 'models' / 'sentiment_vocab.json'
SEQUENCE_LENGTH = 40
_interpreter = None
_vocab = None

POSITIVE = {
    'amazing', 'awesome', 'beautiful', 'best', 'delicious', 'excellent', 'fantastic',
    'fresh', 'friendly', 'good', 'great', 'love', 'loved', 'perfect', 'recommend',
    'tasty', 'wonderful', 'yummy', 'ভালো', 'দারুণ', 'সুস্বাদু', 'চমৎকার'
}
NEGATIVE = {
    'awful', 'bad', 'bland', 'cold', 'disappointing', 'dirty', 'expensive', 'horrible',
    'late', 'mediocre', 'overpriced', 'poor', 'rude', 'slow', 'stale', 'terrible',
    'worst', 'খারাপ', 'বাজে'
}


def _load_tflite():
    global _interpreter, _vocab
    if _interpreter is not None:
        return _interpreter, _vocab
    if not MODEL_PATH.exists() or not VOCAB_PATH.exists():
        return None, None
    try:
        try:
            from tflite_runtime.interpreter import Interpreter
        except ImportError:
            from tensorflow.lite import Interpreter
        _interpreter = Interpreter(model_path=str(MODEL_PATH))
        _interpreter.allocate_tensors()
        _vocab = json.loads(VOCAB_PATH.read_text(encoding='utf-8'))
        return _interpreter, _vocab
    except Exception as exc:
        print(f'[FoodConnect sentiment] TFLite model unavailable; using lexical fallback: {exc}')
        return None, None


def _predict_tflite(text, interpreter, vocab):
    import numpy as np
    inputs = interpreter.get_input_details()
    outputs = interpreter.get_output_details()
    tokens = re.findall(r"[a-zA-Z]+|[\u0980-\u09FF]+", (text or '').lower())
    ids = [vocab.get(token, vocab.get('[UNK]', 1)) for token in tokens[:SEQUENCE_LENGTH]]
    ids += [0] * (SEQUENCE_LENGTH - len(ids))
    input_detail = inputs[0]
    dtype = input_detail['dtype']
    array = np.asarray([ids], dtype=dtype)
    interpreter.set_tensor(input_detail['index'], array)
    interpreter.invoke()
    scores = interpreter.get_tensor(outputs[0]['index'])[0]
    labels = ['negative', 'neutral', 'positive']
    return labels[int(scores.argmax())]


def analyze_sentiment(text):
    """Return positive, neutral, or negative for a review."""
    interpreter, vocab = _load_tflite()
    if interpreter and vocab:
        try:
            return _predict_tflite(text, interpreter, vocab)
        except Exception as exc:
            print(f'[FoodConnect sentiment] TFLite inference failed; using lexical fallback: {exc}')
    cleaned = (text or '').lower()
    tokens = re.findall(r"[a-zA-Z]+|[\u0980-\u09FF]+", cleaned)
    pos = sum(1 for token in tokens if token in POSITIVE)
    neg = sum(1 for token in tokens if token in NEGATIVE)
    if pos > neg:
        return 'positive'
    if neg > pos:
        return 'negative'
    return 'neutral'
