# This file is part of eddylicious
# (c) Timofey Mukha
# The code is released under the GNU GPL Version 3 licence.
# See LICENCE.txt and the Legal section in the User Guide for more information

"""Functions for generating inflow velocity fields using
Lund et al's rescaling, see

Lund T.S., Wu X., Squires K.D. Generation of turbulent inflow
data for spatially-developing boundary layer simulations.
J. Comp. Phys. 1998; 140:233-58.

"""
from __future__ import print_function
from __future__ import division
import numpy as np
from mpi4py import MPI
from scipy.interpolate import interp1d
from scipy.interpolate import interp2d
from ..helper_functions import chunks_and_offsets
from ..writers.ofnative_writers import write_velocity_to_ofnative
from ..writers.hdf5_writers import write_velocity_to_hdf5

__all__ = ["lund_rescale_mean_velocity", "lund_rescale_fluctuations",
           "lund_generate"]


def lund_rescale_mean_velocity(etaPrec, yPlusPrec,
                               uMeanXPrec, uMeanYPrec,
                               nInfl, etaInfl, yPlusInfl, nPointsZInfl,
                               u0Infl, u0Prec,
                               gamma, blending):
    """Rescale the mean velocity profile using Lunds rescaling.

    This function rescales the mean velocity profile taken from the
    precursor simulation using Lund et al's rescaling.

    Parameters
    ----------
    etaPrec : ndarray
        The values of eta for the corresponding values of the mean
        velocity from the precursor.
    yPlusPrec : ndarray
        The values of y+ for the corresponding values of the mean
        velocity from the precursor.
    uMeanXPrec : ndarray
        The values of the mean streamwise velocity from the precursor.
    uMeanYPrec : ndarray
        The values of the mean wall-normal velocity from the precursor.
    nInfl : int
        The amount of points in the wall-normal direction that contain
        the boundary layer at the inflow boundary.
    etaInfl : ndarray
        The values of eta for the mesh points at the inflow boundary.
    yPlusInfl : ndarray
        The values of y+ for the mesh points at the inflow boundary.
    nPointsZInfl : int
        The amount of points in the spanwise direction for the inflow
        boundary.
    u0Infl : float
        The freestream velocity at the inflow.
    u0Prec : float
        The freestream velocity for the precursor.
    gamma : float
        The ratio of the friction velocities in the inflow boundary
        layer and the precursor.
    blending : ndarray
        The weights for blending the inner and outer profiles.

    Returns
    -------
    uX, ndarray
        The values of the mean streamwise velocity.
    uY, ndarray
        The values of the mean wall-normal velocity.

    """
    assert nInfl > 0
    assert nPointsZInfl > 0
    assert u0Infl > 0
    assert u0Prec > 0
    assert gamma > 0
    assert np.all(etaInfl >= 0)
    assert np.all(etaPrec >= 0)
    assert np.all(yPlusInfl >= 0)
    assert np.all(yPlusPrec >= 0)

    # Check if the wall is at the top, if so flip
    flip = False
    if etaInfl[0] > etaInfl[1]:
        etaInfl = np.flipud(etaInfl)
        yPlusInfl = np.flipud(yPlusInfl)
        flip = True

    # The streamwise component
    uMeanXInterp = interp1d(etaPrec, uMeanXPrec)
    uMeanXInterpPlus = interp1d(yPlusPrec, uMeanXPrec)

    uMeanXInner = gamma*uMeanXInterpPlus(yPlusInfl[:nInfl])
    uMeanXOuter = gamma*uMeanXInterp(etaInfl[:nInfl]) + u0Infl - gamma*u0Prec
 
    uMeanXInfl = np.zeros(etaInfl.shape)
    uMeanXInfl[:nInfl] = uMeanXInner*(1 - blending[:nInfl]) + \
        uMeanXOuter*blending[:nInfl]
    uMeanXInfl[nInfl:] = uMeanXInfl[nInfl-1]
    uMeanXInfl = np.ones((etaInfl.size, nPointsZInfl))*uMeanXInfl[:,
                                                                  np.newaxis]

    # The wall-normal component
    uMeanYInterp = interp1d(etaPrec, uMeanYPrec)
    uMeanYInterpPlus = interp1d(yPlusPrec, uMeanYPrec)
    uMeanYInner = uMeanYInterpPlus(yPlusInfl[:nInfl])
    uMeanYOuter = uMeanYInterp(etaInfl[:nInfl])

    uMeanYInfl = np.zeros(etaInfl.shape)
    uMeanYInfl[:nInfl] = uMeanYInner*(1 - blending[:nInfl]) + \
                         uMeanYOuter*blending[:nInfl]
    uMeanYInfl[nInfl:] = uMeanYInfl[nInfl-1]

    uMeanYInfl = np.ones((etaInfl.size, nPointsZInfl))*uMeanYInfl[:,
                                                                  np.newaxis]

    assert np.all(uMeanXInfl >= 0)

    if flip: 
        return np.flipud(uMeanXInfl), np.flipud(uMeanYInfl)
    else:
        return uMeanXInfl, uMeanYInfl


def lund_rescale_fluctuations(etaPrec, yPlusPrec, pointsZ,
                              uPrimeX, uPrimeY, uPrimeZ, gamma,
                              etaInfl, yPlusInfl, pointsZInfl,
                              nInfl, blending):
    """Rescale the fluctuations of velocity using Lund et al's
    rescaling.

    This function rescales the fluctuations of the three components of
    the velocity field taken from the precursor simulation using Lund et
    al's rescaling.

    Parameters
    ----------
    etaPrec : ndarray
        The values of eta for the corresponding values of the mean
        velocity from the precursor.
    yPlusPrec : ndarray
        The values of y+ for the corresponding values of the mean
        velocity from the precursor.
    pointsZ : ndarray
        A 2d array containing the values of z for the points of the
        precursor mesh.
    uPrimeX : ndarray
        A 2d array containing the values of the fluctuations of the x
        component of velocity.
    uPrimeY : ndarray
        A 2d array containing the values of the fluctuations of the y
        component of velocity.
    uPrimeZ : ndarray
        A 2d array containing the values of the fluctuations of the z
        component of velocity.
    gamma : float
        The ratio of the friction velocities in the inflow boundary
        layer and the precursor.
    etaInfl : ndarray
        The values of eta for the mesh points at the inflow boundary.
    yPlusInfl : ndarray
        The values of y+ for the mesh points at the inflow boundary.
    pointsZInfl : ndarray
        A 2d array containing the values of z for the points of the
        inflow boundary.
    nInfl : int
        The amount of points in the wall-normal direction that contain
        the boundary layer at the inflow boundary.
    blending : ndarray
        The weights for blending the inner and outer profiles.

    Returns
    -------
    List of ndarrays
        The list contains three items, each a 2d ndarray. The first
        array contains the rescaled fluctuations of the x component of
        velocity. The second -- of the y component of velocity. The
        third -- of the z component of velocity.

    """
    assert np.all(etaPrec >= 0)
    assert np.all(yPlusPrec >= 0)
    assert np.all(etaInfl >= 0)
    assert np.all(yPlusInfl >= 0)
    assert nInfl > 0
    assert gamma > 0

    # Check if the wall is at the top, if so flip
    flip = False
    if etaInfl[0] > etaInfl[1]:
        etaInfl = np.flipud(etaInfl)
        yPlusInfl = np.flipud(yPlusInfl)
        flip = True

    uPrimeXInfl = np.zeros(pointsZInfl.shape)
    uPrimeYInfl = np.zeros(pointsZInfl.shape)
    uPrimeZInfl = np.zeros(pointsZInfl.shape)

    uPrimeXInterp = interp2d(pointsZ[0, :]/pointsZ[0, -1], etaPrec, uPrimeX)
    uPrimeYInterp = interp2d(pointsZ[0, :]/pointsZ[0, -1], etaPrec, uPrimeY)
    uPrimeZInterp = interp2d(pointsZ[0, :]/pointsZ[0, -1], etaPrec, uPrimeZ)

    uPrimeXPlusInterp = interp2d(pointsZ[0, :]/pointsZ[0, -1], yPlusPrec,
                                 uPrimeX)
    uPrimeYPlusInterp = interp2d(pointsZ[0, :]/pointsZ[0, -1], yPlusPrec,
                                 uPrimeY)
    uPrimeZPlusInterp = interp2d(pointsZ[0, :]/pointsZ[0, -1], yPlusPrec,
                                 uPrimeZ)

    uPrimeXInner = \
        gamma*uPrimeXPlusInterp(pointsZInfl[0, :]/pointsZInfl[0, -1],
                                yPlusInfl[:nInfl])
    uPrimeYInner = \
        gamma*uPrimeYPlusInterp(pointsZInfl[0, :]/pointsZInfl[0, -1],
                                yPlusInfl[:nInfl])
    uPrimeZInner = \
        gamma*uPrimeZPlusInterp(pointsZInfl[0, :]/pointsZInfl[0, -1],
                                yPlusInfl[:nInfl])

    uPrimeXOuter = gamma*uPrimeXInterp(pointsZInfl[0, :]/pointsZInfl[0, -1],
                                       etaInfl[:nInfl])
    uPrimeYOuter = gamma*uPrimeYInterp(pointsZInfl[0, :]/pointsZInfl[0, -1],
                                       etaInfl[:nInfl])
    uPrimeZOuter = gamma*uPrimeZInterp(pointsZInfl[0, :]/pointsZInfl[0, -1],
                                       etaInfl[:nInfl])

    uPrimeXInfl[:nInfl] = \
        uPrimeXInner*(1 - blending[0:nInfl])[:, np.newaxis] + \
        uPrimeXOuter*blending[0:nInfl][:, np.newaxis]
    uPrimeYInfl[:nInfl] = \
        uPrimeYInner*(1 - blending[0:nInfl])[:, np.newaxis] + \
        uPrimeYOuter*blending[0:nInfl][:, np.newaxis]
    uPrimeZInfl[:nInfl] = \
        uPrimeZInner*(1 - blending[0:nInfl])[:, np.newaxis] + \
        uPrimeZOuter*blending[0:nInfl][:, np.newaxis]
    if flip:
        return map(np.flipud, [uPrimeXInfl, uPrimeYInfl, uPrimeZInfl])
    else:
        return [uPrimeXInfl, uPrimeYInfl, uPrimeZInfl]


def lund_generate(readerFunction, writerFunction,
                  dt, t0, tEnd, timePrecision,
                  uMeanXPrec, uMeanXInfl,
                  uMeanYPrec, uMeanYInfl,
                  etaPrec, yPlusPrec, pointsZ,
                  etaInfl, yPlusInfl, pointsZInfl,
                  nInfl, gamma,
                  times, blending):
    """Generate the the inflow velocity using Lund's
    rescaling.

    This function will use Lund et al's rescaling in order to generate
    velocity fields for the inflow boundary. The rescaling for the mean
    profile should be done beforehand and is one of the input parameters
    for this function.

    Parameters
    ----------
    readerFunction : function
        The function to use for reading in data, generated by the
        reader. Should contain the reader's name in the attribute
        "reader".
    writerFunction: function
        The function to use for writing data.
    dt : float
        The time-step to be used in the simulation. This will be used to
        associate a time-value with the produced velocity fields.
    t0 : float
        The starting time to be used in the simulation. This will be
        used to associate a time-value with the produced velocity.
    timePrecision : int
        Number of points after the decimal to keep for the time value.
    tEnd : float
        The ending time for the simulation.
    uMeanXPrec : ndarray
        The values of the mean streamwise velocity from the precursor.
    uMeanXInfl : ndarray
        The values of the mean streamwise velocity for the inflow
        boundary layer.
    uMeanYPrec : ndarray
        The values of the mean wall-normal velocity from the precursor.
    uMeanYInfl : ndarray
        The values of the mean wall-normal velocity for the inflow
        boundary layer.
    etaPrec : ndarray
        The values of eta for the corresponding values of the mean
        velocity from the precursor.
    yPlusPrec : ndarray
        The values of y+ for the corresponding values of the mean
        velocity from the precursor.
    pointsZ : ndarray
        A 2d array containing the values of z for the points of the
        precursor mesh.
    etaInfl : ndarray
        The values of eta for the mesh points at the inflow boundary.
    yPlusInfl : ndarray
        The values of y+ for the mesh points at the inflow boundary.
    pointsZInfl : int
        A 2d array containing the values of z for the points of the
        inflow boundary.
    nInfl : int
        The amount of points in the wall-normal direction that contain
        the boundary layer at the inflow boundary.
    gamma : float
        The ration of the friction velocities in the inflow boundary
        layer and the precursor.
    times : list of floats or strings
        The times for which the velocity field was sampled in the
        precursor simulation.
    blending : ndarray
        The weights for blending the inner and outer profiles.

    """
    # Grab info regarding parallelization
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    nProcs = comm.Get_size()

    # Get the total amount of rescalings to be done
    size = int((tEnd-t0)/dt+1)
    
    # Calculate the amount of rescalings each processor is responsible for
    [chunks, offsets] = chunks_and_offsets(nProcs, size)

    # Perform the rescaling
    for i in range(chunks[rank]):
        t = t0 + dt*i + dt*int(offsets[rank])
        t = float(("{0:."+str(timePrecision)+"f}").format(t))
        position = int(offsets[rank]) + i

        if (rank == 0) and (np.mod(i, int(chunks[rank]/10)) == 0):
            print("     Rescaled about "+str(int(i/chunks[rank]*100))+"%")

        # Read U data
        if readerFunction.reader == "foamFile":
            assert position < len(times)
            [uPrimeX, uPrimeY, uPrimeZ] = readerFunction(times[position])
        elif readerFunction.reader == "hdf5":
            assert position < len(times)
            [uPrimeX, uPrimeY, uPrimeZ] = readerFunction(position)
        else:
            raise ValueError("Unknown reader")

        # Subtract mean
        uPrimeX -= uMeanXPrec[:, np.newaxis]
        uPrimeY -= uMeanYPrec[:, np.newaxis]

        [uXInfl, uYInfl, uZInfl] = lund_rescale_fluctuations(etaPrec,
                                                             yPlusPrec,
                                                             pointsZ,
                                                             uPrimeX,
                                                             uPrimeY,
                                                             uPrimeZ,
                                                             gamma,
                                                             etaInfl,
                                                             yPlusInfl,
                                                             pointsZInfl,
                                                             nInfl,
                                                             blending)

        # Add mean
        uXInfl += uMeanXInfl
        uYInfl += uMeanYInfl

        # Write
        writerFunction(t, position, uXInfl, uYInfl, uZInfl)
