"""
ONNX module tests
"""

import os
import tempfile
import unittest

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from txtai.embeddings import Embeddings
from txtai.pipeline import HFOnnx, HFTrainer, Labels, MLOnnx, Questions


class TestOnnx(unittest.TestCase):
    """
    ONNX tests
    """

    @classmethod
    def setUpClass(cls):
        """
        Create default datasets
        """

        cls.data = [{"text": "Dogs", "label": 0}, {"text": "dog", "label": 0}, {"text": "Cats", "label": 1}, {"text": "cat", "label": 1}] * 100

    def testDefault(self):
        """
        Test exporting an ONNX model with default parameters
        """

        # Export model to ONNX, use default parameters
        onnx = HFOnnx()
        model = onnx("google/bert_uncased_L-2_H-128_A-2")

        # Validate model has data
        self.assertGreater(len(model), 0)

    def testClassification(self):
        """
        Test exporting a classification model to ONNX and running inference
        """

        path = "google/bert_uncased_L-2_H-128_A-2"

        trainer = HFTrainer()
        model, tokenizer = trainer(path, self.data)

        # Output file path
        output = os.path.join(tempfile.gettempdir(), "onnx")

        # Export model to ONNX
        onnx = HFOnnx()
        model = onnx((model, tokenizer), "text-classification", output, True)

        # Test classification
        labels = Labels((model, path), dynamic=False)
        self.assertEqual(labels("cat")[0][0], 1)

    def testPooling(self):
        """
        Test exporting a pooling model to ONNX and running inference
        """

        path = "sentence-transformers/paraphrase-MiniLM-L3-v2"

        # Export model to ONNX
        onnx = HFOnnx()
        model = onnx(path, "pooling", quantize=True)

        embeddings = Embeddings({"path": model, "tokenizer": path})
        self.assertEqual(embeddings.similarity("animal", ["dog", "book", "rug"])[0][0], 0)

    def testQA(self):
        """
        Test exporting a QA model to ONNX and running inference
        """

        path = "distilbert-base-cased-distilled-squad"

        # Export model to ONNX
        onnx = HFOnnx()
        model = onnx(path, "question-answering")

        questions = Questions((model, path))
        self.assertEqual(questions(["What is the price?"], ["The price is $30"])[0], "$30")

    def testScikit(self):
        """
        Test exporting a scikit-learn model to ONNX and running inference
        """

        # pylint: disable=W0613
        def tokenizer(inputs, **kwargs):
            if isinstance(inputs, str):
                inputs = [inputs]

            return {"input_ids": [[x] for x in inputs]}

        # Train a scikit-learn model
        model = Pipeline([("tfidf", TfidfVectorizer()), ("lr", LogisticRegression())])
        model.fit([x["text"] for x in self.data], [x["label"] for x in self.data])

        # Export model to ONNX
        onnx = MLOnnx()
        model = onnx(model)

        # Test classification
        labels = Labels((model, tokenizer), dynamic=False)
        self.assertEqual(labels("cat")[0][0], 1)

    def testZeroShot(self):
        """
        Test exporting a zero shot classification model to ONNX and running inference
        """

        path = "prajjwal1/bert-medium-mnli"

        # Export model to ONNX
        onnx = HFOnnx()
        model = onnx(path, "zero-shot-classification", quantize=True)

        # Test zero shot classification
        labels = Labels((model, path))
        self.assertEqual(labels("That is great news", ["negative", "positive"])[0][0], 1)
