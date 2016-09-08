#
# Copyright (c) 2016 KAMADA Ken'ichi.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.
#

"""FIML estimation of the mean/covariance of data with missing values.

This is an implementation of full information maximum likelihood (FIML)
method to estimate the mean and the covariance of data with missing
values.
"""

import numpy as np
import scipy as sp
import scipy.optimize

def fiml(data, bias=False):
    """FIML estimation of the mean/covariance of data with missing values.

    Estimate the mean and the covariance of data with missing values by
    full information maximum likelihood (FIML) method.

    Parameters
    ----------
    data : ndarray
        A 2-D array containing variables and observations.
        Each row is an observation and each column is a variable.
        A missing value is represented by `np.nan`.

    Returns
    -------
    mean : ndarray
        Estimated means of the variables.
    cov : ndarray
        Estimated covariance of the variables.
    """

    size, dim = data.shape
    mean0 = np.zeros(dim)
    cov0 = np.eye(dim)
    params0 = _pack_params(dim, mean0, cov0)
    # XXX The covariance matrix is guaranteed to be symmetric (see
    # the _pack_params function) but may be still invalid (i.e.
    # non-positive-semidefinite) because no constraint is imposed in
    # the optimization.
    result = sp.optimize.fmin(_obj_func, params0, args=(dim, data))
    mean, cov = _unpack_params(dim, result)
    if not bias:
        cov = cov * (size / (size - 1.0))
    return mean, cov

def _obj_func(params, dim, data):
    mean, cov = _unpack_params(dim, params)
    objval = 0.0
    for x in data:
        obs = ~np.isnan(x)
        objval += _log_likelihood(x[obs], mean[obs], cov[obs][:, obs])
    return -objval

# Pack the mean and the covariance into a 1-dimensional array.
def _pack_params(dim, mean, cov):
    params = np.zeros(dim + dim * (dim + 1) / 2)
    params[:dim] = mean
    for p, i, j in zip(range(dim * (dim + 1) / 2), *np.tril_indices(dim)):
        params[dim + p] = cov[i, j]
    return params

# Unpack the mean and the covariance from a 1-dimensional array.
def _unpack_params(dim, params):
    mean = params[0:dim]
    cov = np.zeros((dim, dim))
    for v, i, j in zip(params[dim:], *np.tril_indices(dim)):
        cov[i, j] = v
        cov[j, i] = v
    return mean, cov

# Log likelihood function.
def _log_likelihood(x, mean, cov):
    return np.log(_pdf_normal(x, mean, cov))

# Probability density function of multivariate normal distribution.
def _pdf_normal(x, mean, cov):
    xshift = x - mean
    t1 = (2 * np.pi) ** (-0.5 * len(x))
    t2 = np.linalg.det(cov) ** (-0.5)
    t3 = -0.5 * xshift.dot(np.linalg.inv(cov)).dot(xshift)
    return t1 * t2 * np.exp(t3)
