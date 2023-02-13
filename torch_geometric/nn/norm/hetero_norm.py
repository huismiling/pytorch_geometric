import torch
from torch import Tensor
from torch_geometric.nn.to_hetero_module import ToHeteroLinear
from torch_geometric.nn.typing import Metadata


class HeteroNorm(torch.nn.Module):
    r"""Applies normalization over node features for each node type using:
    BatchNorm <https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.nn.norm.BatchNorm.html#torch_geometric.nn.norm.BatchNorm>,
    InstanceNorm <https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.nn.norm.InstanceNorm.html#torch_geometric.nn.norm.InstanceNorm>,
    or LayerNorm <https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.nn.norm.LayerNorm.html#torch_geometric.nn.norm.LayerNorm>

    Args:
        in_channels (int): Size of each input sample.
        norm_type (str): Which of "BatchNorm", "InstanceNorm", "LayerNorm" to use
            (default: "BatchNorm")
        eps (float, optional): A value added to the denominator for numerical
            stability. (default: :obj:`1e-5`)
        momentum (float, optional): The value used for the running mean and
            running variance computation. (default: :obj:`0.1`)
        affine (bool, optional): If set to :obj:`True`, this module has
            learnable affine parameters :math:`\gamma` and :math:`\beta`.
            (default: :obj:`True`)
        track_running_stats (bool, optional): If set to :obj:`True`, this
            module tracks the running mean and variance, and when set to
            :obj:`False`, this module does not track such statistics and always
            uses batch statistics in both training and eval modes.
            (default: :obj:`True`)
        allow_single_element (bool, optional): If set to :obj:`True`, batches
            with only a single element will work as during in evaluation.
            That is the running mean and variance will be used.
            Requires :obj:`track_running_stats=True`. (default: :obj:`False`)
    """
    def __init__(self, in_channels: int, norm_type: str, metadata: Metadata, eps: float = 1e-5,
                 momentum: float = 0.1, affine: bool = True,
                 track_running_stats: bool = True,
                 allow_single_element: bool = False):
        super().__init__()
        if not norm_type.lower() in ["batchnorm", "instancenorm", "layernorm"]:
            raise ValueError('Please choose norm type from "BatchNorm", "InstanceNorm", "LayerNorm"')
        if allow_single_element and not track_running_stats:
            raise ValueError("'allow_single_element' requires "
                             "'track_running_stats' to be set to `True`")
        self.in_channels = in_channels
        self.hetero_linear = ToHeteroLinear(Linear(self.in_channels, self.in_channels), metadata)
        self.allow_single_element = allow_single_element

    def reset_parameters(self):
        r"""Resets all learnable parameters of the module."""
        self.module.reset_parameters()

    def forward(self, x: Tensor) -> Tensor:
        r"""
        Args:
            x (torch.Tensor): The source tensor.
        """
        if self.allow_single_element and x.size(0) <= 1:
            return torch.nn.functional.batch_norm(
                x,
                self.module.running_mean,
                self.module.running_var,
                self.module.weight,
                self.module.bias,
                False,  # bn_training
                0.0,  # momentum
                self.module.eps,
            )
        return self.module(x)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.module.num_features})'
