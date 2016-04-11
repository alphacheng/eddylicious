import eddylicious
from eddylicious.readers.hdf5_readers import *
import numpy as np
from os import path


# Do not add zeros on top and bottom, take all points along y
def test_read_points_no_add_zeros_all_points():
    prefix = path.join(eddylicious.__path__[0], "..", "tests", "datasets",
                     "channel_flow_180")
    pointsY = np.load(path.join(prefix, "dsv_output", "pointsY.npy"))
    pointsZ = np.load(path.join(prefix, "dsv_output", "pointsZ.npy"))
    yInd = np.load(path.join(prefix, "dsv_output", "yInd.npy"))
    zInd = np.load(path.join(prefix, "dsv_output", "zInd.npy"))

    [pY, pZ, yI, zI] = read_points_from_foamfile(path.join(prefix,
                                                           "foam_file_output",
                                                           "1000.01",
                                                           "faceCentres"),
                                                 )

    assert np.all(pointsY == pY)
    assert np.all(pointsZ == pZ)
    assert np.all(yInd == yI)
    assert np.all(zInd == zI)


def test_read_points_no_add_zeros_exclude_top():
    n = 10
    prefix = path.join(eddylicious.__path__[0], "..", "tests", "datasets",
                       "channel_flow_180")
    pointsY = np.load(path.join(prefix, "dsv_output", "pointsY.npy"))[:n, :]
    pointsZ = np.load(path.join(prefix, "dsv_output", "pointsZ.npy"))[:n, :]
    yInd = np.load(path.join(prefix, "dsv_output", "yInd.npy"))
    zInd = np.load(path.join(prefix, "dsv_output", "zInd.npy"))

    [pY, pZ, yI, zI] = read_points_from_foamfile(path.join(prefix,
                                                           "foam_file_output",
                                                           "1000.01",
                                                           "faceCentres"),
                                                 nPointsY=n)

    assert np.all(pointsY == pY)
    assert np.all(pointsZ == pZ)
    assert np.all(yInd == yI)
    assert np.all(zInd == zI)


# Add zeros on top and bottom, take all points along y
def test_read_points_add_zeros_bot_all_points():
    prefix = path.join(eddylicious.__path__[0], "..", "tests", "datasets",
                       "channel_flow_180")
    pointsY = np.load(path.join(prefix, "dsv_output", "pointsY.npy"))
    pointsZ = np.load(path.join(prefix, "dsv_output", "pointsZ.npy"))
    yInd = np.load(path.join(prefix, "dsv_output", "yInd.npy"))
    zInd = np.load(path.join(prefix, "dsv_output", "zInd.npy"))

    pointsY = np.append(np.zeros((1, 72)), pointsY, axis=0)
    pointsZ = np.append(np.array([pointsZ[0, :]]), pointsZ, axis=0)
    pointsY = np.append(pointsY, np.zeros((1, 72)), axis=0)
    pointsZ = np.append(pointsZ, np.array([pointsZ[0, :]]),  axis=0)

    [pY, pZ, yI, zI] = read_points_from_foamfile(path.join(prefix,
                                                           "foam_file_output",
                                                           "1000.01",
                                                           "faceCentres"),
                                                 addValBot=0, addValTop=0)

    assert np.all(pointsY == pY)
    assert np.all(pointsZ == pZ)
    assert np.all(yInd == yI)
    assert np.all(zInd == zI)


# Add zeros at the bottom, take part of the along y
def test_read_points_add_zeros_bot_some_points_midalue():
    n = 10
    prefix = path.join(eddylicious.__path__[0], "..", "tests", "datasets",
                       "channel_flow_180")
    pointsY = np.load(path.join(prefix, "dsv_output", "pointsY.npy"))
    pointsZ = np.load(path.join(prefix, "dsv_output", "pointsZ.npy"))
    yInd = np.load(path.join(prefix, "dsv_output", "yInd.npy"))
    zInd = np.load(path.join(prefix, "dsv_output", "zInd.npy"))

    pointsY = np.append(np.zeros((1, 72)), pointsY, axis=0)[:n, :]
    pointsZ = np.append(np.array([pointsZ[0, :]]), pointsZ, axis=0)[:n, :]
    pointsY[-1, :] = 1.0


    [pY, pZ, yI, zI] = read_points_from_foamfile(path.join(prefix,
                                                           "foam_file_output",
                                                           "1000.01",
                                                           "faceCentres"),
                                                 addValBot=0, nPointsY=n,
                                                 midValue=1)

    assert np.all(pointsY == pY)
    assert np.all(pointsZ == pZ)
    assert np.all(yInd == yI)
    assert np.all(zInd == zI)


def test_read_velocity_add_zeros_bot_some_points_interpolate():
    prefix = path.join(eddylicious.__path__[0], "..", "tests", "datasets",
                       "channel_flow_180")
    uX = np.load(path.join(prefix, "dsv_output", "1000.01", "uX.npy"))
    uY = np.load(path.join(prefix, "dsv_output", "1000.01", "uY.npy"))
    uZ = np.load(path.join(prefix, "dsv_output", "1000.01", "uZ.npy"))
    yInd = np.load(path.join(prefix, "dsv_output", "yInd.npy"))
    zInd = np.load(path.join(prefix, "dsv_output", "zInd.npy"))

    nPointsY = 15

    uX = np.append(np.zeros((1, 72)), uX, axis=0)
    uY = np.append(np.zeros((1, 72)), uY, axis=0)
    uZ = np.append(np.zeros((1, 72)), uZ, axis=0)

    uX[nPointsY-1, :] = 0.5*(uX[nPointsY-2, :] + uX[nPointsY, :])
    uY[nPointsY-1, :] = 0.5*(uY[nPointsY-2, :] + uY[nPointsY, :])
    uZ[nPointsY-1, :] = 0.5*(uZ[nPointsY-2, :] + uZ[nPointsY, :])

    [uXR, uYR, uZR] = read_u_from_foamfile(path.join(prefix,
                                                     "foam_file_output",
                                                     "1000.01", "U"), nPointsY,
                                           72, yInd, zInd, addValBot=0,
                                           interpolate=1)

    assert np.all(uX[:nPointsY, :] == uXR[:nPointsY, :])
    assert np.all(uY[:nPointsY, :] == uYR[:nPointsY, :])
    assert np.all(uZ[:nPointsY, :] == uZR[:nPointsY, :])


def test_read_velocity_add_zeros_bot_some_points_no_interpolate():
    prefix = path.join(eddylicious.__path__[0], "..", "tests", "datasets",
                       "channel_flow_180")
    uX = np.load(path.join(prefix, "dsv_output", "1000.01", "uX.npy"))
    uY = np.load(path.join(prefix, "dsv_output", "1000.01", "uY.npy"))
    uZ = np.load(path.join(prefix, "dsv_output", "1000.01", "uZ.npy"))
    yInd = np.load(path.join(prefix, "dsv_output", "yInd.npy"))
    zInd = np.load(path.join(prefix, "dsv_output", "zInd.npy"))

    nPointsY = 15

    uX = np.append(np.zeros((1, 72)), uX, axis=0)
    uY = np.append(np.zeros((1, 72)), uY, axis=0)
    uZ = np.append(np.zeros((1, 72)), uZ, axis=0)

    [uXR, uYR, uZR] = read_u_from_foamfile(path.join(prefix,
                                                     "foam_file_output",
                                                     "1000.01", "U"), nPointsY,
                                           72, yInd, zInd, addValBot=0,
                                           interpolate=0)

    assert np.all(uX[:nPointsY, :] == uXR[:nPointsY, :])
    assert np.all(uY[:nPointsY, :] == uYR[:nPointsY, :])
    assert np.all(uZ[:nPointsY, :] == uZR[:nPointsY, :])

def test_read_velocity_add_zeros_bot_top_all_points_no_interpolate():
    prefix = path.join(eddylicious.__path__[0], "..", "tests", "datasets",
                       "channel_flow_180")
    uX = np.load(path.join(prefix, "dsv_output", "1000.01", "uX.npy"))
    uY = np.load(path.join(prefix, "dsv_output", "1000.01", "uY.npy"))
    uZ = np.load(path.join(prefix, "dsv_output", "1000.01", "uZ.npy"))
    yInd = np.load(path.join(prefix, "dsv_output", "yInd.npy"))
    zInd = np.load(path.join(prefix, "dsv_output", "zInd.npy"))


    uX = np.append(np.zeros((1, 72)), uX, axis=0)
    uY = np.append(np.zeros((1, 72)), uY, axis=0)
    uZ = np.append(np.zeros((1, 72)), uZ, axis=0)

    uX = np.append(uX, np.zeros((1, 72)), axis=0)
    uY = np.append(uY, np.zeros((1, 72)), axis=0)
    uZ = np.append(uZ, np.zeros((1, 72)), axis=0)

    nPointsY = uX.shape[0]

    [uXR, uYR, uZR] = read_u_from_foamfile(path.join(prefix,
                                                     "foam_file_output",
                                                     "1000.01", "U"), nPointsY,
                                           72, yInd, zInd, addValBot=0,
                                           addValTop=0, interpolate=0)
    assert np.all(uX[:, :] == uXR[:, :])
    assert np.all(uY[:, :] == uYR[:, :])
    assert np.all(uZ[:, :] == uZR[:, :])


