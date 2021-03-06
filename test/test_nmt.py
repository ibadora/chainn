import unittest
import numpy as np
from os import path
from subprocess import check_call
from chainer import optimizers
from chainn.test import TestCase
from chainn.util import Vocabulary
from chainn.util.io import load_nmt_train_data, ModelSerializer
from chainn.classifier import EncDecNMT

class Args(object):
    def __init__(self, model):
        self.hidden = 5
        self.use_cpu = True
        self.embed = 6
        self.model = model
        self.depth = 2
        self.init_model = False

class InitArgs(object):
    def __init__(self, init):
        self.init_model = init

class TestNMT(TestCase):
    def setUp(self):
        self.data = path.join(path.dirname(__file__), "data")
        self.script = path.join(path.dirname(__file__),"script")
       
        # Run
        script    = path.join(self.script, "execute_nmt.sh")
        script_ont = path.join(self.script, "execute_nmt_one.sh")
        src       = path.join(self.data, "nmt.en")
        trg       = path.join(self.data, "nmt.ja")
        test      = path.join(self.data, "nmt-test.en")
        train_nmt = path.join("train-nmt.py")
        test_nmt  = path.join("nmt.py")
        self.run = lambda x, y: check_call([script, src, trg, test, train_nmt, test_nmt, x, y])
        self.run_one = lambda x, y: check_call([script_ont, src, trg, test, train_nmt, test_nmt, x, y]) 
        
    def test_NMT_3_read_train(self):
        src=["I am Philip", "I am a student"]
        trg=["私 は フィリップ です", "私 は 学生 です"]
        SRC, TRG, data = load_nmt_train_data(src, trg, cut_threshold=1)
        x_exp = Vocabulary(unk=True, eos=True)
        y_exp = Vocabulary(unk=True, eos=True)
        
        for w in "i am".split():
            x_exp[w]

        for w in "私 は です".split():
            y_exp[w]
        x_data_exp = [\
                [x_exp["i"], x_exp["am"], x_exp.unk_id(), x_exp.eos_id()], \
                [x_exp["i"], x_exp["am"], x_exp.unk_id(), x_exp.unk_id(), x_exp.eos_id()] \
        ]

        y_data_exp = [\
                [y_exp["私" ], y_exp["は" ], y_exp.unk_id(), y_exp["です"], y_exp.eos_id()], \
                [y_exp["私" ], y_exp["は" ], y_exp.unk_id(), y_exp["です"], y_exp.eos_id()] \
        ]

        data_exp = list(zip(x_data_exp, y_data_exp))
        self.assertVocEqual(SRC, x_exp)
        self.assertVocEqual(TRG, y_exp)
        self.assertEqual(data, data_exp)
    
    def test_NMT_2_read_write(self):
        for model in ["encdec", "attn"]:
            src_voc = Vocabulary()
            trg_voc = Vocabulary()
            for tok in "</s> I am Philip".split():
                src_voc[tok]
            for tok in "</s> 私 は フィリップ です".split():
                trg_voc[tok]
            model = EncDecNMT(Args(model), src_voc, trg_voc, optimizer=optimizers.SGD())
    
            model_out = "/tmp/nmt/tmp"
            X, Y  = src_voc, trg_voc
            
            # Train with 1 example
            src = np.array([[X["I"], X["am"], X["Philip"]]], dtype=np.int32)
            trg = np.array([[Y["私"], Y["は"], Y["フィリップ"], Y["です"]]], dtype=np.int32)
            
            model.train(src, trg)
                
            # Save
            serializer = ModelSerializer(model_out)
            serializer.save(model)
    
            # Load
            model1 = EncDecNMT(InitArgs(model_out))
                
            # Check
            self.assertModelEqual(model._model, model1._model)

    def test_NMT_encdec(self):
        self.run("encdec", "")

    def test_NMT_attn_dot(self):
        self.run("attn", "--attention_type dot")
    
    def test_NMT_attn_general(self):
        self.run("attn", "--attention_type general")

    def test_NMT_attn_concat(self):
        self.run("attn", "--attention_type concat")

    def test_NMT_dictattn(self):
        self.run("dictattn", "--dict test/data/dict.txt")
    
    def test_NMT_dictattn_bias(self):
        self.run("dictattn", "--dict test/data/dict.txt --dict_method bias")
    
    def test_NMT_dictattn_linear(self):
        self.run("dictattn", "--dict test/data/dict.txt --dict_method linear")
    
    def test_NMT_dictattn_caching(self):
        self.run("dictattn", "--dict test/data/dict.txt --dict_caching")

    def test_NMT_dictattn_caching(self):
        self.run("dictattn", "--dict test/data/dict.txt --dict_caching")

    def test_NMT_one(self):
        self.run_one("attn", "--attention_type dot")

if __name__ == "__main__":
    unittest.main()
