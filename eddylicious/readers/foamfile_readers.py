# This file is part of eddylicious
# (c) Timofey Mukha
# The code is released under the GNU GPL Version 3 licence.
# See LICENCE.txt and the Legal section in the User Guide for more information

"""Functions for reading fields stored in the foamFile format

"""
import numpy as np
import os

__all__ = ["read_foamfile",
           "read_structured_points_foamfile",
           "read_structured_velocity_foamfile",
           "read_points_foamfile", "read_velocity_foamfile"]


def read_foamfile(readPath):
    """Read data stored in foamFile format.

    Parameters
    ----------
    readPath : str
        The path to the file.

    Returns
    -------
    ndarray
        Contains the read data

    """
    with open(readPath) as dataFile:
        data = [line.rstrip(')\n') for line in dataFile]

    data = [line.lstrip('(') for line in data]
    data = data[3:-1]
    return np.genfromtxt(data)


def read_structured_points_foamfile(readPath, addValBot=float('nan'),
                                    addValTop=float('nan'), excludeBot=0,
                                    excludeTop=0, exchangeValBot=float('nan'),
                                    exchangeValTop=float('nan')):
    """Read the coordinates of the points from a foamFile-format file.


    Reads in the locations of the face centers, stored in foamFile
    format by OpenFOAM, and transforms them into 2d numpy arrays.

    The points are sorted so that the axes of the arrays correspond to
    the wall-normal and spanwise directions. The points are first sorted
    along y, then reshaped into a 2d array and then sorted along z for
    each value of z.

    The function supports manipulating the points in certain ways, see
    the parameter list below.

    Parameters
    ----------
    readPath : str
        The path to the file containing the points.
    addValBot : float, optional
        Append a row of values from below, nothing added by default.
    addValTop : float, optional
        Append a row of values from above, nothing added by default.
    excludeBot : int, optional
        How many points to remove from the bottom in the y direction.
        (default 0).
    excludeTop: int, optional
        How many points to remove from the top in the y direction.
        (default 0).
    exchangeValBot : float, optional
        Exchange the value of y at the bottom.
    exchangeValTop : float, optional
        Exchange the value of y at the top.

    Returns
    -------
    List of ndarrays
        The list contains 4 items

        pointsY :
        A 2d ndarray containing the y coordinates of the points.

        pointsZ :
        A 2d ndarray containing the z coordinates of the points.

        indY :
        The sorting indices from the sorting performed.

        indZ :
        The sorting indices from the sorting performed.

    """
    points = read_foamfile(readPath)
    points = points[:, 1:]

# Sort the points
# Sort along y first
    yInd = np.argsort(points[:, 0])
    points[:, 0] = points[yInd, 0]
    points[:, 1] = points[yInd, 1]

# Find the number of points along z
    nPointsZ = 0
    for i in range(points[:, 0].size):
        if points[i, 0] == points[0, 0]:
            nPointsZ += 1
        else:
            break

# Reshape into a 2d array
    pointsY = np.copy(np.reshape(points[:, 0], (-1, nPointsZ)))
    pointsZ = np.copy(np.reshape(points[:, 1], (-1, nPointsZ)))

# For each y order the points in z
    zInd = np.zeros(pointsZ.shape, dtype=np.int)

    for i in range(pointsZ.shape[0]):
        zInd[i, :] = np.argsort(pointsZ[i, :])
        pointsZ[i, :] = pointsZ[i, zInd[i, :]]


# Add points at y = 0 and y = max(y)
    if not np.isnan(addValBot):
        pointsY = np.append(addValBot*np.ones((1, nPointsZ)), pointsY, axis=0)
        pointsZ = np.append(np.array([pointsZ[0, :]]), pointsZ, axis=0)
    if not np.isnan(addValTop):
        pointsY = np.append(pointsY, addValTop*np.ones((1, nPointsZ)), axis=0)
        pointsZ = np.append(pointsZ, np.array([pointsZ[-1, :]]),  axis=0)

    nPointsY = pointsY.shape[0]

# Cap the points
    if excludeTop:
        pointsY = pointsY[:(nPointsY-excludeTop), :]
        pointsZ = pointsZ[:(nPointsY-excludeTop), :]

    if excludeBot:
        pointsY = pointsY[excludeBot:, :]
        pointsZ = pointsZ[excludeBot:, :]

    if not np.isnan(exchangeValBot):
        pointsY[0, :] = exchangeValBot

    if not np.isnan(exchangeValTop):
        pointsY[-1, :] = exchangeValTop

    return [pointsY, pointsZ, yInd, zInd]


def read_structured_velocity_foamfile(baseReadPath, surfaceName, nPointsZ,
                                      yInd, zInd,
                                      addValBot=(float('nan'), float('nan'),
                                                 float('nan')),
                                      addValTop=(float('nan'), float('nan'),
                                                 float('nan')),
                                      excludeBot=0, excludeTop=0,
                                      interpValBot=False, interpValTop=False):
    """Read the values of the velocity field from a foamFile-format file.

    Reads in the values of the velocity components stored in the
    foamFile file-format. The velocity field is read and the transformed
    into a 2d ndarray, where the array's axes correspond to wall-normal
    and spanwise directions. To achieve this, the sorting indices
    obtained when reordering the mesh points are used.

    Some manipulation with the read-in data is also available via the
    optional parameters.

    Parameters
    ----------
    baseReadPath : str
        The path where the time-directories with the velocity values are
        located.
    surfaceName: str
        The name of the surface that was used for sampling.
    nPointsZ : int
        The amount of points in the mesh in the spanwise direction.
    yInd : ndarray
        The sorting indices for sorting in the wall-normal direction.
    zInd : ndarray
        The sorting indices for sorting in the spanwise direction.
    addValBot : tuple of three floats, optional
        Append a row of values from below.
    addValTop : tuple of three floats, optional
        Append a row of values from above.
    excludeBot : int, optional
        How many points to remove from the bottom in the y direction.
        (default 0).
    excludeTop: int, optional
        How many points to remove from the top in the y direction.
        (default 0).
    interpValBot : bool, optional
        Whether to interpolate the first value in the wall-normal
        direction using two points. (default False)
    interpValTop : bool, optional
        Whether to interpolate the last value in the wall-normal
        direction using two points. (default False)

    Returns
    -------
    function
        A function of one variable (the time-value) that will actually
        perform the reading.

    """
    def read(time):
        """
        A function that will actually perform the reading.

        Parameters
        ----------
        time, float or string
            The value of the time, will be converted to a string.

        Returns
        -------
        List of 2d arrays.
        The list contains three items, corresponding
        to the three components of the velocity field, the order of the
        components in the list is x, y and the z.

        """
        readUPath = os.path.join(baseReadPath, str(time), surfaceName,
                                 "vectorField", "U")
        with open(readUPath) as UFile:
            u = [line.rstrip(')\n') for line in UFile]

        u = [line.lstrip('(') for line in u]
        u = u[3:-1]
        u = np.genfromtxt(u)

        # Sort along y
        u[:, 0] = u[yInd, 0]
        u[:, 1] = u[yInd, 1]
        u[:, 2] = u[yInd, 2]

        # Reshape to 2d
        uX = np.copy(np.reshape(u[:, 0], (-1, nPointsZ)))
        uY = np.copy(np.reshape(u[:, 1], (-1, nPointsZ)))
        uZ = np.copy(np.reshape(u[:, 2], (-1, nPointsZ)))

        # Sort along z
        for i in range(uX.shape[0]):
            uX[i, :] = uX[i, zInd[i, :]]
            uY[i, :] = uY[i, zInd[i, :]]
            uZ[i, :] = uZ[i, zInd[i, :]]

        if not np.isnan(addValBot[0]):
            uX = np.append(addValBot[0]*np.ones((1, nPointsZ)), uX, axis=0)
            uY = np.append(addValBot[1]*np.ones((1, nPointsZ)), uY, axis=0)
            uZ = np.append(addValBot[2]*np.ones((1, nPointsZ)), uZ, axis=0)

        if not np.isnan(addValTop[0]):
            uX = np.append(uX, addValTop[0]*np.ones((1, nPointsZ)), axis=0)
            uY = np.append(uY, addValTop[1]*np.ones((1, nPointsZ)), axis=0)
            uZ = np.append(uZ, addValTop[2]*np.ones((1, nPointsZ)), axis=0)

        nPointsY = uX.shape[0]
        topmostPoint = nPointsY-excludeTop

        # Interpolate for the last point in the wall-normal direction
        if interpValTop and excludeTop:
            uX[topmostPoint-1, :] = 0.5*(uX[topmostPoint-1, :] +
                                         uX[topmostPoint, :])
            uY[topmostPoint-1, :] = 0.5*(uY[topmostPoint-1, :] +
                                         uY[topmostPoint, :])
            uZ[topmostPoint-1, :] = 0.5*(uZ[topmostPoint-1, :] +
                                         uZ[topmostPoint, :])

        # Interpolate for the first point in the wall-normal direction
        if interpValBot and excludeBot:
            uX[excludeBot, :] = 0.5*(uX[excludeBot-1, :] + uX[excludeBot, :])
            uY[excludeBot, :] = 0.5*(uY[excludeBot-1, :] + uY[excludeBot, :])
            uZ[excludeBot, :] = 0.5*(uZ[excludeBot-1, :] + uZ[excludeBot, :])

        # Cap the points
        if excludeTop:
            uX = uX[:topmostPoint, :]
            uY = uY[:topmostPoint, :]
            uZ = uZ[:topmostPoint, :]

        if excludeBot:
            uX = uX[excludeBot:, :]
            uY = uY[excludeBot:, :]
            uZ = uZ[excludeBot:, :]

        return [uX, uY, uZ]

    read.reader = "foamFile"
    return read


def read_points_foamfile(readPath):
    """Read the coordinates of the points from a foamFile-format file.


    Reads in the locations of the face centers, stored in foamFile
    format by OpenFOAM.

    Parameters
    ----------
    readPath : str
        The path to the file containing the points.

    Returns
    -------
    List of ndarrays
        Two arrays corresponding to y and z components of the points.

    """
    points = read_foamfile(readPath)
    points = points[:, 1:]

    return [points[:, 0], points[:, 1]]


def read_velocity_foamfile(baseReadPath, surfaceName):
    """Read the values of the velocity field from a foamFile-format file.

    Reads in the values of the velocity components stored in the
    foamFile file-format.

    Parameters
    ----------
    baseReadPath : str
        The path where the time-directories with the velocity values are
        located.
    surfaceName: str
        The name of the surface that was used for sampling.

    Returns
    -------
    function
        A function of one variable (the time-value) that will actually
        perform the reading.

    """
    def read(time):
        """
        A function that will actually perform the reading.

        Parameters
        ----------
        time, float or string
            The value of the time, will be converted to a string.

        Returns
        -------
        List of ndarrays
            Three arrays corresponding to the three components of
            velocity

        """
        readUPath = os.path.join(baseReadPath, str(time), surfaceName,
                                 "vectorField", "U")
        u = read_foamfile(readUPath)

        return [u[:, 0], u[:, 1], u[:, 2]]

    read.reader = "foamFile"
    return read
