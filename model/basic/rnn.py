import numpy as np

import chainer.functions as F
import chainer.functions as L

from chainer import Variable
from chainn import Vocabulary
from . import ChainnBasicModel

class RNN(ChainnBasicModel):
    name = "rnn"

    def __init__(self, src_voc, trg_voc, args, activation=F.tanh, xp=np):
        super(RNN, self).__init__(
            *self._generate_layer(args.input, args.output, args.hidden, args.depth, args.embed)
        )
        self._input   = args.input
        self._output  = args.output
        self._hidden  = args.hidden
        self._depth   = args.depth
        self._embed   = args.embed
        self._h       = None
        self._src_voc = src_voc
        self._trg_voc = trg_voc
        self._activation = activation
        self._xp      = xp

    def reset_state(self, batch=1):
        self._h = Variable(self._xp.zeros((batch, self._hidden), dtype=np.float32))

    def __call__(self, word, update=True):
        if self._h is None:
            raise Exception("Need to call reset_state() before using the model!")
        embed  = self[0]
        e_to_h = self[1]
        h_to_h = self[2]
        h_to_y = self[-1]
        f = self._activation
        x = embed(word)
        h = e_to_h(x) + h_to_h(self._h)
        for i in range(3,len(self)-1):
            h = self[i](h)
        if update:
            self._h = h
        y = f(h_to_y(h))
        return y

    # PROTECTED
    def _generate_layer(self, input, output, hidden, depth, embed):
        assert(depth >= 1)
        ret = []
        ret.append(L.EmbedID(input, embed))
        for i in range(depth+1):
            start = embed if i == 0 else hidden
            ret.append(L.Linear(start, hidden))
        ret.append(L.Linear(hidden, output))
        return ret

