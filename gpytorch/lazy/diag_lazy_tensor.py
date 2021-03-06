from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import torch
from .lazy_tensor import LazyTensor


class DiagLazyTensor(LazyTensor):
    def __init__(self, diag):
        """
        Diagonal lazy tensor

        Args:
        - diag (Variable: n) diagonal of matrix
        """
        super(DiagLazyTensor, self).__init__(diag)
        self._diag = diag

    def _matmul(self, rhs):
        if rhs.ndimension() == 1 and self.ndimension() == 2:
            return self._diag * rhs
        else:
            res = self._diag.unsqueeze(-1).expand_as(rhs) * rhs
            return res

    def _t_matmul(self, rhs):
        # Matrix is symmetric
        return self._matmul(rhs)

    def _quad_form_derivative(self, left_vecs, right_vecs):
        res = left_vecs * right_vecs
        if res.ndimension() > self._diag.ndimension():
            res = res.sum(-1)
        return (res,)

    def _size(self):
        if self._diag.ndimension() == 2:
            return self._diag.size(0), self._diag.size(-1), self._diag.size(-1)
        else:
            return self._diag.size(-1), self._diag.size(-1)

    def _transpose_nonbatch(self):
        return self

    def _batch_get_indices(self, batch_indices, left_indices, right_indices):
        equal_indices = left_indices.eq(right_indices).type_as(self._diag)
        return self._diag[batch_indices, left_indices] * equal_indices

    def _get_indices(self, left_indices, right_indices):
        equal_indices = left_indices.eq(right_indices).type_as(self._diag)
        return self._diag[left_indices] * equal_indices

    def add_diag(self, added_diag):
        return DiagLazyTensor(self._diag + added_diag.expand_as(self._diag))

    def __add__(self, other):
        from .added_diag_lazy_tensor import AddedDiagLazyTensor
        if isinstance(other, DiagLazyTensor):
            return DiagLazyTensor(self._diag + other._diag)
        else:
            return AddedDiagLazyTensor(other, self)

    def diag(self):
        return self._diag

    def evaluate(self):
        if self.ndimension() == 2:
            return self._diag.diag()
        else:
            return super(DiagLazyTensor, self).evaluate()

    def sum_batch(self, sum_batch_size=None):
        if sum_batch_size is None:
            diag = self._diag.view(-1, self._diag.size(-1))
        else:
            diag = self._diag.view(-1, sum_batch_size, self._diag.size(-1))

        return self.__class__(diag.sum(-2))

    def zero_mean_mvn_samples(self, num_samples):
        if self.ndimension() == 3:
            base_samples = torch.randn(
                num_samples, self._diag.size(0), self._diag.size(1), dtype=self.dtype, device=self.device
            )
        else:
            base_samples = torch.randn(num_samples, self._diag.size(0), dtype=self.dtype, device=self.device)
        samples = self._diag.unsqueeze(0).sqrt() * base_samples
        return samples
