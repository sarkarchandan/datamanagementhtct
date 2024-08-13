from pathlib import Path
import shutil
import imageio.v3 as iio
import numpy as np
from numpy.typing import ArrayLike
import tiledb


src_path = Path().absolute().joinpath("data/reco100.tiff").__str__()
volume: ArrayLike = iio.imread(src_path)

# Use a compressor
gzip_filter = tiledb.GzipFilter()

# Create domain specifying dimensions
domain = tiledb.Domain([
    tiledb.Dim(name="x", domain=(0, volume.shape[0] - 1), tile=1, dtype=np.uint16, filters=[gzip_filter]),
    tiledb.Dim(name="y", domain=(0, volume.shape[1] - 1), tile=1, dtype=np.uint16, filters=[gzip_filter]),
    tiledb.Dim(name="z", domain=(0, volume.shape[2] - 1), tile=1, dtype=np.uint16, filters=[gzip_filter])
])

attr = tiledb.Attr(name="volume", dtype=np.uint16)

# Create dense array schema
schema = tiledb.ArraySchema(
    domain=domain,
    attrs=[attr],
    cell_order="row-major",
    tile_order="row-major",
    sparse=False
)

# # Array location on disk
data_path = Path().absolute().joinpath("data/arr").__str__()
if tiledb.array_exists(uri=data_path, isdense=True):
    shutil.rmtree(data_path)
tiledb.DenseArray.create(data_path, schema=schema)

try:
    with tiledb.open(data_path, mode='w') as arr:
        arr[:arr.shape[0], :arr.shape[1], :arr.shape[2]] = volume

except Exception as e:
    print(e.__str__())

