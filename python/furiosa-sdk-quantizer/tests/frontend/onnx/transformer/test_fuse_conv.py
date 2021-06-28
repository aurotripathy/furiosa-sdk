from abc import ABC

import os

# FIXME Without this environ setting, the following error occurred on Mac OS:
# OMP: Error #15: Initializing libomp.dylib, but found libiomp5.dylib already initialized.
# OMP: Hint This means that multiple copies of the OpenMP runtime have been linked into the program. \
# That is dangerous, since it can degrade performance or cause incorrect results. \
# The best thing to do is to ensure that only a single OpenMP runtime is linked into the process, \
# e.g. by avoiding static linking of the OpenMP runtime in any library. As an unsafe, unsupported, \
# undocumented workaround you can set the environment variable KMP_DUPLICATE_LIB_OK=TRUE \
# to allow the program to continue to execute, but that may cause crashes or silently produce incorrect results. \
# For more information, please see http://openmp.llvm.org/
#
# Process finished with exit code 134 (interrupted by signal 6: SIGABRT)
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

import torch
import torch.nn as nn

from furiosa_sdk_quantizer.frontend.onnx.transformer.fuse_conv import FuseConv
from tests.frontend.onnx.transformer import TestTransformer


# TODO 1. Generate test model that does not meet conditions for conv fusion
# TODO 2. Generate MatMul + Add test model directly by onnx
class UnitTestModel(nn.Module, ABC):
    def __init__(self, in_channel, out_channel):
        super(UnitTestModel, self).__init__()
        self.linear = nn.Linear(in_features=in_channel, out_features=out_channel, bias=False)

    def forward(self, x):
        x = self.linear(x)
        x = torch.add(x, torch.ones(x.shape))
        return x


class UnitTestModel1(nn.Module, ABC):
    def __init__(self, in_channel, out_channel):
        super(UnitTestModel1, self).__init__()
        self.linear = nn.Linear(in_features=in_channel, out_features=out_channel, bias=True)

    def forward(self, x):
        x = self.linear(x)
        return x


class MultiTestModel(UnitTestModel):
    def __init__(self, in_channel, out_channel):
        super(MultiTestModel, self).__init__(in_channel, out_channel)

    def forward(self, x):
        x = torch.mul(x, torch.ones(x.shape))
        x = self.linear(x)
        x = torch.add(x, torch.ones(x.shape))
        x = torch.add(x, torch.ones(x.shape))
        return x


class MultiTestModel1(UnitTestModel1):
    def __init__(self, in_channel, out_channel):
        super(MultiTestModel1, self).__init__(in_channel, out_channel)

    def forward(self, x):
        x = torch.mul(x, torch.ones(x.shape))
        x = self.linear(x)
        x = torch.add(x, torch.ones(x.shape))
        return x


class TestFuseConv(TestTransformer, ABC):
    def _make_test_model(self, torch_model, input_shapes):
        orig_model, trans_model = self.make_test_model(torch_model,
                                                       FuseConv(),
                                                       input_shapes)
        return orig_model, trans_model

    def test_case1(self):
        input_shapes = [(8, 16)]
        in_channel = 16
        out_channel = 4

        op_types = ['Unsqueeze', 'Conv', 'Squeeze']

        orig_model, trans_model = self._make_test_model(UnitTestModel(in_channel, out_channel), input_shapes)
        self.check_graph_node(trans_model, op_types)
        self.check_output_value(orig_model, trans_model, input_shapes)
        self.check_value_info(trans_model)

    def test_case2(self):
        input_shapes = [(8, 16)]
        in_channel = 16
        out_channel = 4

        op_types = ['Unsqueeze', 'Conv', 'Squeeze']

        orig_model, trans_model = self._make_test_model(UnitTestModel1(in_channel, out_channel), input_shapes)
        self.check_graph_node(trans_model, op_types)
        self.check_output_value(orig_model, trans_model, input_shapes)
        self.check_value_info(trans_model)

    def test_case3(self):
        input_shapes = [(8, 16)]
        in_channel = 16
        out_channel = 4

        op_types = ['Mul', 'Unsqueeze', 'Conv', 'Squeeze', 'Add']

        orig_model, trans_model = self._make_test_model(MultiTestModel(in_channel, out_channel), input_shapes)
        self.check_graph_node(trans_model, op_types)
        self.check_output_value(orig_model, trans_model, input_shapes)
        self.check_value_info(trans_model)

    def test_case4(self):
        input_shapes = [(8, 16)]
        in_channel = 16
        out_channel = 4

        op_types = ['Mul', 'Unsqueeze', 'Conv', 'Squeeze', 'Add']

        orig_model, trans_model = self._make_test_model(MultiTestModel1(in_channel, out_channel), input_shapes)
        self.check_graph_node(trans_model, op_types)
        self.check_output_value(orig_model, trans_model, input_shapes)
        self.check_value_info(trans_model)
