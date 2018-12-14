import torch
from torch_geometric.utils import to_batch


class Set2Set(torch.nn.Module):
    r"""Global pooling based on iterative content-based attention

    .. math::
        \mathbf{q}_t &= \mathrm{LSTM}(\mathbf{q}^{*}_{t-1})

        \alpha_{i,t} &= \mathrm{softmax}(\mathbf{x}_i \cdot \mathbf{q}_t)

        \mathbf{r}_t &= \sum_{i=1}^N \alpha_{i,t} \mathbf{x}_i

        \mathbf{q}^{*}_t &= \mathbf{q}_t \, \Vert \, \mathbf{r}_t

    where :math:`\mathbf{q}^{*}_T` defines the output of the layer with twiche
    the dimensionality as the input.

    Args:
        in_channels (int): Size of each input sample.
        processing_steps (int): Number of iterations :math:`T`.
        num_layers (int, optional): Number of recurrent layers, *.e.g*, setting
            :obj:`num_layers=2` would mean stacking two LSTMs together to form
            a stacked LSTM, with the second LSTM taking in outputs of the first
            LSTM and computing the final results. (default: :obj:`1`)
    """

    def __init__(self, in_channels, processing_steps, num_layers=1):
        super(Set2Set, self).__init__()

        self.in_channels = in_channels
        self.out_channels = 2 * in_channels
        self.processing_steps = processing_steps
        self.num_layers = num_layers

        self.lstm = torch.nn.LSTM(self.out_channels, self.in_channels,
                                  num_layers)

        self.reset_parameters()

    def reset_parameters(self):
        self.lstm.reset_parameters()

    def forward(self, x, batch):
        """"""
        x, _ = to_batch(x, batch)
        batch_size, max_nodes, _ = x.size()

        h = (x.new_zeros((self.num_layers, batch_size, self.in_channels)),
             x.new_zeros((self.num_layers, batch_size, self.in_channels)))
        q_star = x.new_zeros(1, batch_size, self.out_channels)

        for i in range(self.processing_steps):
            q, h = self.lstm(q_star, h)
            q = q.view(batch_size, 1, self.in_channels)
            e = (x * q).sum(dim=-1)  # Dot product.
            a = torch.softmax(e, dim=-1)
            a = a.view(batch_size, max_nodes, 1)
            r = (a * x).sum(dim=1, keepdim=True)
            q_star = torch.cat([q, r], dim=-1)
            q_star = q_star.view(1, batch_size, self.out_channels)

        q_star = q_star.view(batch_size, self.out_channels)
        return q_star

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self.in_channels,
                                   self.out_channels)